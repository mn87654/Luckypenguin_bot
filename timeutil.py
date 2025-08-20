from __future__ import annotations
from datetime import datetime
from zoneinfo import ZoneInfo
from settings import settings

def now_tz() -> datetime:
    try:
        tz = ZoneInfo(settings.TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz)

def today_key() -> str:
    return now_tz().strftime("%Y-%m-%d")
