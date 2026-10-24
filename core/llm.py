import io
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()
_client = None


def _gemini_client():
    from google import genai

    global _client
    if _client is None:
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY not found. Check your .env file.")
        _client = genai.Client(api_key=key)
    return _client


def _gemini_call(contents, retries=4):
    from google.genai import errors

    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    delay = 3
    for attempt in range(retries):
        try:
            return _gemini_client().models.generate_content(
                model=model, contents=contents
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
    return _gemini_call(prompt)


OCR_PROMPT = (
    "Transcribe all the text in this image exactly as written, in reading order. "
    "It may be printed or handwritten. Keep headings, bullet points, and formulas. "
    "If there is a diagram or chart, add a short description of it in [square brackets]. "
    "Return only the transcription, with no extra commentary."
)


def _gemini_image_to_text(data, mime):
    from google.genai import types

    part = types.Part.from_bytes(data=data, mime_type=mime)
    return (_gemini_call([part, OCR_PROMPT]) or "").strip()


def _tesseract_image_to_text(data):
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise RuntimeError(
            "Local OCR needs: pip install pytesseract pillow, plus the Tesseract "
            "program installed on Windows."
        )
    cmd = os.getenv("TESSERACT_CMD")
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
    return pytesseract.image_to_string(Image.open(io.BytesIO(data))).strip()


def image_to_text(data, mime="image/png"):
    """Read text from an image. OCR_PROVIDER=gemini (default) or tesseract."""
    if os.getenv("OCR_PROVIDER", "gemini").lower() == "tesseract":
        return _tesseract_image_to_text(data)
    return _gemini_image_to_text(data, mime)
