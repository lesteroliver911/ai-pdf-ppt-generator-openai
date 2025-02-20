import os
import json
import logging
from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from langchain_text_splitters import TokenTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

LLM_MODEL_OPENAI = os.getenv('LLM_MODEL_OPENAI', 'gpt-4o')  # Fallback to gpt-3.5-turbo if not set
logger.info(f"LLM_MODEL_OPENAI: {LLM_MODEL_OPENAI}")

def load_and_analyze_document(pdf_file) -> tuple[list, dict]:
    with open("temp.pdf", "wb") as f:
        f.write(pdf_file.read())
    
    try:
        # Set up LlamaParse
        parser = LlamaParse(
            api_key=os.getenv('LLAMA_PARSE_API_KEY'),
            parsing_instruction = "You are parsing PDF that have text, images and tables. Make sure to extract all the content including the header and footer.Mandatory!",
            use_vendor_multimodal_model=True,
            vendor_multimodal_model_name="openai-gpt4o",
            invalidate_cache=True,
            result_type="markdown", 
            request_timeout=300
            
        )
        
        # Use SimpleDirectoryReader with LlamaParse
        file_extractor = {".pdf": parser}
        documents = SimpleDirectoryReader(input_files=['temp.pdf'], file_extractor=file_extractor).load_data()
        
        # Convert LlamaParse documents to LangChain documents
        langchain_docs = [Document(page_content=doc.text, metadata=doc.metadata) for doc in documents]
        
        text_splitter = TokenTextSplitter(chunk_size=2048, chunk_overlap=24)
        split_documents = text_splitter.split_documents(langchain_docs)
        
        logger.info(f"Initializing ChatOpenAI with model: {LLM_MODEL_OPENAI}")
        llm = ChatOpenAI(model=LLM_MODEL_OPENAI, temperature=0)
        analysis_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyze the following document content and provide a brief summary:
            1. Main topics covered
            2. Key sections or chapters
            3. Suggested presentation structure (max 10 slides)

            Content:
            {content}

            Return the analysis as a JSON object. This is Critical & MANDATORY! No Hallucinaion
            """
        )
        content = "\n".join([doc.page_content for doc in split_documents])
        analysis = llm.invoke(analysis_prompt.format(content=content))
        
        logger.info(f"Raw API response: {analysis.content}")
        
        # Attempt to parse JSON, if it fails, return the content as a string
        try:
            analysis_json = json.loads(analysis.content)
        except json.JSONDecodeError as json_error:
            logger.warning(f"Failed to parse JSON: {str(json_error)}")
            analysis_json = {"analysis": analysis.content}
        
        logger.info(f"Document analyzed: {len(split_documents)} chunks")
        return split_documents, analysis_json
    except Exception as e:
        logger.error(f"Error in load_and_analyze_document: {str(e)}")
        raise
    finally:
        os.remove("temp.pdf")
