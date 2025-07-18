from utils.time_utils import get_current_activity
from utils.logging import log_debug
import utils.notification
from datetime import datetime
import utils.config

def update_ui(app):
    now = app.now_provider()
    app.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
    activity = get_current_activity(app.schedule, now)
    next_task, next_task_start = app.get_next_task_and_time(now)
    # --- 30 seconds before next task notification ---
    if utils.config.allow_notification and next_task and 0 <= (next_task_start - now).total_seconds() <= 30:
        if not hasattr(app, '_notified_next_task') or app._notified_next_task != next_task['name']:
            utils.notification.send_gotify_notification({
                'name': f"30 seconds to start {next_task['name']}",
                'description': [f"{next_task['name']} starts at {next_task['start_time']}"]
            }, is_delayed=True)
            app._notified_next_task = next_task['name']
    elif hasattr(app, '_notified_next_task') and (not next_task or (next_task_start - now).total_seconds() > 30 or (next_task_start - now).total_seconds() < 0):
        app._notified_next_task = None
    # --- UI update logic ---
    if activity:
        desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(activity["description"]))
        app.activity_label.config(
            text=f"Actions:\n{desc}"
        )
        # Send notification if activity changed and notifications are allowed
        if (app.last_activity is None or app.last_activity["name"] != activity["name"]) and utils.config.allow_notification:
            utils.notification.send_gotify_notification(activity)
            log_debug(f"Notification sent for activity: {activity['name']}")
        app.last_activity = activity
    else:
        # --- Show time till next task if no active task ---
        if next_task is None:
            text = "No scheduled task was found."
        else:
            seconds_left = int((next_task_start - now).total_seconds())
            if seconds_left < 0:
                # Handle over-midnight: add 24h
                seconds_left += 24*3600
            hours, remainder = divmod(seconds_left, 3600)
            minutes, seconds = divmod(remainder, 60)
            text = f"No active task\nNext: {next_task['name']} at {next_task['start_time']}\nTime left: {hours:02d}:{minutes:02d}:{seconds:02d}"
        app.activity_label.config(text=text)
    # Redraw everything every 20 seconds
    seconds_since_last_action = (datetime.now() - app.last_action).total_seconds()

    # Redraw timeline and cards if no action for 20 seconds or at the start of each minute
    if seconds_since_last_action >= 20 or (now.second == 0 and seconds_since_last_action > 5):
        log_debug("Redrawing timeline and cards due to inactivity...")
        app.redraw_timeline_and_cards(app.winfo_width(), app.winfo_height())
        if app.card_visual_changed:
            app.restore_card_visuals()

    app.after(1000, lambda: update_ui(app))
