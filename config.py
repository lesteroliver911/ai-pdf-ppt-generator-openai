import os
from dotenv import load_dotenv

load_dotenv()

LLM_MODEL_OPENAI = "gpt-4o"  # Updated to the latest official GPT-4 model
EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 5
MAX_DOCS_FOR_CONTEXT = 8
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FLASK_SECRET_KEY = '192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf'
