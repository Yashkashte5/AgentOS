import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
STRONG_MODEL = "llama-3.3-70b-versatile"
LIGHT_MODEL  = "llama-3.1-8b-instant"

# Self-heal
MAX_RETRIES = 3

EXECUTION_TIMEOUT = 60  


LANGCHAIN_TRACING_V2  = os.getenv("LANGCHAIN_TRACING_V2", "")
LANGCHAIN_API_KEY     = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT     = os.getenv("LANGCHAIN_PROJECT", "")