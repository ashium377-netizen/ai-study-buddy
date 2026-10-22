import os
import time
import re
from dotenv import load_dotenv

load_dotenv()
_client = None


def _gemini(prompt, retries=4):
    from google import genai
    from google.genai import errors

    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not found. Check your .env file.")
        _client = genai.Client(api_key=key)

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    delay = 3
    for attempt in range(retries):
        try:
            return _client.models.generate_content(
                model=model, contents=prompt
            ).text
        except errors.APIError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise


def _ollama(prompt):
    import ollama

    model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    response = ollama.chat(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    text = response["message"]["content"]
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return text.strip()


def generate(prompt):
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "ollama":
        return _ollama(prompt)
    return _gemini(prompt)