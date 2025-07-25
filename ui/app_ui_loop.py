from utils.time_utils import get_current_activity
from utils.logging import log_debug
import utils.notification
from datetime import datetime
import utils.config
from constants import UIConstants, NotificationConstants

def update_ui(app):
    now = app.now_provider()
    
    # Check if we need to update UI based on time changes
    should_update = _should_update_ui(app, now)
    
    # Always update time display (lightweight operation)
    app.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
    
    activity = get_current_activity(app.schedule, now)
    next_task, next_task_start = app.get_next_task_and_time(now)
    # --- Advance notification for next task ---
    if utils.config.allow_notification and next_task and 0 <= (next_task_start - now).total_seconds() <= NotificationConstants.ADVANCE_WARNING_SECONDS:
        if not hasattr(app, '_notified_next_task') or app._notified_next_task != next_task['name']:
            utils.notification.send_gotify_notification({
                'name': f"30 seconds to start {next_task['name']}",
                'description': [f"{next_task['name']} starts at {next_task['start_time']}"]
            }, is_delayed=True)
            app._notified_next_task = next_task['name']
    elif hasattr(app, '_notified_next_task') and (not next_task or (next_task_start - now).total_seconds() > NotificationConstants.ADVANCE_WARNING_SECONDS or (next_task_start - now).total_seconds() < 0):
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


    # Redraw timeline and cards if no action for threshold time or at the start of each minute
    if (seconds_since_last_action >= UIConstants.INACTIVITY_REDRAW_THRESHOLD_SEC or 
        (now.second == 0 and seconds_since_last_action > UIConstants.MINIMUM_REDRAW_INTERVAL_SEC)) and should_update:
        log_debug(f"Seconds since last action: {seconds_since_last_action}")
        log_debug("Redrawing timeline and cards due to inactivity...")
        app.redraw_timeline_and_cards(app.winfo_width(), app.winfo_height())
        if app.card_visual_changed:
            app.restore_card_visuals()

    # Store last update time for optimization
    app._last_ui_update = now
    
    app.after(UIConstants.UI_UPDATE_INTERVAL_MS, lambda: update_ui(app))


def _should_update_ui(app, now: datetime) -> bool:
    """Determine if UI needs updating based on time changes and state."""
    # Always update on first run
    if not hasattr(app, '_last_ui_update'):
        return True
    
    last_update = getattr(app, '_last_ui_update', None)
    if last_update is None:
        return True
    
    # Update if minute changed (for time-sensitive displays)
    if now.minute != last_update.minute:
        return True
    
    # Update if schedule or cards changed
    if getattr(app, 'schedule_changed', False) or getattr(app, 'card_visual_changed', False):
        return True
    
    # Update every 10 seconds for active task progress
    if (now - last_update).total_seconds() >= 10:
        return True
    
    return False
