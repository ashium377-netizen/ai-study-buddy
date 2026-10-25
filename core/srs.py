"""Spaced repetition scheduling (a simplified SM-2, like Anki).

Ratings: 0 = Again, 1 = Hard, 2 = Good, 3 = Easy.
"""
from datetime import date, timedelta

AGAIN, HARD, GOOD, EASY = 0, 1, 2, 3
LABELS = {AGAIN: "Again", HARD: "Hard", GOOD: "Good", EASY: "Easy"}
MIN_EASE = 1.3
MAX_INTERVAL = 365


def schedule(ease, interval, reps, rating, today=None):
    """Return (ease, interval_days, reps, due_date_iso) after one review."""
    today = today or date.today()
    ease = float(ease or 2.5)
    interval = int(interval or 0)
    reps = int(reps or 0)

    if rating == AGAIN:
        ease = max(MIN_EASE, ease - 0.2)
        reps = 0
        interval = 0  # due again today: shown again later in the same session
    elif rating == HARD:
        ease = max(MIN_EASE, ease - 0.15)
        interval = max(1, round(interval * 1.2)) if reps > 0 else 1
        reps += 1
    elif rating == GOOD:
        if reps == 0:
            interval = 1
        elif reps == 1:
            interval = 6
        else:
            interval = round(interval * ease)
        reps += 1
    else:  # EASY
        ease = ease + 0.15
        if reps == 0:
            interval = 4
        else:
            interval = round(max(interval, 1) * ease * 1.3)
        reps += 1

    interval = min(interval, MAX_INTERVAL)
    due = today + timedelta(days=interval)
    return round(ease, 2), interval, reps, due.isoformat()


def preview(ease, interval, reps):
    """Days until the next review for each rating (for the button labels)."""
    return {r: schedule(ease, interval, reps, r)[1] for r in (AGAIN, HARD, GOOD, EASY)}


def pretty_days(days):
    if days <= 0:
        return "<10 min"
    if days == 1:
        return "1 day"
    if days < 30:
        return f"{days} days"
    if days < 365:
        return f"{round(days / 30)} mo"
    return "1 yr"
