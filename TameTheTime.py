import sys
from datetime import datetime, timedelta
from utils.logging import log_startup, log_info, log_error
import ui.app
from config.config_loader import load_schedule
import utils.config
from constants import AppConstants, ValidationConstants

timelapse_speed = AppConstants.DEFAULT_TIMELAPSE_SPEED
start_real_time = None
start_sim_time = None


def check_no_notification_parameter() -> None:
    if AppConstants.ARG_NO_NOTIFICATION in sys.argv:
        log_info("Notifications are disabled.")
        utils.config.allow_notification = False
    else:
        log_info("Notifications are enabled.")

def check_time_parameter() -> None:
    global start_sim_time
    if AppConstants.ARG_TIME in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_TIME)
        if idx + 1 < len(sys.argv):
            try:
                start_sim_time = datetime.fromisoformat(sys.argv[idx + 1])
            except ValueError:
                log_error(f"Invalid date format: {sys.argv[idx + 1]}. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)

def check_timelapse_speed_parameter() -> None:
    global timelapse_speed
    if AppConstants.ARG_TIMELAPSE_SPEED in sys.argv:
        idx = sys.argv.index(AppConstants.ARG_TIMELAPSE_SPEED)
        if idx + 1 < len(sys.argv):
            try:
                val = float(sys.argv[idx + 1])
                if ValidationConstants.MIN_TIMELAPSE_SPEED < val <= ValidationConstants.MAX_TIMELAPSE_SPEED:
                    timelapse_speed = val
                else:
                    log_error(f"Invalid timelapse-speed: {val}. Must be in ({ValidationConstants.MIN_TIMELAPSE_SPEED}, {ValidationConstants.MAX_TIMELAPSE_SPEED}].")
                    sys.exit(1)
            except ValueError:
                log_error(f"Invalid timelapse-speed value: {sys.argv[idx + 1]}")
                sys.exit(1)

def get_now() -> datetime:
    global start_real_time, start_sim_time
    elapsed_real = (datetime.now() - start_real_time).total_seconds()
    elapsed_sim = elapsed_real * timelapse_speed
    return start_sim_time + timedelta(seconds=elapsed_sim)

def main() -> None:
    global start_real_time, start_sim_time
    
    config_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else None
    # Init with current time
    start_real_time = start_sim_time = datetime.now()
    check_time_parameter()
    schedule, config_path = load_schedule(config_path, now_provider=get_now)
    
    # Optionally override with command line parameters
    log_startup()
    check_no_notification_parameter()
    check_timelapse_speed_parameter()
    app = ui.app.TimeboxApp(schedule, config_path, now_provider=get_now)
    app.mainloop()

if __name__ == "__main__":
    main()
