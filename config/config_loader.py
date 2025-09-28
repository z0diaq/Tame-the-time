import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
import yaml
from utils.logging import log_error
from utils.time_utils import TimeUtils
from utils.locale_utils import get_weekday_name

def get_day_config_path(current_day: int) -> str:
    """Determine the configuration file path based on the current day."""
    if 0 <= current_day <= 6:
        day_config = f"{get_weekday_name(current_day)}_settings.yaml"
        if os.path.exists(day_config):
            return day_config
    
    return "default_settings.yaml"


def create_sample_schedule(now: datetime) -> List[Dict[str, Any]]:
    """Create a default configuration to be used if no specific config is found."""
    # Create schedule with 3 sample activities
    # Each 30 minutes long
    # First that ended 10 minutes ago
    # Second that is currently ongoing
    # Third that starts in 20 minutes
    return [
        {
            "name": "Past Activity",
            "start_time": TimeUtils.normalize_time_format(now - timedelta(minutes=40)),
            "end_time": TimeUtils.normalize_time_format(now - timedelta(minutes=10)),
            "description": [ "This is a past activity." ],
            "tasks": [ "Activity 1 task" ]
        },
        {
            "name": "Current Activity",
            "start_time": TimeUtils.normalize_time_format(now - timedelta(minutes=10)),
            "end_time": TimeUtils.normalize_time_format(now + timedelta(minutes=20)),
            "description": [ "This is the current activity." ],
            "tasks": [ "Activity 2 task" ]
        },
        {
            "name": "Future Activity",
            "start_time": TimeUtils.normalize_time_format(now + timedelta(minutes=20)),
            "end_time": TimeUtils.normalize_time_format(now + timedelta(minutes=50)),
            "description": [ "This is a future activity." ],
            "tasks": [ "Activity 3 task" ]
        }
    ]

def validate_schedule(schedule: List[Dict[str, Any]]) -> bool:
    """Validate the schedule structure and time formats."""
    
    for activity in schedule:
        if not all(key in activity for key in ["name", "start_time", "end_time", "description"]):
            log_error(f"Invalid activity format: {activity}")
            return False
        
        # Validate time format using TimeUtils
        for time_key in ["start_time", "end_time"]:
            try:
                TimeUtils.parse_time_with_validation(activity[time_key])
            except ValueError as e:
                log_error(f"Invalid time format in {activity['name']} for {time_key}: {e}")
                return False
    
    return True

def load_schedule(config_path: Optional[str] = None, now_provider: Optional[Callable[[], datetime]] = None) -> Tuple[List[Dict[str, Any]], str]:
    """Load and validate the schedule from a YAML file."""
    is_default_config = config_path is None or config_path == "default_settings.yaml"
    config_path = config_path or get_day_config_path(current_day=now_provider().date().weekday())
    
    try:
        with open(config_path, 'r') as file:
            schedule = yaml.safe_load(file)
        
        if not validate_schedule(schedule):
            raise ValueError("Schedule must be a list of activities")
                
        return schedule, config_path
    
    except FileNotFoundError:
        if is_default_config:
            return create_sample_schedule(now_provider()), config_path
        log_error(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        log_error(f"Error parsing YAML configuration: {e}")
        sys.exit(1)
    except ValueError as e:
        log_error(f"Configuration error: {e}")
        sys.exit(1)
