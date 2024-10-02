import json
import os
from operator import itemgetter
from config import EMBEDDING_MODEL, TOP_K, MAX_DOCS_FOR_CONTEXT
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnableLambda
from langchain_openai import OpenAIEmbeddings
from langchain_core.retrievers import BaseRetriever
from langchain.load import dumps, loads
from utils.document_processing import LLM_MODEL_OPENAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

def create_retriever(documents: list) -> BaseRetriever:
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    vectordb = Chroma.from_documents(documents, embeddings)
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K},
    )
    return retriever

def reciprocal_rank_fusion(results: list[list], k=60):
    fused_scores = {}
    for docs in results:
        for rank, doc in enumerate(docs):
            doc_str = dumps(doc)
            if doc_str not in fused_scores:
                fused_scores[doc_str] = 0
            fused_scores[doc_str] += 1 / (rank + k)

    reranked_results = [
        (loads(doc), score)
        for doc, score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
    ]

    return [x[0] for x in reranked_results[:MAX_DOCS_FOR_CONTEXT]]

def query_generator(original_query: dict) -> list[str]:
    query = original_query.get("query")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that generates multiple search queries based on a single input query."),
        ("user", "Generate multiple search queries related to: {original_query}. When creating queries, please refine or add closely related contextual information to improve search results, without significantly altering the original query's meaning."),
        ("user", "OUTPUT (3 queries):")
    ])

    model = ChatOpenAI(temperature=0, model_name=LLM_MODEL_OPENAI)
    query_generator_chain = prompt | model | StrOutputParser() | (lambda x: x.split("\n"))
    queries = query_generator_chain.invoke({"original_query": query})
    queries.insert(0, "0. " + query)
    return queries

def rrf_retriever(query: str, retriever: BaseRetriever) -> list:
    chain = (
        {"query": itemgetter("query")}
        | RunnableLambda(query_generator)
        | retriever.map()
        | reciprocal_rank_fusion
    )
    result = chain.invoke({"query": query})
    return result
