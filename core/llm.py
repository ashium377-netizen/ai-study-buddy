import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
_client = None

def get_client():
    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not found. Check your .env file.")
        _client = genai.Client(api_key=key)
    return _client

def generate(prompt, retries=4):
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    delay = 2
    for attempt in range(retries):
        try:
            response = get_client().models.generate_content(
                model=model, contents=prompt
            )
            return response.text
        except errors.ServerError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)
            delay *= 2