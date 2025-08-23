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
    TIMELINE_CURRENT_TIME_LINE = "green"
    TIMELINE_CURRENT_TIME_TEXT = "green"
    
    # UI element colors
    CARD_OUTLINE = "black"
    CARD_PROGRESS_FILL = "green"
    CARD_PROGRESS_OUTLINE = "black"
    CARD_PROGRESS_FILL_NO_OUTLINE = "green"
    CARD_BEING_MODIFIED_STIPPLE = "gray25"
    CARD_DISABLED_TEXT = "#cccccc"
    CARD_LABEL_TEXT = "black"
    
    # Task count colors
    TASK_COUNT_TEXT = "#0a0a0a"
    TASK_COUNT_ALL_DONE = "#008000"  # Dark green
    TASK_COUNT_PAST_UNDONE = "#ff4040"  # Light red
    TASK_COUNT_ACTIVE_UNDONE = "#ff0000"  # Red (for blinking)
    TASK_COUNT_FUTURE_UNDONE = "#0a0a0a"  # Default black
    
    # Status bar colors
    STATUS_BAR_BG = "#e0e0e0"
    STATUS_BAR_TEXT = "black"
    STATUS_BAR_WARNING_BG = "red"
    STATUS_BAR_WARNING_TEXT = "white"
    
    # App UI colors
    TIME_LABEL_BG = "#0f8000"
    ACTIVITY_LABEL_BG = "#ffff99"
    ACTIVITY_LABEL_TEXT = "black"
    CANVAS_BG = "white"
    CHART_FRAME_BG = "white"
    
    # Chart colors for statistics
    CHART_COLOR_1 = "#1f77b4"
    CHART_COLOR_2 = "#ff7f0e"
    CHART_COLOR_3 = "#2ca02c"
    CHART_COLOR_4 = "#d62728"
    CHART_COLOR_5 = "#9467bd"
    CHART_COLOR_6 = "#8c564b"
    CHART_COLOR_7 = "#e377c2"
    CHART_COLOR_8 = "#7f7f7f"
    CHART_COLOR_9 = "#bcbd22"
    CHART_COLOR_10 = "#17becf"
    
    @classmethod
    def get_chart_colors(cls):
        """Return list of chart colors for statistics."""
        return [
            cls.CHART_COLOR_1, cls.CHART_COLOR_2, cls.CHART_COLOR_3, cls.CHART_COLOR_4,
            cls.CHART_COLOR_5, cls.CHART_COLOR_6, cls.CHART_COLOR_7, cls.CHART_COLOR_8,
            cls.CHART_COLOR_9, cls.CHART_COLOR_10
        ]


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
