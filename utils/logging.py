import os
import traceback
from datetime import datetime
import platform

loglevel_debug = 1
loglevel_info = 2
loglevel_warning = 3
loglevel_error = 4
loglevel_critical = 5

logtarget_file = 1
logtarget_console = 2

logtarget = logtarget_console
loglevel = loglevel_info
logfile = "app.log"
logfile_handle = None

logging_start_time = datetime.now()

def loglevel_to_string(level: int) -> str:
    """
    Converts a log level integer to its string representation.

    Args:
        level (int): The log level integer.

    Returns:
        str: The string representation of the log level.
    """
    if level == loglevel_debug:
        return "DBG"
    elif level == loglevel_info:
        return "INF"
    elif level == loglevel_warning:
        return "WRN"
    elif level == loglevel_error:
        return "ERR"
    elif level == loglevel_critical:
        return "CRI"
    else:
        return "UNK"

def log(message: str, level: int = loglevel_info):
    """
    Logs a message to a specified file with a given log level.

    Args:
        message (str): The message to log.
        level (int): The log level (e.g., loglevel_info, loglevel_debug, loglevel_error).
    """
    if level < loglevel:
        return
    
    time_since_start = datetime.now() - logging_start_time

    # Format the message with a timestamp
    log_message = f"{datetime.now().strftime('%y%m%d %H%M%S')} {time_since_start.total_seconds():<.3f} [{loglevel_to_string(level)}]: {message}"

    if logtarget == logtarget_console:
        print(log_message)
    elif logtarget == logtarget_file:
        if not logfile:
            raise ValueError("Logfile is not set. Please set the logfile before logging.")
        global logfile_handle
        if logfile_handle is None:
            logfile_handle = open(logfile, "a")
        logfile_handle.write(log_message + "\n")

def log_error(message: str):
    """
    Logs an error message to a specified file.

    Args:
        message (str): The error message to log.
    """
    log(message, level=loglevel_error)

def log_info(message: str):
    """
    Logs an informational message to a specified file.
    Args:
        message (str): The informational message to log.
    """
    log(message, level=loglevel_info)

def log_debug(message: str):
    """
    Logs a debug message to a specified file.
    Args:
        message (str): The debug message to log.
    """
    log(message, level=loglevel_debug)

def log_warning(message: str):
    """
    Logs a warning message to a specified file.
    Args:
        message (str): The warning message to log.
    """
    log(message, level=loglevel_warning)

def log_critical(message: str):
    """
    Logs a critical message to a specified file.
    Args:
        message (str): The critical message to log.
    """
    log(message, level=loglevel_critical)

def log_exception(exception: Exception):
    """
    Logs an exception message to a specified file.
    Args:
        exception (Exception): The exception to log.
    """
    log_error(f"Exception occurred: {str(exception)}")
    log_error(f"Stack trace: {''.join(traceback.format_exception(None, exception, exception.__traceback__))}")

def log_traceback():
    """
    Logs the current traceback to a specified file.
    Args:
        file (str): The file to log the traceback to.
    """
    tb = traceback.format_exc()
    if tb:
        log_error(f"Traceback:\n{tb}")
    else:
        log_info("No traceback available.")

def ensure_log_directory(file: str = "app.log"):
    """
    Ensures that the directory for the log file exists.
    Args:
        file (str): The log file path.
    """
    directory = os.path.dirname(file)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        log_info(f"Created log directory: {directory}")
    else:
        log_info(f"Log directory already exists: {directory}")

def setup_logging(file: str = "app.log", level: int = loglevel_info):
    """
    Sets up the logging environment by ensuring the log directory exists.
    Args:
        file (str): The log file path.
    """
    global loglevel
    loglevel = level
    ensure_log_directory(file)
    log_info("Logging setup complete.")


def setup_logging_console(level: int = loglevel_info):
    """
    Sets up console logging.
    Args:
        level (int): The log level for console logging.
    """
    global logtarget, loglevel
    logtarget = logtarget_console
    loglevel = level
    log_info("Console logging setup complete.")

def setup_logging_file(file: str = "app.log", level: int = loglevel_info):
    """
    Sets up file logging.
    Args:
        file (str): The log file path.
        level (int): The log level for file logging.
    """
    global logtarget, logfile, loglevel
    logtarget = logtarget_file
    logfile = file
    loglevel = level
    ensure_log_directory(file)
    log_info("File logging setup complete.")

def log_startup():
    """
    Setup loging using argc and argv if provided.
    """
    file = "app.log"
    level = loglevel_info

    if "--log-file" in os.sys.argv:
        idx = os.sys.argv.index("--log-file")
        if idx + 1 < len(os.sys.argv):
            file = os.sys.argv[idx + 1]
        if not file.endswith(".log"):
            file += ".log"

    # Check for command line arguments to set log level
    if "--log-level" in os.sys.argv:
        idx = os.sys.argv.index("--log-level")
        if idx + 1 < len(os.sys.argv):
            level_str = os.sys.argv[idx + 1].upper()
            if level_str in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                if level_str == "DEBUG":
                    level = loglevel_debug
                elif level_str == "INFO":
                    level = loglevel_info
                elif level_str == "WARNING":
                    level = loglevel_warning
                elif level_str == "ERROR":
                    level = loglevel_error
                elif level_str == "CRITICAL":
                    level = loglevel_critical
            else:
                raise ValueError(f"Invalid log level: {level_str}")
        else:
            raise ValueError("No log level provided after --log-level")

    global logtarget
    if "--log-target" in os.sys.argv:
        idx = os.sys.argv.index("--log-target")
        if idx + 1 < len(os.sys.argv):
            target_str = os.sys.argv[idx + 1].lower()
            if target_str == "file":
                logtarget = logtarget_file
            elif target_str == "console":
                logtarget = logtarget_console
            else:
                raise ValueError(f"Invalid log target: {target_str}")
        else:
            raise ValueError("No log target provided after --log-target")

    if logtarget == logtarget_file:
        setup_logging_file(file, level)
    elif logtarget == logtarget_console:
        setup_logging_console(level)
    else:
        raise ValueError(f"Invalid log target: {target_str}")

    log_info("Application started.")
    log_info(f"Log file: {file}")
    log_info(f"Python version: {os.sys.version}")
    if platform.system() == "Windows":
        log_info(f"OS: {os.name}")
    else:
        log_info(f"OS: {os.name} {os.uname().release}")

def log_shutdown(file: str = "app.log"):
    """
    Logs the shutdown information of the application.
    Args:
        file (str): The log file path.
    """
    log_info("Application shutting down.")
