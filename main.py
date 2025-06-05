import sys
from config.config_loader import load_schedule
import ui.app
from datetime import datetime

now_parameter_value = None

def check_now_parameter():
    global now_parameter_value
    if '--now' in sys.argv:
        idx = sys.argv.index('--now')
        if idx + 1 < len(sys.argv):
            try:
                now_parameter_value = datetime.fromisoformat(sys.argv[idx + 1])
            except ValueError:
                print(f"Invalid date format: {sys.argv[idx + 1]}. Expected ISO format (YYYY-MM-DDTHH:MM:SS).")
                sys.exit(1)

def check_no_notification_parameter():
    if '--no-notification' in sys.argv:
        print("Notifications are disabled.")
        ui.app.allow_notification = False
    else:
        print("Notifications are enabled.")

def get_now():
    if now_parameter_value is not None:
        return now_parameter_value
    return datetime.now()

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else None
    schedule = load_schedule(config_path)
    check_now_parameter()
    check_no_notification_parameter()
    app = ui.app.TimeboxApp(schedule, now_provider=get_now)
    app.mainloop()

if __name__ == "__main__":
    main()
