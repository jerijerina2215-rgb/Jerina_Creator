import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_PROJECT = os.getenv("GEMINI_PROJECT")
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
