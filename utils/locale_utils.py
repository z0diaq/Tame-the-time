from typing import List
from utils.translator import get_value

# Default English fallback (Monday-first)
_DEFAULT_WEEKDAYS: List[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

_DEFAULT_WEEKDAYS_SHORT: List[str] = [
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
]

def get_weekdays() -> List[str]:
    """Return localized weekday names (Monday-first), falling back to English."""
    val = get_value("datetime.weekdays")
    if isinstance(val, list) and len(val) == 7 and all(isinstance(x, str) for x in val):
        return val
    return _DEFAULT_WEEKDAYS


def get_weekdays_short() -> List[str]:
    """Return localized short weekday names (Mon-first), falling back to English."""
    val = get_value("datetime.weekdays_short")
    if isinstance(val, list) and len(val) == 7 and all(isinstance(x, str) for x in val):
        return val
    return _DEFAULT_WEEKDAYS_SHORT


def get_weekday_name(index: int) -> str:
    """Get localized weekday name by Python's weekday index (0=Monday..6=Sunday)."""
    days = get_weekdays()
    if 0 <= index < 7:
        return days[index]
    # Fallback: clamp
    return days[0]
