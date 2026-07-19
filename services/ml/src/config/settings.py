from dotenv import load_dotenv
import os

load_dotenv()

PORT = os.getenv("PORT", 8001)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")