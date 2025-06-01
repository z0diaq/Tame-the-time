import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import yaml

def get_day_config_path() -> str:
    """Determine the configuration file path based on the current day."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    current_day = datetime.now().weekday()
    
    if 0 <= current_day <= 4:
        day_config = f"{day_names[current_day]}_settings.yaml"
        if os.path.exists(day_config):
            return day_config
    
    return "default_settings.yaml"

def load_schedule(config_path: Optional[str] = None) -> List[Dict]:
    """Load and validate the schedule from a YAML file."""
    config_path = config_path or get_day_config_path()
    
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
        
        return schedule
    
    except FileNotFoundError:
        print(f"Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML configuration: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
