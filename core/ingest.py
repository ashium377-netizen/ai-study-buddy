import io

from pypdf import PdfReader

from core import llm

IMAGE_MIME = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}
SUPPORTED = ["pdf", "docx", "pptx", "txt", "md"] + list(IMAGE_MIME)
MAX_OCR_PAGES = 15


def _ext(name):
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def _pdf(data):
    reader = PdfReader(io.BytesIO(data))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    if len(text.split()) >= 30:
        return text

    # Probably a scanned PDF: read the page images instead.
    parts = []
    for page in list(reader.pages)[:MAX_OCR_PAGES]:
        for img in page.images:
            mime = IMAGE_MIME.get(_ext(img.name), "image/png")
            parts.append(llm.image_to_text(img.data, mime))
    return "\n\n".join(p for p in parts if p) or text


def _docx(data):
    from docx import Document

    doc = Document(io.BytesIO(data))
    lines = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                lines.append(" | ".join(cells))
    return "\n".join(lines)


def _pptx(data):
    from pptx import Presentation

    prs = Presentation(io.BytesIO(data))
    out = []
    for n, slide in enumerate(prs.slides, start=1):
        lines = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    t = "".join(run.text for run in para.runs).strip()
                    if t:
                        lines.append(t)
            if getattr(shape, "has_table", False) and shape.has_table:
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        lines.append(" | ".join(cells))
        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                lines.append(f"Notes: {notes}")
        if lines:
            out.append(f"Slide {n}:\n" + "\n".join(lines))
    return "\n\n".join(out)


def read_bytes(data, name):
    """Turn an uploaded file (as bytes) into plain text."""
    ext = _ext(name)
    if ext == "pdf":
        text = _pdf(data)
    elif ext == "docx":
        text = _docx(data)
    elif ext == "pptx":
        text = _pptx(data)
    elif ext in ("txt", "md"):
        text = data.decode("utf-8", errors="replace")
    elif ext in IMAGE_MIME:
        text = llm.image_to_text(data, IMAGE_MIME[ext])
    else:
        raise ValueError(
            f"'.{ext}' files aren't supported. Use: " + ", ".join(SUPPORTED)
        )
    if len(text.split()) < 5:
        raise ValueError(
            "Couldn't find readable text in this file. If it's a scan or a photo, "
            "check that the image is clear."
        )
    return text


def read_document(uploaded):
    """Read a Streamlit UploadedFile."""
    return read_bytes(uploaded.getvalue(), uploaded.name)


def chunk_text(text, size=150, overlap=30):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
        start += size - overlap
    return chunks


def add_note(text, source):
    """Chunk the text and save it to the knowledge base. Returns chunk count."""
    from core import embed

    chunks = chunk_text(text)
    if not chunks:
        raise ValueError("Nothing to save: the notes are empty.")
    return embed.add_chunks(chunks, source)
