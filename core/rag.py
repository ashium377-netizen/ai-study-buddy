from core.embed import search
from core.llm import generate

def answer(question, k=3):
    results = search(question, k=k)
    if not results:
        return "No notes saved yet. Upload a PDF and save it to the knowledge base first.", []

    context = "\n\n".join(
        f"[{i + 1}] (Source: {r['source']}, chunk {r['chunk_index'] + 1})\n{r['text']}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a study assistant. Answer the student's question using ONLY the notes below.
If the answer is not in the notes, reply exactly: "I couldn't find that in your notes."
Keep the answer short and clear. Mention the note number(s) you used, like [1].

NOTES:
{context}

QUESTION: {question}

ANSWER:"""

    return generate(prompt), results