import html
import os
import random
from datetime import date
import time

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from core import cards as cardlib
from core import db, embed, ingest, rag, srs, stats
from core import quiz as quizlib
from core.flashcard_ui import card_html

st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide")
db.init_db()

ACCENT = "#7c5cff"
INK = "#1f2340"

st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, li, input, textarea,
  button p, div[data-testid="stMarkdownContainer"], div[data-testid="stMetricValue"] {
    font-family: 'Inter', 'Source Sans Pro', system-ui, sans-serif;
  }
  footer, #MainMenu { visibility: hidden; }
  .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1100px; }

  /* sidebar */
  section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f4f0ff 0%, #fbfaff 100%);
    border-right: 1px solid #e2dcff;
  }

  /* buttons */
  .stButton > button, .stDownloadButton > button {
    border-radius: 12px; font-weight: 600; padding: 0.55rem 1rem;
    border: 1px solid #d9d0ff; transition: transform .12s ease, box-shadow .12s ease;
  }
  .stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-1px); box-shadow: 0 6px 16px rgba(124, 92, 255, .18);
    border-color: #7c5cff;
  }
  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7c5cff 0%, #9b6bff 100%); border: none; color: #fff;
  }

  div[data-testid="stColumn"] div[data-testid="stElementContainer"]:has(> .stButton),
  div[data-testid="stColumn"] .stButton { width: 100% !important; }
  div[data-testid="stColumn"] .stButton > button { width: 100%; }

  /* metric cards */
  div[data-testid="stMetric"] {
    background: #ffffff; border: 1px solid #e8e2ff; border-radius: 16px;
    padding: 14px 18px; box-shadow: 0 2px 10px rgba(124, 92, 255, .07);
  }
  div[data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; color: #1f2340; }
  div[data-testid="stMetricLabel"] p { color: #6b7280; font-weight: 600; }

  /* expanders, chat, tables, bordered boxes */
  div[data-testid="stExpander"] {
    border: 1px solid #e8e2ff; border-radius: 14px; background: #ffffff; overflow: hidden;
  }
  div[data-testid="stChatMessage"] {
    background: #ffffff; border: 1px solid #eee9ff; border-radius: 16px; padding: 14px 16px;
  }
  div[data-testid="stDataFrame"] {
    border: 1px solid #e8e2ff; border-radius: 12px; overflow: hidden;
  }
  div[data-testid="stAlert"] { border-radius: 14px; }
  h1, h2, h3 { letter-spacing: -0.02em; font-weight: 700; }

  /* hero / landing page */
  .hero { text-align: center; padding: 2.2rem 0 1.2rem; }
  .hero h1 {
    font-size: 3rem; font-weight: 800; line-height: 1.1; margin: 0 0 .6rem;
    background: linear-gradient(135deg, #5b3df5 0%, #b36bff 100%);
    -webkit-background-clip: text; background-clip: text; color: transparent;
  }
  .hero p { font-size: 1.15rem; color: #5b6078; max-width: 640px; margin: 0 auto; }
  .pill {
    display: inline-block; background: #efe9ff; color: #5b3df5; font-weight: 600;
    font-size: .8rem; padding: 4px 12px; border-radius: 999px; margin-bottom: 1rem;
  }
  .feature-grid {
    display: flex; flex-wrap: wrap; justify-content: center;
    gap: 16px; margin: 1.8rem 0 1.2rem;
  }
  .feature {
    flex: 1 1 230px; max-width: 262px;
    background: #ffffff; border: 1px solid #e8e2ff; border-radius: 18px; padding: 20px;
    box-shadow: 0 2px 12px rgba(124, 92, 255, .07); transition: transform .15s ease, box-shadow .15s ease;
  }
  .feature:hover { transform: translateY(-3px); box-shadow: 0 10px 24px rgba(124, 92, 255, .16); }
  .feature .ico { font-size: 1.8rem; margin-bottom: 8px; }
  .feature b { display: block; font-size: 1.05rem; margin-bottom: 4px; color: #1f2340; }
  .feature span { color: #6b7280; font-size: .93rem; line-height: 1.45; }
  .steps { display: flex; gap: 14px; flex-wrap: wrap; justify-content: center; margin-top: 1rem; }
  .step {
    background: #f1edff; border-radius: 14px; padding: 10px 16px; color: #3b2fa0;
    font-weight: 600; font-size: .95rem;
  }
  .step i {
    font-style: normal; background: #7c5cff; color: #fff; border-radius: 999px;
    padding: 1px 9px; margin-right: 8px; font-size: .85rem;
  }

  /* header chip for the active file */
  .file-chip {
    display: inline-block; background: #efe9ff; color: #3b2fa0; font-weight: 600;
    padding: 6px 14px; border-radius: 999px; font-size: .9rem; margin-bottom: .6rem;
    max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

  /* phones */
  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 3.8rem; }
    .hero h1 { font-size: 2.1rem; }
    .hero p { font-size: 1rem; }
    div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; gap: .6rem; }
    div[data-testid="stColumn"] { min-width: calc(50% - .6rem) !important; flex: 1 1 calc(50% - .6rem) !important; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; }
  }
</style>
""",
    unsafe_allow_html=True,
)


def _style(chart, height):
    return (
        chart.properties(height=height)
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelColor="#6b7280", titleColor="#6b7280", gridColor="#eee9ff",
            domainColor="#e2dcff", tickColor="#e2dcff", labelFontSize=12,
        )
    )


def themed_bar(df, x, y, height=260):
    chart = (
        alt.Chart(df)
        .mark_bar(color=ACCENT, cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X(f"{x}:N", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{y}:Q", title=None, axis=alt.Axis(tickMinStep=1)),
            tooltip=[x, y],
        )
    )
    return _style(chart, height)


def themed_line(df, x, y, height=260):
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:O", title="Test number", axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=None, scale=alt.Scale(domain=[0, 100])),
        tooltip=[x, y],
    )
    line = base.mark_line(color=ACCENT, strokeWidth=3)
    points = base.mark_point(color=ACCENT, filled=True, size=90)
    return _style(line + points, height)


def show_chart(chart):
    # Newer Streamlit uses width="stretch"; older versions use use_container_width.
    try:
        st.altair_chart(chart, width="stretch")
    except TypeError:
        st.altair_chart(chart, use_container_width=True)

LETTERS = "ABCD"

for _key, _default in (("messages", []), ("study", {}), ("test", None)):
    if _key not in st.session_state:
        st.session_state[_key] = _default

if "notice" in st.session_state:
    st.toast(st.session_state.pop("notice"))


def friendly_error(e):
    msg = str(e)
    low = msg.lower()
    if "429" in msg or "resource_exhausted" in low or "rate limit" in low:
        return (
            "The AI is rate-limited right now (too many requests). "
            "Wait a minute and try again, or switch to Ollama in your .env file."
        )
    if "503" in msg or "unavailable" in low:
        return "The AI service is busy right now. Please try again in a moment."
    if "groq_api_key" in low:
        return "No Groq key found. Add GROQ_API_KEY to your .env file."
    if "gemini_api_key" in low:
        return (
            "No Gemini key found. Add GEMINI_API_KEY to your .env file "
            "(needed to read images)."
        )
    if "connect" in low and "ollama" in low:
        return "Can't reach Ollama. Make sure the Ollama app is running."
    return f"Something went wrong: {msg}"


def model_label():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "groq":
        return f"Groq · {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}"
    if provider == "ollama":
        return f"Ollama · {os.getenv('OLLAMA_MODEL', 'llama3.2:3b')}"
    return f"Gemini · {os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')}"


def show_html(html_text, height):
    # Newer Streamlit replaces components.html with st.iframe.
    if hasattr(st, "iframe"):
        st.iframe(html_text, height=height)
    else:
        components.html(html_text, height=height)


def reset_study_state():
    st.session_state.pop("review", None)
    st.session_state.study = {}
    st.session_state.test = None


# ------------------------------------------------------------------ sidebar
sources = embed.list_sources()

with st.sidebar:
    st.title("📚 AI Study Buddy")
    st.subheader("Add notes")
    mode = st.radio(
        "How to add notes",
        ["Upload a file", "Paste text"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if mode == "Upload a file":
        st.caption("PDF · Word · PowerPoint · text · photos of notes")
        uploaded = st.file_uploader(
            "Upload notes",
            type=ingest.SUPPORTED,
            label_visibility="collapsed",
        )
        if uploaded and st.button("Save to my notes", type="primary", key="save_upload"):
            try:
                with st.spinner("Reading your file..."):
                    text = ingest.read_document(uploaded)
                with st.spinner("Saving your notes..."):
                    n = ingest.add_note(text, uploaded.name)
                reset_study_state()
                st.session_state["active"] = uploaded.name
                st.session_state["notice"] = f"Saved {uploaded.name} ({n} sections)"
                st.rerun()
            except Exception as e:
                st.error(friendly_error(e))
    else:
        title = st.text_input("Name", placeholder="e.g. Biology chapter 3")
        pasted = st.text_area("Paste your notes", height=160)
        if st.button("Save pasted notes", type="primary", key="save_paste"):
            name = title.strip() or "Pasted notes"
            if len(pasted.split()) < 5:
                st.error("Paste a bit more text first.")
            else:
                try:
                    with st.spinner("Saving your notes..."):
                        n = ingest.add_note(pasted, name)
                    reset_study_state()
                    st.session_state["active"] = name
                    st.session_state["notice"] = f"Saved {name} ({n} sections)"
                    st.rerun()
                except Exception as e:
                    st.error(friendly_error(e))

    st.divider()
    st.subheader("Your notes")
    active = None
    if not sources:
        st.caption("Nothing saved yet.")
    else:
        names = list(sources)
        if st.session_state.get("active") not in names:
            st.session_state["active"] = names[0]
        active = st.selectbox("Working on", names, key="active")
        st.caption(
            f"{sources[active]} sections · {db.count_cards(active)} flashcards · "
            f"{db.due_count(active)} due"
        )
        streak_n = stats.streak()
        if streak_n:
            st.caption(f"🔥 {streak_n}-day study streak")
        with st.popover("🗑 Delete…"):
            if st.button("Delete this file", key="delete_active"):
                embed.delete_source(active)
                db.delete_source_data(active)
                reset_study_state()
                st.session_state["notice"] = f"Deleted {active}"
                st.rerun()
            if st.button("Delete everything", key="delete_all"):
                embed.clear_all()
                db.clear_all_data()
                st.session_state.messages = []
                reset_study_state()
                st.session_state["notice"] = "Deleted all notes"
                st.rerun()

    st.divider()
    st.caption(f"AI model: {model_label()}")


# ------------------------------------------------------------------ chat
def show_sources(srcs):
    if srcs:
        with st.expander("Sources"):
            for s in srcs:
                st.markdown(f"**{s['source']}, section {s['chunk_index'] + 1}**")
                st.write(s["text"])


def render_chat(active):
    search_all = True
    if len(sources) > 1:
        search_all = st.toggle(
            "Search across all my notes", value=True, key="chat_all"
        )
        st.caption(
            "Searching all notes" if search_all else f"Searching only {active}"
        )

    if st.session_state.messages and st.button("Clear chat", key="clear_chat"):
        st.session_state.messages = []
        st.rerun()

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
                    reply, used = rag.answer(
                        question,
                        history=history,
                        source=None if search_all else active,
                    )
                except Exception as e:
                    reply, used = friendly_error(e), []
            st.write(reply)
            show_sources(used)
        st.session_state.messages.append(
            {"role": "assistant", "content": reply, "sources": used}
        )


# ------------------------------------------------------------------ summary
def render_summary(active):
    summary = db.get_summary(active)
    st.subheader(f"Summary of {active}")
    label = "Regenerate summary" if summary else "Generate summary"
    if st.button(label, type="secondary" if summary else "primary", key="gen_summary"):
        try:
            with st.spinner("Reading all your notes... this can take a minute."):
                summary = rag.summarize_source(active)
            db.save_summary(active, summary)
        except Exception as e:
            st.error(friendly_error(e))
    if summary:
        st.markdown(rag.fix_math(summary))
        st.download_button(
            "Download summary (.md)",
            data=summary,
            file_name=f"{active.rsplit('.', 1)[0]}-summary.md",
            mime="text/markdown",
            key="dl_summary",
        )
    else:
        st.info(
            "Click the button to get an exam-ready summary of this whole file, "
            "organized under headings."
        )


# ------------------------------------------------------------------ flashcards
def render_flashcards(active):
    rows = db.get_cards(active)

    with st.expander("Create flashcards", expanded=not rows):
        c1, c2 = st.columns(2)
        per = c1.selectbox("Cards per section", [2, 3, 4], index=1, key="fc_per")
        quick = c2.checkbox("Quick test (first 5 sections only)", key="fc_quick")
        gen_label = "Regenerate flashcards" if rows else "Generate flashcards"
        if st.button(gen_label, type="primary", key="fc_gen"):
            bar = st.progress(0.0, text="Starting...")

            def on_progress(done, total):
                bar.progress(done / total, text=f"Section {done} of {total}")

            try:
                new = cardlib.generate_for_source(
                    active,
                    max_chunks=5 if quick else None,
                    per_chunk=per,
                    progress=on_progress,
                )
            except Exception as e:
                bar.empty()
                st.error(friendly_error(e))
                return
            bar.empty()
            if not new:
                st.warning("No cards were created. Please try again.")
                return
            db.replace_cards(active, new)
            st.session_state.pop("review", None)
            st.session_state.study = {}
            st.session_state["notice"] = f"Created {len(new)} flashcards"
            st.rerun()
        if rows and st.button("Delete this deck", key="fc_delete"):
            db.delete_cards(active)
            st.session_state.pop("review", None)
            st.session_state.study = {}
            st.rerun()

    if not rows:
        st.info("No flashcards yet. Open 'Create flashcards' above to make some.")
        return

    due_n = db.due_count(active)
    # The chosen mode is stored separately and the labels never change, so
    # rating a card can't reset the mode.
    current = st.session_state.get("fc_mode_value", "review")
    if current not in ("review", "free"):
        current = "review"
    st.radio(
        "Study mode",
        ["review", "free"],
        index=["review", "free"].index(current),
        format_func=lambda m: "Review due" if m == "review" else "Free study",
        horizontal=True,
        key="fc_mode_widget",
        label_visibility="collapsed",
        on_change=lambda: st.session_state.update(
            fc_mode_value=st.session_state["fc_mode_widget"]
        ),
    )
    mode = st.session_state.get("fc_mode_value", "review")
    if mode == "review":
        st.caption(
            f"{due_n} card(s) due today" if due_n else "No cards due right now"
        )
    if mode == "review":
        render_review(active)
    else:
        render_free_study(active, rows)


def render_review(active):
    """Spaced repetition: cards come back at growing intervals."""
    r = st.session_state.setdefault("review", {})
    due = db.get_due_cards(active)
    if r.get("source") != active or r.get("day") != date.today().isoformat():
        r.clear()
        r.update(
            source=active,
            day=date.today().isoformat(),
            queue=[c["id"] for c in due],
            done=0,
            counts={0: 0, 1: 0, 2: 0, 3: 0},
        )
    # Cards that became due since the session started (rare) are not added mid-way.
    queue = r["queue"]

    if not queue:
        total = r["done"]
        if total:
            st.success(f"Session complete. You reviewed {total} card(s). 🎉")
            c = r["counts"]
            st.caption(
                f"Again {c[0]} · Hard {c[1]} · Good {c[2]} · Easy {c[3]}"
            )
        else:
            st.success("Nothing is due right now. You're all caught up! 🎉")
        nxt = db.next_due_date(active)
        if nxt:
            st.info(f"Next card is due on **{nxt}**.")
        st.caption(
            "Spaced repetition shows each card again just before you'd forget it. "
            "Want extra practice? Switch to 'Free study' above."
        )
        return

    card = next(
        (c for c in db.get_cards(active) if c["id"] == queue[0]), None
    )
    if card is None:
        queue.pop(0)
        st.rerun()

    total_session = r["done"] + len(queue)
    st.progress(r["done"] / total_session, text=f"{len(queue)} card(s) left in this session")
    show_html(card_html(card["question"], card["answer"], card["topic"]), 330)
    st.caption("Think of the answer first, flip the card to check, then rate how well you knew it.")

    days = srs.preview(card["ease"], card["interval"], card["reps"])
    cols = st.columns(4)
    styles = {0: "secondary", 1: "secondary", 2: "primary", 3: "secondary"}
    for rating, col in zip((0, 1, 2, 3), cols):
        label = f"{srs.LABELS[rating]} · {srs.pretty_days(days[rating])}"
        if col.button(label, key=f"srs_{rating}", type=styles[rating]):
            db.review_card(card["id"], rating)
            queue.pop(0)
            r["done"] += 1
            r["counts"][rating] += 1
            if rating == srs.AGAIN:
                queue.append(card["id"])  # see it again before the session ends
            st.rerun()


def render_free_study(active, rows):
    """Browse cards in any order. This does not change the review schedule."""
    topics = sorted({r["topic"] for r in rows})
    f1, f2 = st.columns([3, 1])
    topic = f1.selectbox("Topic", ["All topics"] + topics, key="fc_topic")
    shuffle = f2.toggle("Shuffle", value=False, key="fc_shuffle")

    deck = [r for r in rows if topic == "All topics" or r["topic"] == topic]
    by_id = {r["id"]: r for r in deck}

    s = st.session_state.study
    key = f"{active}|{topic}|{shuffle}|{len(deck)}"
    if s.get("key") != key:
        order = [r["id"] for r in deck]
        if shuffle:
            random.shuffle(order)
        s.clear()
        s.update(key=key, order=order, pos=0, known=set(), missed=set())

    n = len(s["order"])
    if n == 0:
        st.info("No cards in this topic.")
        return

    if s["pos"] >= n:
        st.success(f"Deck finished! You knew {len(s['known'])} of {n} cards. 🎉")
        b1, b2 = st.columns(2)
        if s["missed"] and b1.button(
            f"Review {len(s['missed'])} missed cards", type="primary", key="fc_review"
        ):
            s["order"] = [i for i in s["order"] if i in s["missed"]]
            s.update(pos=0, known=set(), missed=set())
            st.rerun()
        if b2.button("Start over", key="fc_restart"):
            s["order"] = [r["id"] for r in deck]
            if shuffle:
                random.shuffle(s["order"])
            s.update(pos=0, known=set(), missed=set())
            st.rerun()
    else:
        card = by_id[s["order"][s["pos"]]]
        st.progress(s["pos"] / n, text=f"Card {s['pos'] + 1} / {n}")
        show_html(card_html(card["question"], card["answer"], card["topic"]), 330)
        b1, b2, b3, b4 = st.columns([1, 2, 2, 1])
        if b1.button("←", key="fc_prev", disabled=s["pos"] == 0):
            s["pos"] -= 1
            st.rerun()
        if b2.button(f"✗ Don't know  ({len(s['missed'])})", key="fc_miss"):
            db.record_review(card["id"], False)
            s["missed"].add(card["id"])
            s["known"].discard(card["id"])
            s["pos"] += 1
            st.rerun()
        if b3.button(f"✓ Know  ({len(s['known'])})", type="primary", key="fc_know"):
            db.record_review(card["id"], True)
            s["known"].add(card["id"])
            s["missed"].discard(card["id"])
            s["pos"] += 1
            st.rerun()
        if b4.button("→", key="fc_next"):
            s["pos"] += 1
            st.rerun()

    st.divider()
    h1, h2 = st.columns([3, 1])
    h1.subheader(f"All flashcards ({len(deck)})")
    show = h2.toggle("Show answers", value=True, key="fc_show")
    df = pd.DataFrame(
        {
            "Question": [r["question"] for r in deck],
            "Answer": [r["answer"] if show else "••••••" for r in deck],
            "Topic": [r["topic"] for r in deck],
            "Knew": [r["known"] or 0 for r in deck],
            "Missed": [r["missed"] or 0 for r in deck],
        }
    )
    st.dataframe(df, hide_index=True)


# ------------------------------------------------------------------ test
def finish_test(active, t):
    result = quizlib.grade(t["questions"], t["answers"])
    details = [
        {
            "question": t["questions"][r["index"]]["question"],
            "status": r["status"],
            "topic": t["questions"][r["index"]]["topic"],
        }
        for r in result["results"]
    ]
    db.save_attempt(active, result["total"], result["correct"], details)
    t["done"] = True
    t["result"] = result


def render_test(active):
    t = st.session_state.test
    if t and t["source"] != active:
        st.session_state.test = t = None

    if t is None:
        st.subheader("Take a test")
        st.write(
            "Multiple-choice questions made from your notes. "
            "You'll get a score and an explanation for every answer."
        )
        n = st.select_slider(
            "Number of questions", options=[5, 10, 15, 20], value=10, key="test_n"
        )
        if st.button("Start test", type="primary", key="test_start"):
            bar = st.progress(0.0, text="Writing your questions...")

            def on_progress(done, total):
                bar.progress(done / total, text=f"Writing questions ({done}/{total})")

            try:
                qs = quizlib.generate_quiz(active, n=n, progress=on_progress)
            except Exception as e:
                bar.empty()
                st.error(friendly_error(e))
                return
            bar.empty()
            if len(qs) < 3:
                st.error(
                    "Couldn't write enough good questions. Try again, "
                    "or add more notes."
                )
                return
            st.session_state.test = {
                "id": int(time.time() * 1000),
                "source": active,
                "questions": qs,
                "answers": {},
                "pos": 0,
                "done": False,
                "result": None,
            }
            st.rerun()

        attempts = db.list_attempts(active)
        if attempts:
            st.subheader("Past results")
            st.dataframe(
                pd.DataFrame(
                    {
                        "Date": [a["taken_at"].replace("T", " ") for a in attempts],
                        "Score": [f"{a['correct']} / {a['total']}" for a in attempts],
                        "Percent": [
                            f"{round(100 * a['correct'] / a['total'])}%"
                            for a in attempts
                        ],
                    }
                ),
                hide_index=True,
            )
        return

    qs = t["questions"]
    n = len(qs)

    if not t["done"]:
        pos = t["pos"]
        q = qs[pos]
        answered = sum(1 for v in t["answers"].values() if v in (0, 1, 2, 3))
        st.progress((pos + 1) / n, text=f"Question {pos + 1} of {n}")
        st.markdown(f"### {q['question']}")

        saved = t["answers"].get(pos)
        choice = st.radio(
            "Choose an answer",
            [0, 1, 2, 3],
            index=saved if saved in (0, 1, 2, 3) else None,
            format_func=lambda i: f"{LETTERS[i]}.  {q['options'][i]}",
            key=f"t{t['id']}_{pos}",
            label_visibility="collapsed",
        )
        if choice is not None:
            t["answers"][pos] = choice
            answered = sum(1 for v in t["answers"].values() if v in (0, 1, 2, 3))
        st.caption(f"{answered} of {n} answered")

        last = pos == n - 1
        b1, b2, b3 = st.columns(3)
        if b1.button("← Previous", disabled=pos == 0, key="t_prev"):
            t["pos"] -= 1
            st.rerun()
        if b2.button("I don't know", key="t_skip"):
            t["answers"][pos] = -1
            if not last:
                t["pos"] += 1
            st.rerun()
        if b3.button("Submit test" if last else "Next →", type="primary", key="t_next"):
            if last:
                finish_test(active, t)
            else:
                t["pos"] += 1
            st.rerun()
        if last and answered < n:
            st.warning(f"You still have {n - answered} unanswered question(s).")
        return

    r = t["result"]
    pct = round(100 * r["correct"] / r["total"])
    wrong = sum(1 for x in r["results"] if x["status"] == "wrong")
    skipped = sum(1 for x in r["results"] if x["status"] == "skipped")

    st.subheader("Your score")
    m1, m2, m3 = st.columns(3)
    m1.metric("Score", f"{r['correct']} / {r['total']}")
    m2.metric("Percent", f"{pct}%")
    m3.metric("Wrong / skipped", f"{wrong} / {skipped}")
    st.progress(pct / 100)
    if pct >= 80:
        st.success("Excellent! You know this material well.")
    elif pct >= 50:
        st.info("Good effort. Review the questions you missed below.")
    else:
        st.warning("Keep practising. Try the flashcards, then retake the test.")

    topic_rows = [
        {
            "Topic": name,
            "Correct": f"{v['correct']} / {v['total']}",
            "Percent": f"{round(100 * v['correct'] / v['total'])}%",
        }
        for name, v in sorted(r["per_topic"].items())
    ]
    st.markdown("**By topic**")
    st.dataframe(pd.DataFrame(topic_rows), hide_index=True)
    weak = [
        name for name, v in r["per_topic"].items() if v["correct"] / v["total"] < 0.6
    ]
    if weak:
        st.caption("Worth revising: " + ", ".join(sorted(weak)))

    st.subheader("Review your answers")
    icons = {"correct": "✅", "wrong": "❌", "skipped": "➖"}
    for res in r["results"]:
        q = qs[res["index"]]
        with st.expander(f"{icons[res['status']]}  Q{res['index'] + 1}. {q['question']}"):
            chosen = res["chosen"]
            if chosen in (0, 1, 2, 3):
                st.write(f"**Your answer:** {LETTERS[chosen]}. {q['options'][chosen]}")
            else:
                st.write("**Your answer:** (skipped)")
            st.write(f"**Correct answer:** {LETTERS[q['answer']]}. {q['options'][q['answer']]}")
            if q["explanation"]:
                st.write(f"**Why:** {q['explanation']}")

    b1, b2 = st.columns(2)
    if b1.button("Retake this test", key="t_retake"):
        t.update(id=int(time.time() * 1000), answers={}, pos=0, done=False, result=None)
        st.rerun()
    if b2.button("New test", type="primary", key="t_new"):
        st.session_state.test = None
        st.rerun()


# ------------------------------------------------------------------ progress
def render_progress(active):
    scope = st.radio(
        "Show progress for",
        ["file", "all"],
        format_func=lambda m: f"This file ({active})" if m == "file" else "All my notes",
        horizontal=True,
        key="prog_scope",
        label_visibility="collapsed",
    )
    src = active if scope == "file" else None

    due = db.due_count(src)
    total_cards = (
        db.count_cards(active)
        if src
        else sum(db.count_cards(n) for n in sources)
    )
    history = stats.score_history(src)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Due today", due)
    m2.metric("Reviewed today", stats.reviews_today(src))
    m3.metric("Study streak", f"{stats.streak(src)} day(s)")
    m4.metric(
        "Latest test",
        f"{history[-1][1]}%" if history else "–",
        delta=(
            f"{history[-1][1] - history[-2][1]:+d} pts" if len(history) > 1 else None
        ),
    )
    if due:
        st.info(f"You have {due} card(s) to review. Open Flashcards → Review due.")
    elif total_cards:
        st.success("You're all caught up on flashcards for today. 🎉")

    if not total_cards and not history:
        st.info(
            "Nothing to show yet. Make flashcards or take a test, "
            "and your progress will appear here."
        )
        return

    st.subheader("Reviews in the last 14 days")
    days = stats.reviews_by_day(src, days=14)
    if sum(n for _, n in days):
        df = pd.DataFrame(
            {"Reviews": [n for _, n in days]},
            index=[d.strftime("%d %b") for d, _ in days],
        )
        show_chart(themed_bar(df.reset_index(names="Day"), "Day", "Reviews"))
    else:
        st.caption("No reviews yet. Rate some cards in Flashcards → Review due.")

    left, right = st.columns(2)
    with left:
        st.subheader("How well you remember")
        rb = stats.rating_breakdown(src, days=30)
        n = sum(rb.values())
        if n:
            ok = round(100 * (rb[1] + rb[2] + rb[3]) / n)
            st.metric("Recalled (last 30 days)", f"{ok}%")
            st.dataframe(
                pd.DataFrame(
                    {
                        "Rating": [srs.LABELS[i] for i in range(4)],
                        "Times": [rb[i] for i in range(4)],
                    }
                ),
                hide_index=True,
            )
        else:
            st.caption("Appears after your first reviews.")
    with right:
        st.subheader("Your cards")
        stages = stats.card_stages(src)
        if sum(stages.values()):
            show_chart(
                themed_bar(
                    pd.DataFrame({"Stage": list(stages), "Cards": list(stages.values())}),
                    "Stage",
                    "Cards",
                    height=220,
                )
            )
            st.caption(
                "New = not reviewed yet · Learning = seen, short gaps · "
                "Mature = you recall it after 3+ weeks"
            )
        else:
            st.caption("No flashcards yet.")

    st.subheader("Test scores")
    if history:
        show_chart(
            themed_line(
                pd.DataFrame(
                    {
                        "Test": list(range(1, len(history) + 1)),
                        "Score (%)": [h[1] for h in history],
                    }
                ),
                "Test",
                "Score (%)",
            )
        )
        st.caption("Each point is one test, oldest on the left.")
    else:
        st.caption("No tests taken yet. Try the Test view.")

    st.subheader("Topics to revise")
    topics = stats.topic_performance(src)
    if topics:
        weak = [t for t in topics if t["accuracy"] < 70][:5]
        if weak:
            st.warning(
                "Weakest topics: " + ", ".join(f"{t['topic']} ({t['accuracy']}%)" for t in weak)
            )
        else:
            st.success("No weak topics. Nice work!")
        st.dataframe(
            pd.DataFrame(
                {
                    "Topic": [t["topic"] for t in topics],
                    "Accuracy": [f"{t['accuracy']}%" for t in topics],
                    "Card reviews": [t["reviews"] for t in topics],
                    "Test questions": [t["test_questions"] for t in topics],
                }
            ),
            hide_index=True,
        )
        st.caption("Accuracy combines flashcard reviews (Again counts as a miss) and test answers.")
    else:
        st.caption("Shows up after a few reviews or a test.")


# ------------------------------------------------------------------ main page
if not sources:
    st.markdown(
        """
<div class="hero">
  <div class="pill">📚 AI Study Buddy</div>
  <h1>Turn your notes into<br>a study system</h1>
  <p>Upload your notes and get answers with sources, exam-ready summaries,
  flashcards that come back at the right time, and tests that show what to revise.</p>
</div>
<div class="feature-grid">
  <div class="feature"><div class="ico">💬</div><b>Chat with your notes</b>
    <span>Ask anything and get answers from your own material, with the sections they came from.</span></div>
  <div class="feature"><div class="ico">📝</div><b>Smart summaries</b>
    <span>An exam-ready summary of the whole file, organised under headings.</span></div>
  <div class="feature"><div class="ico">🃏</div><b>Spaced flashcards</b>
    <span>Flip cards that return just before you would forget them.</span></div>
  <div class="feature"><div class="ico">✅</div><b>Graded tests</b>
    <span>Multiple-choice tests with explanations and a score for every topic.</span></div>
  <div class="feature"><div class="ico">📊</div><b>Progress tracking</b>
    <span>Streaks, review history and your weakest topics at a glance.</span></div>
</div>
<div class="steps">
  <div class="step"><i>1</i>Add notes in the sidebar</div>
  <div class="step"><i>2</i>Chat, summarise or make flashcards</div>
  <div class="step"><i>3</i>Take a test and track progress</div>
</div>
<p style="text-align:center;color:#8a8fa8;margin-top:1.4rem;font-size:.9rem">
Works with PDF, Word, PowerPoint, text files and photos of notes.</p>
""",
        unsafe_allow_html=True,
    )
    st.stop()

# Streamlit only pins the chat box to the bottom of the page when it sits at the
# top level, not inside st.tabs. So we use a tab-like selector instead of st.tabs.
st.markdown(
    f'<div class="file-chip">📄 {html.escape(active)}</div>', unsafe_allow_html=True
)
VIEWS = ["💬 Chat", "📝 Summary", "🃏 Flashcards", "✅ Test", "📊 Progress"]
if hasattr(st, "segmented_control"):
    view = st.segmented_control(
        "View", VIEWS, default=VIEWS[0], key="view", label_visibility="collapsed"
    )
else:
    view = st.radio(
        "View", VIEWS, horizontal=True, key="view", label_visibility="collapsed"
    )
view = view or VIEWS[0]
st.divider()

if view == VIEWS[0]:
    render_chat(active)
elif view == VIEWS[1]:
    render_summary(active)
elif view == VIEWS[2]:
    render_flashcards(active)
elif view == VIEWS[3]:
    render_test(active)
else:
    render_progress(active)
