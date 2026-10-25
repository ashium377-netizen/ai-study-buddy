import re

from core import embed, llm

FORMULA_RULE = (
    "Write formulas and numbers in plain text with Unicode symbols, for example "
    "E = hν = hc/λ and h = 6.626 × 10⁻³⁴ J·s. Do NOT use LaTeX, backslashes, or $ signs."
)


def fix_math(text):
    """Turn leftover LaTeX into something Streamlit can draw."""
    text = text or ""
    text = re.sub(r"\\\[(.+?)\\\]", lambda m: f"$$ {m.group(1).strip()} $$", text, flags=re.S)
    text = re.sub(r"\\\((.+?)\\\)", lambda m: f"${m.group(1).strip()}$", text, flags=re.S)
    # "(E=h\nu=...)" : the backslash before the bracket was lost earlier
    text = re.sub(
        r"\(([^()\n]*\\[A-Za-z][^()\n]*)\)",
        lambda m: f"${m.group(1).strip()}$",
        text,
    )
    return text

_FOLLOW_UP_WORDS = {
    "it", "that", "this", "those", "these", "they", "them",
    "its", "above", "previous", "more", "simpler", "again",
}


def looks_like_follow_up(question):
    words = question.lower().replace("?", " ").split()
    return len(words) <= 6 or any(w in _FOLLOW_UP_WORDS for w in words)


def _history_text(history, max_turns=4):
    recent = history[-max_turns * 2:]
    lines = []
    for m in recent:
        who = "Student" if m["role"] == "user" else "Assistant"
        lines.append(f"{who}: {m['content'][:500]}")
    return "\n".join(lines)


def rewrite_question(question, history):
    if not history or not looks_like_follow_up(question):
        return question
    prompt = f"""Rewrite the student's latest message as ONE standalone question that makes sense without the conversation. Keep the meaning. If it is already standalone, a greeting, or a thanks, return it unchanged. Return ONLY the question.

CONVERSATION:
{_history_text(history)}

LATEST MESSAGE: {question}

STANDALONE QUESTION:"""
    try:
        text = llm.generate(prompt).strip()
        return text or question
    except Exception:
        return question


def answer(question, history=None, k=3, source=None):
    history = history or []
    standalone = rewrite_question(question, history)
    results = embed.search(standalone, k=k, source=source)
    if not results:
        return "No notes saved yet. Add some notes in the sidebar first.", []

    context = "\n\n".join(
        f"[{i + 1}] (Source: {r['source']}, chunk {r['chunk_index'] + 1})\n{r['text']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a friendly study assistant.

RULES:
- Answer using ONLY the notes below. You only see a few excerpts, not the whole document.
- If the student greets you or says thanks, reply briefly and warmly, and say you can answer questions about their notes.
- If the answer is not in the excerpts, reply exactly: "I couldn't find that in your notes."
- If the student asks you to summarize everything, say you only see a few excerpts and suggest the Summary tab.
- Keep answers short and clear, and cite note numbers like [1].
- Use the conversation only to understand what words like "it" or "that" refer to.

CONVERSATION SO FAR:
{_history_text(history) or "(none)"}

NOTES:
{context}

STUDENT QUESTION: {question}
(Searched as: {standalone})

ANSWER:"""

    return fix_math(llm.generate(prompt)), results


def summarize_source(source, batch_size=40):
    chunks = embed.get_source_chunks(source)
    if not chunks:
        return "No notes found for this file."

    parts = []
    for i in range(0, len(chunks), batch_size):
        batch = "\n\n".join(chunks[i:i + batch_size])
        parts.append(llm.generate(f"""Summarize these study notes as exam-oriented bullet points.
Group them under short headings (use ## for headings). Include key definitions, numbers, formulas, and examples.
Use only the notes below.
{FORMULA_RULE}

NOTES:
{batch}

SUMMARY:"""))

    if len(parts) == 1:
        return fix_math(parts[0])

    combined = "\n\n".join(parts)
    return fix_math(llm.generate(f"""Combine these partial summaries into ONE organized bullet-point summary with short headings (use ## for headings). Remove repeated points.
{FORMULA_RULE}

PARTIAL SUMMARIES:
{combined}

FINAL SUMMARY:"""))
