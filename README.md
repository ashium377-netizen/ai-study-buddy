# 📚 AI Study Buddy

Turn your own notes into a study system. Upload a PDF, Word file, PowerPoint, text file or a photo of your notes, then chat with them, summarise them, revise with spaced-repetition flashcards, take graded tests and track your progress.

Everything the AI says comes from **your notes**, and answers show the sections they came from.

## Features

- **Chat with your notes (RAG):** ask questions and get answers grounded in your own material, with the source sections shown. Follow-up questions are understood in context.
- **Smart summaries:** an exam-ready summary of a whole file, organised under headings, downloadable as Markdown.
- **Spaced-repetition flashcards:** AI-generated cards you flip and rate (Again / Hard / Good / Easy). A scheduler decides when each card returns, so you review it just before you would forget it.
- **Graded tests:** multiple-choice tests with an explanation for every answer and a score per topic.
- **Progress dashboard:** study streak, review history, recall rate, card maturity and weakest topics.
- **Many input types:** PDF, DOCX, PPTX, TXT, MD and images (printed or handwritten notes, read with OCR). Scanned PDFs fall back to OCR automatically.
- **Works on phones too:** the layout adapts to small screens.
- **Background generation:** tests, flashcards and summaries keep generating while you open other tabs.

## How it works

```
Upload file → extract text → split into ~150-word chunks (30-word overlap)
            → embed each chunk (MiniLM) → store in ChromaDB

Question → embed → find the 3 most similar chunks
         → send chunks + question to the LLM → answer with sources
```

This is **Retrieval-Augmented Generation (RAG)**: instead of answering from its general knowledge, the model is given the most relevant parts of your notes and told to answer only from them. That reduces made-up answers and lets every answer cite where it came from.

## Architecture

```
Browser
   │
   ▼
app.py  (Streamlit UI: landing page, sidebar, Home / Chat / Summary / Flashcards / Test / Progress)
   │
   ▼
core/  (the engine, no UI code)
   ├── ingest.py         file → plain text (PDF, DOCX, PPTX, TXT, images via OCR)
   ├── embed.py          chunking, embeddings, ChromaDB storage and search
   ├── rag.py            retrieval + answer / summary prompts
   ├── llm.py            one interface to Gemini, Groq or Ollama (with retries)
   ├── cards.py          flashcard generation (strict JSON, duplicate removal)
   ├── quiz.py           test generation and grading
   ├── srs.py            spaced-repetition scheduling (SM-2 style)
   ├── stats.py          streaks, review history, weak topics
   ├── db.py             SQLite reads and writes
   └── flashcard_ui.py   the flip-card component

Storage (created on first run, not in Git)
   ├── chroma_db/        vector index of your notes
   └── study_buddy.db    cards, summaries, test attempts, review log
```

**Why two databases?** ChromaDB is built for similarity search over text meaning. SQLite stores structured records such as review dates and scores.

## Tech stack

| Part | Technology |
|---|---|
| UI | Streamlit, custom CSS, Altair charts |
| Language | Python 3.11 |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`), runs locally |
| Vector database | ChromaDB |
| Relational database | SQLite |
| LLM | Google Gemini (default), Groq or Ollama, switchable in `.env` |
| OCR | Gemini vision (default) or Tesseract |
| File parsing | pypdf, python-docx, python-pptx |

## Getting started

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/ashium377-netizen/ai-study-buddy.git
cd ai-study-buddy
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

The first run downloads the embedding model, so it needs an internet connection and takes a little longer.

### 2. Add your settings

Create a file named `.env` in the project folder:

```env
# Choose one: gemini (default), groq, ollama
LLM_PROVIDER=gemini

GEMINI_API_KEY=your-key-here
# GROQ_API_KEY=your-key-here

# Optional
# GEMINI_MODEL=gemini-3.5-flash
# GROQ_MODEL=llama-3.3-70b-versatile
# OLLAMA_MODEL=llama3.2:3b
# OCR_PROVIDER=tesseract      # default is gemini
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

- **Gemini:** free key at Google AI Studio.
- **Groq:** free key at console.groq.com.
- **Ollama:** no key needed. Install Ollama, run `ollama pull llama3.2:3b` and set `LLM_PROVIDER=ollama`. Everything then runs offline except the first model download.

The `.env` file is listed in `.gitignore`, so your keys are never uploaded.

### 3. Run

```bash
streamlit run app.py
```

Open the address shown in the terminal (usually http://localhost:8501).

## Using the app

1. Click **Get started** on the landing page.
2. Add notes in the sidebar: upload a file or paste text.
3. Use the tabs: **Chat**, **Summary**, **Flashcards**, **Test** and **Progress**.
4. Come back daily and review your due cards to keep your streak going.

## Design decisions

- **Provider switch:** free API limits differ, so changing models is a one-line edit in `.env`.
- **Retries with backoff:** temporary API failures (rate limits, server busy) are retried automatically instead of crashing.
- **Strict JSON from the LLM:** flashcard and test outputs are validated and repaired, and near-duplicates are removed with word-overlap (Jaccard) similarity.
- **Engine/UI split:** all logic lives in `core/`, so it can be tested and reused without Streamlit.
- **Background threads:** slow AI generation runs in a thread, so switching tabs doesn't interrupt it.

## Limitations

- There are no user accounts. All notes on one installation are shared.
- Data is stored on local disk, so hosts with temporary disks would lose it between restarts.
- Embeddings run locally, which needs more memory than most free cloud hosts offer.
- Answer quality depends on the LLM and on how clearly the notes are written. Handwriting OCR can make mistakes.

## Possible future work

- User accounts and a hosted database
- Hosted embeddings for lightweight cloud deployment
- Automated tests for the scheduler, grading and JSON repair
- Export decks to Anki

## Author

Built by Ashium, Debajit and Priyangshu as a minor project.
