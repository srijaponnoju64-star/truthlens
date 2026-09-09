import os
from dotenv import load_dotenv
from groq import Groq

# Load .env from project root (works regardless of where uvicorn is started from)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise EnvironmentError(
        "GROQ_API_KEY is not set. "
        "Add it to your .env file: GROQ_API_KEY=gsk_..."
    )

groq_client = Groq(api_key=GROQ_API_KEY)
