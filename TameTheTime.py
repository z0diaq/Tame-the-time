import sys
import os
import json
import tkinter as tk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from utils.logging import log_startup, log_info, log_error
import ui.app
from config.config_loader import load_schedule
import utils.config
from constants import AppConstants, ValidationConstants
from models.time_manager import TimeManager
from utils.translator import init_translator, t

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

def load_user_settings() -> dict:
    """Load user settings from file."""
    settings_path = os.path.expanduser("~/.tame_the_time_settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            return json.load(f)
    return {}

def ask_schedule_selection(last_schedule_path: str) -> Optional[str]:
    """Show dialog asking user which schedule to load.
    
    Args:
        last_schedule_path: Path to the last loaded schedule
        
    Returns:
        Path to load (either last_schedule_path or None for default), 
        or False if user cancelled
    """
    # Create a temporary root window for the dialog
    root = tk.Tk()
    root.withdraw()
    
    # Get short filename for display
    filename = os.path.basename(last_schedule_path)
    
    # Format the message with the last schedule path
    message = t("message.schedule_selection_prompt").format(last_schedule=filename)
    
    # Create custom dialog with three buttons
    dialog = tk.Toplevel(root)
    dialog.title(t("window.schedule_selection"))
    dialog.geometry("400x150")
    dialog.resizable(False, False)
    
    # Center the dialog on screen
    dialog.update_idletasks()
    x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
    y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
    dialog.geometry(f"+{x}+{y}")
    
    result = {"choice": None}
    
    def on_last_schedule():
        result["choice"] = last_schedule_path
        dialog.destroy()
        root.destroy()
    
    def on_default_schedule():
        result["choice"] = None  # None means use default
        dialog.destroy()
        root.destroy()
    
    # Message label
    label = tk.Label(dialog, text=message, wraplength=350, justify="left", padx=20, pady=20)
    label.pack()
    
    # Button frame
    button_frame = tk.Frame(dialog)
    button_frame.pack(pady=10)
    
    # Buttons
    last_btn = tk.Button(button_frame, text=t("button.last_schedule"), command=on_last_schedule, width=15)
    last_btn.pack(side=tk.LEFT, padx=5)
    
    default_btn = tk.Button(button_frame, text=t("button.default_schedule"), command=on_default_schedule, width=15)
    default_btn.pack(side=tk.LEFT, padx=5)
    
    # Handle window close (X button)
    dialog.protocol("WM_DELETE_WINDOW", on_default_schedule)
    
    # Make dialog modal
    dialog.transient(root)
    dialog.grab_set()
    
    # Wait for user interaction
    root.wait_window(dialog)
    
    return result["choice"]

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
    
    # If no custom config path provided, check for last schedule and ask user
    if config_path is None:
        settings = load_user_settings()
        last_schedule_path = settings.get('last_schedule_path')
        
        # Initialize language from settings for dialog translations
        current_language = settings.get('current_language', 'en')
        init_translator(current_language)
        
        # If there's a last schedule and it exists, ask user which to load
        if last_schedule_path and os.path.exists(last_schedule_path):
            log_info(f"Found last schedule: {last_schedule_path}")
            selected_path = ask_schedule_selection(last_schedule_path)
            
            # selected_path will be either:
            # - last_schedule_path (user chose last schedule)
            # - None (user chose default schedule)
            config_path = selected_path
            
            if config_path:
                log_info(f"User selected last schedule: {config_path}")
            else:
                log_info("User selected default schedule")
    
    schedule: List[Dict[str, Any]]
    schedule, config_path = load_schedule(config_path, now_provider=get_now)
    
    # Setup logging and notifications
    log_startup()
    check_no_notification_parameter()
    
    app: ui.app.TimeboxApp = ui.app.TimeboxApp(schedule, config_path, db_path, now_provider=get_now)
    app.mainloop()

if __name__ == "__main__":
    main()
