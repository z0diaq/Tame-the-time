import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml
from utils.logging import log_error

def get_day_config_path(current_day) -> str:
    """Determine the configuration file path based on the current day."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if 0 <= current_day <= 6:
        day_config = f"{day_names[current_day]}_settings.yaml"
        if os.path.exists(day_config):
            return day_config
    
    return "default_settings.yaml"

def create_sample_schedule(now) -> Dict:
    """Create a default configuration to be used if no specific config is found."""
    # Create schedule with 3 sample activities
    # Each 30 minutes long
    # First that ended 10 minutes ago
    # Second that is currently ongoing
    # Third that starts in 20 minutes
    return [
        {
            "name": "Past Activity",
            "start_time": (now - timedelta(minutes=40)).strftime("%H:%M"),
            "end_time": (now - timedelta(minutes=10)).strftime("%H:%M"),
            "description": "This is a past activity."
        },
        {
            "name": "Current Activity",
            "start_time": (now - timedelta(minutes=10)).strftime("%H:%M"),
            "end_time": (now + timedelta(minutes=20)).strftime("%H:%M"),
            "description": "This is the current activity."
        },
        {
            "name": "Future Activity",
            "start_time": (now + timedelta(minutes=20)).strftime("%H:%M"),
            "end_time": (now + timedelta(minutes=50)).strftime("%H:%M"),
            "description": "This is a future activity."
        }
    ]

def load_schedule(config_path: Optional[str] = None, now_provider=None) -> List[Dict]:
    """Load and validate the schedule from a YAML file."""
    is_default_config = config_path is None or config_path == "default_settings.yaml"
    config_path = config_path or get_day_config_path(current_day=now_provider().date().weekday())
    
    try:
        with open(config_path, 'r') as file:
            schedule = yaml.safe_load(file)
        
        if not isinstance(schedule, list):
            raise ValueError("Schedule must be a list of activities")
        
        for activity in schedule:
            if not all(key in activity for key in ["name", "start_time", "end_time", "description"]):
                raise ValueError(f"Invalid activity format in {config_path}")
            
            # Validate time format
            for time_key in ["start_time", "end_time"]:
                try:
                    datetime.strptime(activity[time_key], "%H:%M")
                except ValueError:
                    raise ValueError(f"Invalid time format in {activity['name']} for {time_key}")
        
        return schedule, config_path
    
    except FileNotFoundError:
        if is_default_config:
            return create_sample_schedule(now_provider().time()), config_path
        log_error(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        log_error(f"Error parsing YAML configuration: {e}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Configuration error: {e}")
        sys.exit(1)
