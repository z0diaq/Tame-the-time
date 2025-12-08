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
from __version__ import __version__

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

def ask_schedule_selection(last_schedule_path: Optional[str], day_schedule_path: Optional[str]) -> Optional[str]:
    """Show dialog with dropdown asking user which schedule to load.
    
    Args:
        last_schedule_path: Path to the last loaded schedule (None if none or was default)
        day_schedule_path: Path to today's day-specific schedule (None if doesn't exist)
        
    Returns:
        Path to load, or None for default schedule
    """
    # Create a temporary root window for the dialog
    root = tk.Tk()
    root.title(t("window.schedule_selection"))
    root.geometry("450x180")
    root.resizable(False, False)
    
    # Center the window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # Build dropdown options in priority order
    options = []  # List of (display_text, path_value) tuples
    
    # 1. Last used schedule (highest priority if exists)
    if last_schedule_path and os.path.exists(last_schedule_path):
        filename = os.path.basename(last_schedule_path)
        display = t("schedule_option.last_used").format(filename=filename)
        options.append((display, last_schedule_path))
    
    # 2. Today's schedule (second priority if exists and different from last)
    if day_schedule_path and os.path.exists(day_schedule_path):
        if not last_schedule_path or day_schedule_path != last_schedule_path:
            filename = os.path.basename(day_schedule_path)
            display = t("schedule_option.today").format(filename=filename)
            options.append((display, day_schedule_path))
    
    # 3. Default schedule (always available)
    options.append((t("schedule_option.default"), None))
    
    # Extract display texts for combobox values
    display_texts = [display for display, _ in options]
    
    result = {"choice": None}
    
    def on_proceed():
        # Get selected index from combobox and map to path
        selected_text = dropdown_var.get()
        selected_idx = display_texts.index(selected_text)
        result["choice"] = options[selected_idx][1]
        root.quit()
        root.destroy()
    
    # Label
    label = tk.Label(root, text=t("label.select_schedule_to_load"), padx=20, pady=10)
    label.pack(anchor="w")
    
    # Dropdown (Combobox)
    from tkinter import ttk
    dropdown_frame = tk.Frame(root)
    dropdown_frame.pack(fill="x", padx=20, pady=5)
    
    dropdown_var = tk.StringVar(value=display_texts[0])  # Default to first option
    combobox = ttk.Combobox(
        dropdown_frame,
        textvariable=dropdown_var,
        values=display_texts,
        state="readonly",
        width=55
    )
    combobox.pack(fill="x", pady=2)
    combobox.current(0)  # Select first option
    
    # Conditional hint: Show only if both last and day schedules exist
    show_hint = (
        last_schedule_path and os.path.exists(last_schedule_path) and
        day_schedule_path and os.path.exists(day_schedule_path) and
        last_schedule_path != day_schedule_path
    )
    
    if show_hint:
        hint_label = tk.Label(
            root,
            text=t("message.day_schedule_available_hint"),
            wraplength=400,
            justify="left",
            padx=20,
            pady=5,
            fg="#666666",
            font=("TkDefaultFont", 9, "italic")
        )
        hint_label.pack(anchor="w")
    
    # Button frame
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    # Proceed button
    proceed_btn = tk.Button(button_frame, text=t("button.proceed"), command=on_proceed, width=15)
    proceed_btn.pack()
    
    # Handle window close (X button) - default to first option
    root.protocol("WM_DELETE_WINDOW", on_proceed)
    
    # Bring window to front and focus
    root.lift()
    root.focus_force()
    
    # Run the dialog event loop
    root.mainloop()
    
    return result["choice"]

def main() -> None:
    """Main application entry point."""
    global time_manager
    
    # Check for version flag
    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"Tame-the-Time version {__version__}")
        sys.exit(0)
    
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
        
        # Import here to avoid circular dependency
        from config.config_loader import get_day_config_path
        from utils.locale_utils import get_weekday_name
        
        # Determine if there's a day-specific schedule for today
        current_day = get_now().date().weekday()
        day_schedule_filename = f"{get_weekday_name(current_day)}_settings.yaml"
        day_schedule_path = day_schedule_filename if os.path.exists(day_schedule_filename) else None
        
        # Prepare last_schedule_path for dialog (None if it was default)
        last_schedule_for_dialog = None
        if last_schedule_path and not last_schedule_path.endswith('default_settings.yaml'):
            last_schedule_for_dialog = last_schedule_path
        
        # Show dialog if there's either a last schedule or a day-specific schedule
        should_show_dialog = (
            (last_schedule_for_dialog and os.path.exists(last_schedule_for_dialog)) or
            (day_schedule_path and os.path.exists(day_schedule_path))
        )
        
        if should_show_dialog:
            if last_schedule_for_dialog:
                log_info(f"Found last schedule: {last_schedule_for_dialog}")
            if day_schedule_path:
                log_info(f"Found day-specific schedule: {day_schedule_path}")
            
            selected_path = ask_schedule_selection(last_schedule_for_dialog, day_schedule_path)
            config_path = selected_path
            
            if config_path:
                log_info(f"User selected schedule: {config_path}")
            else:
                log_info("User selected default schedule")
        else:
            log_info("No previous or day-specific schedule found, using default schedule")
    
    schedule: List[Dict[str, Any]]
    schedule, config_path = load_schedule(config_path, now_provider=get_now)
    
    # Setup logging and notifications
    log_startup()
    log_info(f"Tame-the-Time version {__version__}")
    check_no_notification_parameter()
    
    app: ui.app.TimeboxApp = ui.app.TimeboxApp(schedule, config_path, db_path, now_provider=get_now)
    app.mainloop()

if __name__ == "__main__":
    main()
