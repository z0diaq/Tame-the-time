import sys
from datetime import datetime, timedelta
from utils.logging import log_startup, log_info, log_error
import ui.app
from config.config_loader import load_schedule

timelapse_speed = 1.0
start_real_time = None
start_sim_time = None


def check_no_notification_parameter():
    if '--no-notification' in sys.argv:
        log_info("Notifications are disabled.")
        ui.app.allow_notification = False
    else:
        log_info("Notifications are enabled.")

def check_time_parameter():
    global start_sim_time
    if '--time' in sys.argv:
        idx = sys.argv.index('--time')
        if idx + 1 < len(sys.argv):
            try:
                start_sim_time = datetime.fromisoformat(sys.argv[idx + 1])
            except ValueError:
                log_error(f"Invalid date format: {sys.argv[idx + 1]}. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)

def check_timelapse_speed_parameter():
    global timelapse_speed
    if '--timelapse-speed' in sys.argv:
        idx = sys.argv.index('--timelapse-speed')
        if idx + 1 < len(sys.argv):
            try:
                val = float(sys.argv[idx + 1])
                if 0.0 < val <= 1000.0:
                    timelapse_speed = val
                else:
                    log_error(f"Invalid timelapse-speed: {val}. Must be in (0.0, 1000.0].")
                    sys.exit(1)
            except ValueError:
                log_error(f"Invalid timelapse-speed value: {sys.argv[idx + 1]}")
                sys.exit(1)

def get_now():
    global start_real_time, start_sim_time
    elapsed_real = (datetime.now() - start_real_time).total_seconds()
    elapsed_sim = elapsed_real * timelapse_speed
    return start_sim_time + timedelta(seconds=elapsed_sim)

def main():
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
