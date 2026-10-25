import json
import sqlite3
from datetime import date, datetime

DB_PATH = "study_buddy.db"

CARD_EXTRA_COLUMNS = {
    "known": "INTEGER DEFAULT 0",
    "missed": "INTEGER DEFAULT 0",
    "last_reviewed": "TEXT",
}


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            chunk_index INTEGER,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            topic TEXT,
            ease REAL DEFAULT 2.5,
            interval INTEGER DEFAULT 0,
            reps INTEGER DEFAULT 0,
            due_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing = {r["name"] for r in conn.execute("PRAGMA table_info(cards)")}
    for col, ddl in CARD_EXTRA_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE cards ADD COLUMN {col} {ddl}")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            source TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            taken_at TEXT NOT NULL,
            total INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            details TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS review_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER,
            source TEXT NOT NULL,
            topic TEXT,
            rating INTEGER NOT NULL,
            reviewed_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ---------- flashcards ----------

def replace_cards(source, cards):
    conn = _connect()
    conn.execute("DELETE FROM cards WHERE source = ?", (source,))
    today = date.today().isoformat()
    conn.executemany(
        "INSERT INTO cards (source, chunk_index, question, answer, topic, due_date) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        [
            (source, c["chunk_index"], c["question"], c["answer"], c["topic"], today)
            for c in cards
        ],
    )
    conn.commit()
    conn.close()


def get_cards(source):
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM cards WHERE source = ? ORDER BY chunk_index, id", (source,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def count_cards(source):
    conn = _connect()
    n = conn.execute(
        "SELECT COUNT(*) FROM cards WHERE source = ?", (source,)
    ).fetchone()[0]
    conn.close()
    return n


def sources_with_cards():
    conn = _connect()
    rows = conn.execute("SELECT DISTINCT source FROM cards ORDER BY source").fetchall()
    conn.close()
    return [r[0] for r in rows]


def record_review(card_id, knew):
    conn = _connect()
    col = "known" if knew else "missed"
    conn.execute(
        f"UPDATE cards SET {col} = {col} + 1, last_reviewed = ? WHERE id = ?",
        (datetime.now().isoformat(timespec="seconds"), card_id),
    )
    conn.commit()
    conn.close()


def review_card(card_id, rating):
    """Apply a spaced-repetition rating (0 Again, 1 Hard, 2 Good, 3 Easy)."""
    from core import srs

    conn = _connect()
    card = conn.execute("SELECT * FROM cards WHERE id = ?", (card_id,)).fetchone()
    if card is None:
        conn.close()
        return None
    ease, interval, reps, due = srs.schedule(
        card["ease"], card["interval"], card["reps"], rating
    )
    now = datetime.now().isoformat(timespec="seconds")
    col = "missed" if rating == srs.AGAIN else "known"
    conn.execute(
        f"UPDATE cards SET ease = ?, interval = ?, reps = ?, due_date = ?, "
        f"last_reviewed = ?, {col} = {col} + 1 WHERE id = ?",
        (ease, interval, reps, due, now, card_id),
    )
    conn.execute(
        "INSERT INTO review_log (card_id, source, topic, rating, reviewed_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (card_id, card["source"], card["topic"], rating, now),
    )
    conn.commit()
    conn.close()
    return {"interval": interval, "due_date": due}


def get_due_cards(source=None, today=None):
    today = today or date.today().isoformat()
    conn = _connect()
    if source is None:
        rows = conn.execute(
            "SELECT * FROM cards WHERE due_date <= ? ORDER BY due_date, id", (today,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM cards WHERE source = ? AND due_date <= ? "
            "ORDER BY due_date, id",
            (source, today),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def due_count(source=None):
    return len(get_due_cards(source))


def next_due_date(source):
    conn = _connect()
    row = conn.execute(
        "SELECT MIN(due_date) FROM cards WHERE source = ?", (source,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


def delete_cards(source):
    conn = _connect()
    conn.execute("DELETE FROM cards WHERE source = ?", (source,))
    conn.commit()
    conn.close()


def clear_cards():
    conn = _connect()
    conn.execute("DELETE FROM cards")
    conn.commit()
    conn.close()


# ---------- summaries ----------

def save_summary(source, content):
    conn = _connect()
    conn.execute(
        "INSERT INTO summaries (source, content, created_at) VALUES (?, ?, ?) "
        "ON CONFLICT(source) DO UPDATE SET content = excluded.content, "
        "created_at = excluded.created_at",
        (source, content, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def get_summary(source):
    conn = _connect()
    row = conn.execute(
        "SELECT content FROM summaries WHERE source = ?", (source,)
    ).fetchone()
    conn.close()
    return row[0] if row else None


# ---------- tests ----------

def save_attempt(source, total, correct, details):
    conn = _connect()
    conn.execute(
        "INSERT INTO quiz_attempts (source, taken_at, total, correct, details) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            source,
            datetime.now().isoformat(timespec="seconds"),
            total,
            correct,
            json.dumps(details),
        ),
    )
    conn.commit()
    conn.close()


def list_attempts(source):
    conn = _connect()
    rows = conn.execute(
        "SELECT id, taken_at, total, correct FROM quiz_attempts "
        "WHERE source = ? ORDER BY id DESC",
        (source,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- cleanup ----------

def delete_source_data(source):
    conn = _connect()
    for table in ("cards", "summaries", "quiz_attempts", "review_log"):
        conn.execute(f"DELETE FROM {table} WHERE source = ?", (source,))
    conn.commit()
    conn.close()


def clear_all_data():
    conn = _connect()
    for table in ("cards", "summaries", "quiz_attempts", "review_log"):
        conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()
