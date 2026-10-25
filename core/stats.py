"""Numbers for the Progress dashboard. Everything is read from the local database."""
import json
from collections import defaultdict
from datetime import date, datetime, timedelta

from core import db


def _where(source):
    return ("WHERE source = ?", (source,)) if source else ("", ())


def _day(ts):
    return datetime.fromisoformat(ts).date()


def reviews_by_day(source=None, days=14, today=None):
    """[(date, count)] for the last `days` days, oldest first, including zeros."""
    today = today or date.today()
    clause, args = _where(source)
    conn = db._connect()
    rows = conn.execute(
        f"SELECT reviewed_at FROM review_log {clause}", args
    ).fetchall()
    conn.close()
    counts = defaultdict(int)
    for r in rows:
        counts[_day(r[0])] += 1
    return [
        (today - timedelta(days=i), counts.get(today - timedelta(days=i), 0))
        for i in range(days - 1, -1, -1)
    ]


def study_days(source=None):
    """Set of dates on which the student reviewed a card or finished a test."""
    clause, args = _where(source)
    conn = db._connect()
    days = {
        _day(r[0])
        for r in conn.execute(f"SELECT reviewed_at FROM review_log {clause}", args)
    }
    days |= {
        _day(r[0])
        for r in conn.execute(f"SELECT taken_at FROM quiz_attempts {clause}", args)
    }
    conn.close()
    return days


def streak(source=None, today=None):
    """Consecutive study days. Today not being studied yet doesn't break it."""
    today = today or date.today()
    days = study_days(source)
    day = today if today in days else today - timedelta(days=1)
    n = 0
    while day in days:
        n += 1
        day -= timedelta(days=1)
    return n


def reviews_today(source=None, today=None):
    today = today or date.today()
    return dict(reviews_by_day(source, days=1, today=today)).get(today, 0)


def rating_breakdown(source=None, days=30, today=None):
    """{rating: count} over the last `days` days."""
    today = today or date.today()
    since = (today - timedelta(days=days - 1)).isoformat()
    clause, args = _where(source)
    clause = (clause + " AND" if clause else "WHERE") + " reviewed_at >= ?"
    conn = db._connect()
    rows = conn.execute(
        f"SELECT rating, COUNT(*) FROM review_log {clause} GROUP BY rating",
        args + (since,),
    ).fetchall()
    conn.close()
    out = {0: 0, 1: 0, 2: 0, 3: 0}
    out.update({r[0]: r[1] for r in rows})
    return out


def card_stages(source=None):
    """New / learning / mature card counts."""
    clause, args = _where(source)
    conn = db._connect()
    rows = conn.execute(
        f"SELECT reps, interval FROM cards {clause}", args
    ).fetchall()
    conn.close()
    out = {"New": 0, "Learning": 0, "Mature": 0}
    for reps, interval in rows:
        if not reps:
            out["New"] += 1
        elif (interval or 0) >= 21:
            out["Mature"] += 1
        else:
            out["Learning"] += 1
    return out


def score_history(source=None):
    """[(taken_at, percent, correct, total, source)] oldest first."""
    clause, args = _where(source)
    conn = db._connect()
    rows = conn.execute(
        f"SELECT taken_at, correct, total, source FROM quiz_attempts {clause} "
        "ORDER BY id",
        args,
    ).fetchall()
    conn.close()
    return [
        (r[0], round(100 * r[1] / r[2]) if r[2] else 0, r[1], r[2], r[3])
        for r in rows
    ]


def topic_performance(source=None, min_items=3):
    """Per topic accuracy from flashcard reviews and tests, weakest first.

    Returns [{"topic", "accuracy", "reviews", "test_questions"}], where accuracy is
    the share of answers that were right (a review rated Again counts as wrong).
    """
    clause, args = _where(source)
    conn = db._connect()
    reviews = conn.execute(
        f"SELECT topic, rating FROM review_log {clause}", args
    ).fetchall()
    attempts = conn.execute(
        f"SELECT details FROM quiz_attempts {clause}", args
    ).fetchall()
    conn.close()

    right, total = defaultdict(int), defaultdict(int)
    rev_n, test_n = defaultdict(int), defaultdict(int)
    for topic, rating in reviews:
        key = (topic or "General").strip().title()
        total[key] += 1
        rev_n[key] += 1
        right[key] += rating != 0
    for (details,) in attempts:
        try:
            items = json.loads(details or "[]")
        except ValueError:
            continue
        for it in items:
            key = (it.get("topic") or "General").strip().title()
            total[key] += 1
            test_n[key] += 1
            right[key] += it.get("status") == "correct"

    out = [
        {
            "topic": t,
            "accuracy": round(100 * right[t] / total[t]),
            "reviews": rev_n[t],
            "test_questions": test_n[t],
        }
        for t in total
        if total[t] >= min_items
    ]
    return sorted(out, key=lambda x: (x["accuracy"], x["topic"]))
