import json
import re

from core import embed, llm

CARD_PROMPT = """You are creating flashcards for a student from the study notes below.

Write up to {n} flashcards. RULES:
- Use ONLY facts stated in the notes.
- Each question must make sense on its own. Never say "the passage", "the notes", "the text" or "according to".
- One idea per card, and never two cards about the same fact.
- Prefer definitions, differences, causes, steps, formulas, and numbers.
- Answers must be short (1-2 sentences).
- Skip trivia, headings, and anything unclear or garbled.
- Topic: a broad label of 1-3 words (like "Temperature" or "Roles"). Reuse the same label for related cards.

Return ONLY a JSON list with no other text, in exactly this format:
[{{"question": "...", "answer": "...", "topic": "..."}}]

NOTES:
{notes}
"""

BAD_QUESTION = re.compile(
    r"\b(the (passage|text|notes|document|excerpt)|according to)\b", re.I
)

STOPWORDS = {
    "what", "is", "are", "the", "a", "an", "of", "in", "on", "to", "for",
    "does", "do", "did", "how", "which", "when", "why", "and", "or", "with",
    "by", "it", "its", "that", "this", "be", "can", "as", "at", "from",
}


def extract_json(text):
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.DOTALL)
    text = text.replace("```json", "").replace("```", "")
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON list found")
    return json.loads(text[start:end + 1])


def _clean(cards):
    good = []
    for c in cards:
        if not isinstance(c, dict):
            continue
        q = str(c.get("question", "")).strip()
        a = str(c.get("answer", "")).strip()
        t = str(c.get("topic", "")).strip().title() or "General"
        if len(q) < 10 or len(a) < 2:
            continue
        if BAD_QUESTION.search(q):
            continue
        good.append({"question": q, "answer": a, "topic": t})
    return good


def content_words(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _is_duplicate(card, seen):
    q = content_words(card["question"])
    a = content_words(card["answer"])
    for other in seen:
        q_sim = jaccard(q, content_words(other["question"]))
        a_sim = jaccard(a, content_words(other["answer"]))
        if q_sim >= 0.5 or (a_sim >= 0.5 and q_sim >= 0.3):
            return True
    return False


def generate_cards_for_chunk(chunk, n=3, retries=2):
    prompt = CARD_PROMPT.format(n=n, notes=chunk)
    for _ in range(retries + 1):
        try:
            return _clean(extract_json(llm.generate(prompt)))
        except (ValueError, json.JSONDecodeError):
            continue
    return []


def generate_for_source(source, max_chunks=None, per_chunk=3, progress=None):
    chunks = embed.get_source_chunks(source)
    if max_chunks:
        chunks = chunks[:max_chunks]

    cards, seen = [], []
    for i, chunk in enumerate(chunks):
        if len(chunk.split()) >= 30:
            for c in generate_cards_for_chunk(chunk, n=per_chunk):
                if _is_duplicate(c, seen):
                    continue
                seen.append(c)
                c["chunk_index"] = i
                cards.append(c)
        if progress:
            progress(i + 1, len(chunks))
    return cards
