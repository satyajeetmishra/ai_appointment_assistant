# services/normalization.py (minimal validator)
import re
from typing import Tuple, Optional, Dict

LOCAL_TZ = "Asia/Kolkata"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")  # 00:00 to 23:59

def _is_valid_date_iso(s: Optional[str]) -> bool:
    return bool(s) and bool(_DATE_RE.match(s))

def _is_valid_time_24h(s: Optional[str]) -> bool:
    return bool(s) and bool(_TIME_RE.match(s))

def normalize(date_phrase: Optional[str], time_phrase: Optional[str]) -> Tuple[Dict, float]:
    """
    Minimal normalization layer:
    - Accept only ISO date (YYYY-MM-DD) and 24h time (HH:MM).
    - If invalid, set to None.
    - tz is always Asia/Kolkata.
    """
    date_out = date_phrase if _is_valid_date_iso(date_phrase) else None
    time_out = time_phrase if _is_valid_time_24h(time_phrase) else None

    # Simple confidence: both valid -> 0.95, one valid -> 0.75, none -> 0.2
    if date_out and time_out:
        conf = 0.95
    elif date_out or time_out:
        conf = 0.75
    else:
        conf = 0.2

    return {"date": date_out, "time": time_out, "tz": LOCAL_TZ}, conf
