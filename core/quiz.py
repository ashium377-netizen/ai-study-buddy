import json
import math
import random

from core import embed, llm
from core.cards import content_words, extract_json, jaccard

QUIZ_PROMPT = """You are writing a multiple-choice test for a student from the study notes below.

Write {n} questions. RULES:
- Use ONLY facts stated in the notes.
- Each question must make sense on its own. Never say "the passage", "the notes", "the text" or "according to".
- Exactly 4 options. One is correct. The other three are believable wrong answers, not silly ones.
- Never use "all of the above" or "none of the above".
- Keep the options short and similar in length.
- explanation: one sentence on why the correct answer is right.
- topic: a broad label of 1-3 words.
- Never ask two questions about the same fact.

Return ONLY a JSON list with no other text, in exactly this format:
[{{"question": "...", "options": ["...", "...", "...", "..."], "answer": 0, "explanation": "...", "topic": "..."}}]
"answer" is the position (0, 1, 2 or 3) of the correct option in "options".

NOTES:
{notes}
"""

LETTERS = "ABCD"


def _clean(items):
    good = []
    for it in items:
        if not isinstance(it, dict):
            continue
        q = str(it.get("question", "")).strip()
        opts = it.get("options")
        if len(q) < 10 or not isinstance(opts, list) or len(opts) != 4:
            continue
        opts = [str(o).strip() for o in opts]
        if any(not o for o in opts) or len({o.lower() for o in opts}) != 4:
            continue
        try:
            ans = int(it.get("answer"))
        except (TypeError, ValueError):
            continue
        if ans not in (0, 1, 2, 3):
            continue
        correct = opts[ans]
        random.shuffle(opts)  # models love putting the answer at A
        good.append({
            "question": q,
            "options": opts,
            "answer": opts.index(correct),
            "explanation": str(it.get("explanation", "")).strip(),
            "topic": str(it.get("topic", "")).strip().title() or "General",
        })
    return good


def _ask(notes, n, retries=2):
    prompt = QUIZ_PROMPT.format(n=n, notes=notes)
    for _ in range(retries + 1):
        try:
            return _clean(extract_json(llm.generate(prompt)))
        except (ValueError, json.JSONDecodeError):
            continue
    return []


def _is_duplicate(q, seen):
    w = content_words(q["question"])
    return any(jaccard(w, content_words(s["question"])) >= 0.6 for s in seen)


def _groups(chunks, g):
    size = len(chunks) / g
    return [chunks[round(i * size):round((i + 1) * size)] for i in range(g)]


def generate_quiz(source, n=10, progress=None):
    chunks = embed.get_source_chunks(source)
    if not chunks:
        return []

    g = max(1, min(n, len(chunks)))
    groups = ["\n\n".join(part) for part in _groups(chunks, g) if part]
    per_group = math.ceil(n / len(groups))

    questions = []
    for i, notes in enumerate(groups):
        for q in _ask(notes, per_group):
            if not _is_duplicate(q, questions):
                q["group"] = i
                questions.append(q)
        if progress:
            progress(i + 1, len(groups))

    # Top up if some calls came back short.
    tries = 0
    while len(questions) < n and tries < 3:
        tries += 1
        i = random.randrange(len(groups))
        for q in _ask(groups[i], n - len(questions)):
            if not _is_duplicate(q, questions):
                q["group"] = i
                questions.append(q)

    if len(questions) > n:
        questions = sorted(random.sample(questions, n), key=lambda q: q["group"])
    return questions


def grade(questions, answers):
    """answers: {question_index: chosen_option_index, or -1 for 'don't know'}"""
    results, per_topic = [], {}
    correct = 0
    for i, q in enumerate(questions):
        chosen = answers.get(i)
        if chosen is None or chosen == -1:
            status = "skipped"
        elif chosen == q["answer"]:
            status = "correct"
            correct += 1
        else:
            status = "wrong"
        topic = per_topic.setdefault(q["topic"], {"correct": 0, "total": 0})
        topic["total"] += 1
        topic["correct"] += status == "correct"
        results.append({"index": i, "status": status, "chosen": chosen})
    return {
        "total": len(questions),
        "correct": correct,
        "per_topic": per_topic,
        "results": results,
    }
