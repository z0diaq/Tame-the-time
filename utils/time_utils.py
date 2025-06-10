from datetime import datetime, time
from typing import Dict, Optional

def format_time(t: time) -> str:
    """Format a time object to HH:MM string."""
    return t.strftime("%H:%M")

def get_current_activity(schedule: list[Dict], current_time: datetime) -> Optional[Dict]:
    """Determine the current activity based on the current time."""
    if current_time.weekday() >= 5:
        return None
    
    time_now = current_time.time()
    for activity in schedule:
        start_hour, start_minute = map(int, activity["start_time"].split(":"))
        end_hour, end_minute = map(int, activity["end_time"].split(":"))
        
        start_time = time(start_hour, start_minute)
        end_time = time(end_hour, end_minute)
        
        if start_time <= time_now < end_time:
            activity_with_time = activity.copy()
            activity_with_time["start_time"] = start_time
            activity_with_time["end_time"] = end_time
            return activity_with_time
    
    return None
