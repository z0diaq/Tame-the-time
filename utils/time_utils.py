from datetime import datetime, time
from typing import Dict, List, Optional, Any

def format_time(t: time) -> str:
    """Format a time object to HH:MM string."""
    return t.strftime("%H:%M")

def get_current_activity(schedule: List[Dict[str, Any]], current_time: datetime) -> Optional[Dict[str, Any]]:
    """Determine the current activity based on the current time."""

    ''' Weekend handling
    if current_time.weekday() >= 5:
        return None
    '''
    
    time_now = current_time.time()
    for activity in schedule:
        start_hour, start_minute = map(int, activity["start_time"].split(":"))
        end_hour, end_minute = map(int, activity["end_time"].split(":"))
        
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)
        
        if start_time <= time_now < end_time:
            # Return activity with original string time format preserved
            return activity.copy()
    
    return None

def round_to_nearest_5_minutes(minutes: int) -> int:
    """Round minutes to the nearest 5 minutes."""
    return 5 * round(minutes / 5)

def parse_time_str(tstr):
    # Accepts '8:00', '08:00', '8:00:00', '08:00:00' and returns a time object
    parts = tstr.split(":")
    if len(parts) == 2:
        # e.g. '8:00' or '08:00'
        hour = int(parts[0])
        minute = int(parts[1])
        return time(hour, minute)
    elif len(parts) == 3:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2])
        return time(hour, minute, second)
    else:
        raise ValueError(f"Invalid time string: {tstr}")
