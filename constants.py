"""
Constants used throughout the Tame-the-time application.
Centralizes magic numbers and strings for better maintainability.
"""

class UIConstants:
    """UI-related constants for layout and positioning."""
    # Card positioning ratios
    CARD_LEFT_RATIO = 0.15
    CARD_RIGHT_RATIO = 0.85
    
    # Timeline positioning
    TIMELINE_OFFSET_Y = 100
    PIXELS_PER_HOUR_DEFAULT = 60
    
    # Update intervals
    UI_UPDATE_INTERVAL_MS = 1000
    SETTINGS_SAVE_DEBOUNCE_MS = 1000
    MENU_HIDE_DELAY_MS = 500
    
    # Mouse and interaction
    MENU_SHOW_THRESHOLD_Y = 30
    RESIZE_THRESHOLD_PIXELS = 10
    INACTIVITY_REDRAW_THRESHOLD_SEC = 20
    MINIMUM_REDRAW_INTERVAL_SEC = 5
    
    # Canvas and drawing
    CARD_RESIZE_HANDLE_SIZE = 10
    TIMELINE_GRANULARITY_HOUR = 60
    TIMELINE_GRANULARITY_5MIN = 5


class Colors:
    """Color constants for UI elements."""
    # Task card colors
    FINISHED_TASK = "#cccccc"
    ACTIVE_TASK = "#ffff99"
    INACTIVE_TASK = "#add8e6"
    
    # Timeline colors
    TIMELINE_HOUR_LINE = "gray"
    TIMELINE_MINUTE_LINE = "#dddddd"
    TIMELINE_TEXT = "black"
    TIMELINE_MINUTE_TEXT = "#888888"
    
    # UI element colors
    CARD_OUTLINE = "black"
    CARD_PROGRESS_FILL = "#4CAF50"
    CARD_BEING_MODIFIED_STIPPLE = "gray25"
    CARD_DISABLED_TEXT = "#cccccc"
    TASK_COUNT_TEXT = "#0a0a0a"


class FileConstants:
    """File and path related constants."""
    SETTINGS_FILENAME = ".tame_the_time_settings.json"
    DEFAULT_CONFIG_FILENAME = "default_settings.yaml"
    LOG_FILENAME = "app.log"
    
    # Day configuration files
    DAY_CONFIG_TEMPLATE = "{day}_settings.yaml"
    DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class ValidationConstants:
    """Constants for validation and limits."""
    # Time validation
    MIN_HOUR = 0
    MAX_HOUR = 24
    MIN_MINUTE = 0
    MAX_MINUTE = 59
    TIME_ROUNDING_MINUTES = 5
    
    # Timelapse speed limits
    MIN_TIMELAPSE_SPEED = 0.0
    MAX_TIMELAPSE_SPEED = 1000.0
    
    # Notification timing
    NOTIFICATION_ADVANCE_SECONDS = 30


class NotificationConstants:
    """Notification-related constants."""
    NEXT_TASK_NOTIFICATION_TITLE = "Next Task"
    TASK_START_NOTIFICATION_TITLE = "Task Started"
    TASK_END_NOTIFICATION_TITLE = "Task Ended"
    
    # Notification timing
    ADVANCE_WARNING_SECONDS = 30


class LoggingConstants:
    """Logging-related constants."""
    # Log levels
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4
    CRITICAL = 5
    
    # Log targets
    CONSOLE = 1
    FILE = 2
    
    # Log level strings
    LEVEL_STRINGS = {
        DEBUG: "DBG",
        INFO: "INF",
        WARNING: "WRN",
        ERROR: "ERR",
        CRITICAL: "CRI"
    }


class AppConstants:
    """General application constants."""
    APP_NAME = "Tame the Time"
    DESKTOP_FILE_NAME = "TameTheTime.desktop"
    
    # Command line arguments
    ARG_NO_NOTIFICATION = "--no-notification"
    ARG_TIME = "--time"
    ARG_TIMELAPSE_SPEED = "--timelapse-speed"
    
    # Default values
    DEFAULT_TIMELAPSE_SPEED = 1.0
    DEFAULT_START_HOUR = 8
    DEFAULT_END_HOUR = 18
