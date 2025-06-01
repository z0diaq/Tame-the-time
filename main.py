import sys
from config.config_loader import load_schedule
from ui.app import TimeboxApp

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else None
    schedule = load_schedule(config_path)
    app = TimeboxApp(schedule)
    app.mainloop()

if __name__ == "__main__":
    main()
