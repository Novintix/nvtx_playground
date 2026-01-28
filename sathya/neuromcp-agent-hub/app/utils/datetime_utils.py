from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import re

DEFAULT_TZ = "Asia/Kolkata"

def now_in_tz(tz: str = DEFAULT_TZ) -> datetime:
    return datetime.now(ZoneInfo(tz))

def parse_time_4pm(text: str) -> tuple[int, int] | None:
    # supports "4pm", "4 pm", "16:00"
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b", text.lower())
    if not m:
        return None
    hh = int(m.group(1))
    mm = int(m.group(2) or 0)
    ap = m.group(3)
    if ap == "pm" and hh < 12:
        hh += 12
    if ap == "am" and hh == 12:
        hh = 0
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return hh, mm
    return None

def make_iso_for_relative_day(day_word: str, time_hhmm: tuple[int,int], tz: str = DEFAULT_TZ) -> str:
    base = now_in_tz(tz).replace(second=0, microsecond=0)
    if day_word == "tomorrow":
        base = base + timedelta(days=1)
    # set time
    hh, mm = time_hhmm
    base = base.replace(hour=hh, minute=mm)
    return base.isoformat()

def normalize_relative_times(plan: dict, tz: str = DEFAULT_TZ) -> dict:
    """
    If the plan contains start_time/end_time but with old dates,
    and the user intent includes 'tomorrow', rewrite to tomorrow in tz.
    Only touches calendar.create_event inputs.
    """
    goal = (plan.get("goal") or "").lower()
    steps = plan.get("steps") or []
    if "tomorrow" not in goal:
        return plan

    t = parse_time_4pm(goal) or (16, 0)

    for s in steps:
        if s.get("tool") == "calendar.create_event":
            inp = s.get("input", {})
            start = inp.get("start_time")
            end = inp.get("end_time")
            # rewrite to tomorrow using goal time if clearly relative
            inp["timezone"] = inp.get("timezone") or tz
            inp["start_time"] = make_iso_for_relative_day("tomorrow", t, inp["timezone"])
            # default +1 hour
            hh, mm = t
            inp["end_time"] = make_iso_for_relative_day("tomorrow", (min(hh+1,23), mm), inp["timezone"])
            s["input"] = inp
    plan["steps"] = steps
    return plan
