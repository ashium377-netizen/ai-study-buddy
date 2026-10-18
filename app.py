import streamlit as st
from core.ingest import extract_text, chunk_text
from core.embed import add_chunks, search

st.title("AI Study Buddy")

uploaded = st.file_uploader("Upload your notes (PDF)", type="pdf")

if uploaded:
    text = extract_text(uploaded)
    chunks = chunk_text(text)
    st.success(f"Extracted {len(text.split())} words into {len(chunks)} chunks")

    if st.button("Save to knowledge base"):
        with st.spinner("Embedding chunks... the first time takes longer"):
            n = add_chunks(chunks, source=uploaded.name)
        st.success(f"Saved {n} chunks from {uploaded.name}")

st.divider()
st.subheader("Search your notes")
query = st.text_input("Ask something about your notes")

if query:
    results = search(query)
    if not results:
        st.warning("No notes saved yet. Upload a PDF and click 'Save to knowledge base' first.")
    for r in results:
        st.markdown(
            f"**{r['source']}, chunk {r['chunk_index'] + 1}** "
            f"(distance: {r['distance']:.2f})"
        )
        st.write(r["text"])