import streamlit as st
from core.ingest import extract_text, chunk_text
from core.embed import add_chunks, list_sources, delete_source, clear_all
from core.rag import answer, summarize_source

st.title("AI Study Buddy")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Your notes")
    uploaded = st.file_uploader("Upload notes (PDF)", type="pdf")
    if uploaded:
        text = extract_text(uploaded)
        chunks = chunk_text(text)
        st.write(f"{len(text.split())} words, {len(chunks)} chunks")
        if st.button("Save to knowledge base"):
            with st.spinner("Embedding chunks..."):
                n = add_chunks(chunks, source=uploaded.name)
            st.success(f"Saved {n} chunks from {uploaded.name}")
            st.rerun()

    st.divider()
    st.subheader("Saved notes")
    sources = list_sources()
    if not sources:
        st.caption("Nothing saved yet.")
    for name, count in sources.items():
        st.write(f"**{name}** ({count} chunks)")
        c1, c2 = st.columns(2)
        if c1.button("Summarize", key=f"sum_{name}"):
            with st.spinner("Summarizing..."):
                try:
                    summary = summarize_source(name)
                except Exception as e:
                    summary = f"Something went wrong: {e}"
            st.session_state.messages.append(
                {"role": "assistant", "content": f"**Summary of {name}**\n\n{summary}"}
            )
            st.rerun()
        if c2.button("Delete", key=f"del_{name}"):
            delete_source(name)
            st.rerun()
    if sources and st.button("Clear everything"):
        clear_all()
        st.session_state.messages = []
        st.rerun()

st.subheader("Ask your notes")


def show_sources(srcs):
    if srcs:
        with st.expander("Sources"):
            for s in srcs:
                st.markdown(f"**{s['source']}, chunk {s['chunk_index'] + 1}**")
                st.write(s["text"])


for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.write(m["content"])
        show_sources(m.get("sources"))

question = st.chat_input("Ask a question about your notes")

if question:
    history = list(st.session_state.messages)
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                reply, sources_used = answer(question, history=history)
            except Exception as e:
                reply, sources_used = f"Something went wrong: {e}", []
        st.write(reply)
        show_sources(sources_used)

    st.session_state.messages.append(
        {"role": "assistant", "content": reply, "sources": sources_used}
    )