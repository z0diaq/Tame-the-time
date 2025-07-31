from utils.time_utils import get_current_activity
from utils.logging import log_debug
from datetime import datetime
from typing import Dict
from constants import UIConstants
from models.schedule import ScheduledActivity

def update_ui(app):
    """Update the UI based on time changes and state."""
    now = app.now_provider()
    
    # Check if we need to update UI based on time changes
    activity = get_current_activity(app.schedule, now)
    should_update = _should_update_ui(app, now, activity)
    
    # Always update time display (lightweight operation)
    app.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
    
    next_task, next_task_start = app.get_next_task_and_time(now)
    
    # Convert dictionary activities to ScheduledActivity objects for notification service
    current_activity_obj = None
    if activity:
        current_activity_obj = ScheduledActivity.from_dict(activity)
    
    next_activity_obj = None
    if next_task:
        next_activity_obj = ScheduledActivity.from_dict(next_task)
    
    # Use notification service for all notification logic
    app.notification_service.check_and_send_notifications(
        current_activity_obj, next_activity_obj, next_task_start
    )
    # --- UI update logic ---
    if activity:
        desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(activity["description"]))
        app.activity_label.config(
            text=f"Actions:\n{desc}"
        )
        # Activity change notifications are now handled by the notification service
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

    # Redraw timeline and cards if no action for threshold time or at the start of each minute
    if should_update:
        log_debug("Redrawing timeline and cards due to inactivity...")
        app.redraw_timeline_and_cards(app.winfo_width(), app.winfo_height())
        if app.card_visual_changed:
            app.restore_card_visuals()
            app.card_visual_changed = False
    else:
        _refresh_active_card_if_undone_tasks(app, activity)

    # Store last update time for optimization
    app._last_ui_update = now
        
    app.after(UIConstants.UI_UPDATE_INTERVAL_MS, lambda: update_ui(app))

def _refresh_active_card_if_undone_tasks(app, activity):
    """Refresh only active card to show blinking tasks count."""
    tasks = activity.get("tasks", [])
    if not tasks:
        return
    
    # Find the corresponding card object to check _tasks_done
    for card_obj in getattr(app, 'cards', []):
        if (card_obj.activity.get('name') == activity.get('name') and 
            card_obj.activity.get('start_time') == activity.get('start_time')):
            # Use _tasks_done if present, otherwise assume all tasks are undone
            tasks_done = getattr(card_obj, '_tasks_done', [False] * len(tasks))
            if any(not done for done in tasks_done):
                log_debug("Refreshing active card due to undone tasks")
                card_obj.update_card_visuals(
                    card_obj.start_hour,
                    card_obj.start_minute,
                    app.start_hour,
                    app.pixels_per_hour,
                    app.offset_y,
                    now=app.now_provider().time(),
                    width=app.winfo_width()
                )

def _should_update_ui(app, now: datetime, activity: Dict) -> bool:
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
    if activity and (now - last_update).total_seconds() >= 10:
        return True

    # Redraw everything every 20 seconds
    seconds_since_last_action = (datetime.now() - app.last_action).total_seconds()
    log_debug(f"Seconds since last action: {seconds_since_last_action}")

    if seconds_since_last_action >= UIConstants.INACTIVITY_REDRAW_THRESHOLD_SEC:
        return True 
    
    # Update every second at the start of each minute to show change of active card
    if now.second == 0 and seconds_since_last_action > UIConstants.MINIMUM_REDRAW_INTERVAL_SEC:
        return True
    
    return False
