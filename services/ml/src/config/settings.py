from dotenv import load_dotenv
import os

load_dotenv()

PORT = os.getenv("PORT", 8001)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing.")