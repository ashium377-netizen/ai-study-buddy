import streamlit as st
from core.ingest import extract_text, chunk_text

st.title("AI Study Buddy")

uploaded = st.file_uploader("Upload your notes (PDF)", type="pdf")

if uploaded:
    text = extract_text(uploaded)
    chunks = chunk_text(text)
    st.success(f"Extracted {len(text.split())} words into {len(chunks)} chunks")
    for i, c in enumerate(chunks[:3]):
        st.subheader(f"Chunk {i + 1}")
        st.write(c)