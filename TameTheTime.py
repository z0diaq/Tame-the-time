import sys
import os
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from utils.logging import log_startup, log_info, log_error
import ui.app
from config.config_loader import load_schedule
import utils.config
from constants import AppConstants, ValidationConstants
from models.time_manager import TimeManager

# Global time manager instance
time_manager: Optional[TimeManager] = None


def check_no_notification_parameter() -> None:
    """Check and set notification parameter from command line arguments."""
    if AppConstants.ARG_NO_NOTIFICATION in sys.argv:
        log_info("Notifications are disabled.")
        utils.config.allow_notification = False
    else:
        log_info("Notifications are enabled.")

def check_time_parameter() -> None:
    """Check and set simulation start time from command line arguments."""
    global time_manager
    if AppConstants.ARG_TIME in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_TIME)
        if idx + 1 < len(sys.argv):
            try:
                start_time = datetime.fromisoformat(sys.argv[idx + 1])
                if time_manager:
                    time_manager.set_simulation_start_time(start_time)
            except ValueError:
                log_error(f"Invalid date format: {sys.argv[idx + 1]}. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)

def check_timelapse_speed_parameter() -> None:
    """Check and set timelapse speed from command line arguments."""
    global time_manager
    if AppConstants.ARG_TIMELAPSE_SPEED in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_TIMELAPSE_SPEED)
        if idx + 1 < len(sys.argv):
            try:
                val = float(sys.argv[idx + 1])
                if ValidationConstants.MIN_TIMELAPSE_SPEED < val <= ValidationConstants.MAX_TIMELAPSE_SPEED:
                    if time_manager:
                        time_manager.set_timelapse_speed(val)
                else:
                    log_error(f"Invalid timelapse-speed: {val}. Must be in ({ValidationConstants.MIN_TIMELAPSE_SPEED}, {ValidationConstants.MAX_TIMELAPSE_SPEED}].")
                    sys.exit(1)
            except ValueError:
                log_error(f"Invalid timelapse-speed value: {sys.argv[idx + 1]}")
                sys.exit(1)

def check_config_parameter() -> Optional[str]:
    """Check and extract config path from command line arguments.
    
    Returns:
        Optional[str]: Config path if specified, None otherwise.
        Handles both relative and absolute paths.
    """
    if AppConstants.ARG_CONFIG in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_CONFIG)
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]
            # Handle both relative and absolute paths
            if os.path.isabs(config_path):
                return config_path
            else:
                return os.path.abspath(config_path)
        else:
            log_error(f"Missing value for {AppConstants.ARG_CONFIG} argument.")
            sys.exit(1)
    return None

def check_db_parameter() -> Optional[str]:
    """Check and extract database path from command line arguments.
    
    Returns:
        Optional[str]: Database path if specified, None otherwise.
        Handles both relative and absolute paths.
    """
    if AppConstants.ARG_DB in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_DB)
        if idx + 1 < len(sys.argv):
            db_path = sys.argv[idx + 1]
            # Handle both relative and absolute paths
            if os.path.isabs(db_path):
                return db_path
            else:
                return os.path.abspath(db_path)
        else:
            log_error(f"Missing value for {AppConstants.ARG_DB} argument.")
            sys.exit(1)
    return None

def get_now() -> datetime:
    """Get current simulated time based on timelapse speed."""
    global time_manager
    if time_manager:
        return time_manager.get_current_time()
    return datetime.now()

def main() -> None:
    """Main application entry point."""
    global time_manager
    
    # Initialize time manager
    time_manager = TimeManager()
    check_time_parameter()
    check_timelapse_speed_parameter()
    
    # Extract config path from command line arguments
    config_path: Optional[str] = check_config_parameter()
    
    # Extract database path from command line arguments
    db_path: Optional[str] = check_db_parameter()
    
    schedule: List[Dict[str, Any]]
    schedule, config_path = load_schedule(config_path, now_provider=get_now)
    
    # Setup logging and notifications
    log_startup()
    check_no_notification_parameter()
    
    app: ui.app.TimeboxApp = ui.app.TimeboxApp(schedule, config_path, db_path, now_provider=get_now)
    app.mainloop()

if __name__ == "__main__":
    main()
