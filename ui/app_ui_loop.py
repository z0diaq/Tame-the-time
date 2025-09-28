from utils.time_utils import get_current_activity
from utils.logging import log_debug, log_error, log_info
from datetime import datetime
from typing import Dict
from constants import UIConstants
from models.schedule import ScheduledActivity
from ui.timeline import reposition_current_time_line
import os
import yaml
from utils.locale_utils import get_weekday_name

def update_ui(app):
    """Update the UI based on time changes and state."""
    now = app.now_provider()
    
    # Check for day rollover and handle it
    _check_and_handle_day_rollover(app, now)
    
    # Check if we need to update UI based on time changes
    activity = get_current_activity(app.schedule, now)
    should_update = _should_update_ui(app, now, activity)
    
    # Always update time display (lightweight operation)
    app.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
    
    # Always update current time line position and format (lightweight operation)
    mouse_inside = _is_mouse_inside_window(app)
    reposition_current_time_line(app.canvas, app.current_time_ids, app.start_hour, app.pixels_per_hour, app.offset_y, app.winfo_width(), now.time(), mouse_inside)
    
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
    if not activity:
        return
    
    tasks = activity.get("tasks", [])
    if not tasks:
        return
    
    # Find the corresponding card object to check _tasks_done using ID-based matching
    activity_id = activity.get("id")
    for card_obj in getattr(app, 'cards', []):
        if activity_id and card_obj.activity.get('id') == activity_id:
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

def _is_mouse_inside_window(app) -> bool:
    """Check if mouse is inside the window area."""
    try:
        mouse_x = app.winfo_pointerx()
        mouse_y = app.winfo_pointery()
        window_x = app.winfo_rootx()
        window_y = app.winfo_rooty()
        window_width = app.winfo_width()
        window_height = app.winfo_height()
        
        return (window_x <= mouse_x <= window_x + window_width and 
                window_y <= mouse_y <= window_y + window_height)
    except Exception:
        return False

def _should_update_ui(app, now: datetime, activity: Dict) -> bool:
    """Determine if UI needs updating based on time changes and state."""
    # Always update on first run
    if not hasattr(app, '_last_ui_update'):
        log_debug("No previous _last_ui_update")
        return True
    
    last_update = getattr(app, '_last_ui_update', None)
    if last_update is None:
        log_debug("The last_update is not set")
        return True
    
    # Don't update if mouse pointer is inside window area - avoid interfering with user interaction
    try:
        mouse_x = app.winfo_pointerx()
        mouse_y = app.winfo_pointery()
        window_x = app.winfo_rootx()
        window_y = app.winfo_rooty()
        window_width = app.winfo_width()
        window_height = app.winfo_height()
        
        if (window_x <= mouse_x <= window_x + window_width and 
            window_y <= mouse_y <= window_y + window_height):
            log_debug("Mouse pointer inside window area - skipping UI update")
            return False
    except Exception as e:
        # If we can't get mouse position, continue with normal checks
        log_debug(f"Could not check mouse position: {e}")
    
    # Update if cards changed
    if getattr(app, 'card_visual_changed', False):
        log_debug("Cards visuals changed!")
        return True
    
    # Update every 10 seconds for active task progress
    if activity and (now - last_update).total_seconds() >= 10:
        log_debug("More than 10 seconds since last_update")
        return True

    # Redraw everything every 20 seconds
    seconds_since_last_action = (datetime.now() - app.last_action).total_seconds()
    log_debug(f"Seconds since last action: {seconds_since_last_action}")

    if seconds_since_last_action >= UIConstants.INACTIVITY_REDRAW_THRESHOLD_SEC:
        log_debug("Time since last acton above INACTIVE_REDRAW_THRESHOLD_SEC")
        return True 
    
    # Update every second at the start of each minute to show change of active card
    if now.minute != last_update.minute and seconds_since_last_action > UIConstants.MINIMUM_REDRAW_INTERVAL_SEC:
        log_debug("New minute and seconds since last action above MINIMUM_REDRAW_INTERVAL_SEC")
        return True
    
    return False


def _check_and_handle_day_rollover(app, now: datetime) -> None:
    """
    Check if current time has passed the day_start point and handle day rollover.
    
    Args:
        app: The main application instance
        now: Current datetime
    """
    # Initialize last_day_rollover_check if not present
    if not hasattr(app, '_last_day_rollover_check'):
        app._last_day_rollover_check = now
        return
    
    last_check = app._last_day_rollover_check
    day_start_hour = getattr(app, 'day_start', 0)
    
    # Check if we've crossed the day_start boundary
    if _has_crossed_day_start_boundary(last_check, now, day_start_hour):
        log_debug(f"Day rollover detected at {now.strftime('%H:%M:%S')} (day_start: {day_start_hour})")
        _handle_day_rollover(app, now)
    
    app._last_day_rollover_check = now


def _has_crossed_day_start_boundary(last_time: datetime, current_time: datetime, day_start_hour: int) -> bool:
    """
    Check if we've crossed the day_start boundary between two time points.
    
    Args:
        last_time: Previous check time
        current_time: Current time
        day_start_hour: Hour when new day starts (0-23)
        
    Returns:
        True if day_start boundary was crossed
    """
    # If times are on different calendar days, check if we crossed day_start
    if last_time.date() != current_time.date():
        # Check if current time is past day_start on the new calendar day
        if current_time.hour >= day_start_hour:
            return True
    
    # Check if we crossed day_start within the same calendar day
    # This handles cases where day_start is not midnight (e.g., 6 AM)
    if (last_time.hour < day_start_hour <= current_time.hour and 
        last_time.date() == current_time.date()):
        return True
    
    return False


def _handle_day_rollover(app, now: datetime) -> None:
    """
    Handle day rollover by checking for new schedule file, loading it if exists,
    resetting timeline, tasks, and statistics.
    
    Args:
        app: The main application instance
        now: Current datetime
    """
    log_debug("Handling day rollover...")
    
    # 1. Check if a new schedule file exists for the new day and load it
    schedule_loaded = _check_and_load_new_day_schedule(app, now)
    
    # 2. Reset timeline to start from top (center on current time)
    _reset_timeline_to_top(app, now)
    
    # 3. Reset all task completion status to undone (only if no new schedule was loaded)
    if not schedule_loaded:
        _reset_all_task_completion_status(app)
    
    # 4. Create new daily task entries for the new day
    _create_new_day_task_entries(app)
    
    # 5. Update status bar to reflect new day statistics
    app.update_status_bar()
    
    log_info(f"Day rollover completed at {now.strftime('%H:%M:%S %Y-%m-%d')}")
    
    # Mark last action time to prevent immediate UI updates
    app.last_action = now


def _reset_timeline_to_top(app, now: datetime) -> None:
    """Reset timeline view to start from the top (current time centered)."""
    try:
        # Center view on current time
        minutes_since_start = (now.hour - app.start_hour) * 60 + now.minute
        center_y = int(minutes_since_start * app.pixels_per_hour / 60) + 100
        new_offset = (app.winfo_height() // 2) - center_y
        delta_y = new_offset - app.offset_y
        app.offset_y = new_offset
        
        # Move timeline and cards to new position
        from ui.zoom_and_scroll import move_timelines_and_cards
        move_timelines_and_cards(app, delta_y)
        
        log_debug("Timeline reset to top for new day")
    except Exception as e:
        log_error(f"Failed to reset timeline to top: {e}")


def _reset_all_task_completion_status(app) -> None:
    """Reset all task completion status to undone for the new day."""
    try:
        reset_count = 0
        for card_obj in getattr(app, 'cards', []):
            if hasattr(card_obj, '_tasks_done') and card_obj._tasks_done:
                # Reset all tasks to undone
                card_obj._tasks_done = [False] * len(card_obj._tasks_done)
                reset_count += len(card_obj._tasks_done)
                
                # Update card visuals to reflect reset status
                card_obj.update_card_visuals(
                    card_obj.start_hour, card_obj.start_minute,
                    app.start_hour, app.pixels_per_hour, app.offset_y,
                    now=app.now_provider().time(), width=app.winfo_width()
                )
        
        log_debug(f"Reset {reset_count} task completion statuses for new day")
    except Exception as e:
        log_error(f"Failed to reset task completion status: {e}")


def _check_and_load_new_day_schedule(app, now: datetime) -> bool:
    """
    Check if a schedule file exists for the new day and load it if found.
    
    Args:
        app: The main application instance
        now: Current datetime
        
    Returns:
        bool: True if a new schedule was loaded, False otherwise
    """
    try:
        new_schedule_path = _get_new_day_schedule_path(now)
        
        if new_schedule_path and os.path.exists(new_schedule_path):
            log_info(f"Found schedule file for new day: {new_schedule_path}")
            return _load_new_schedule_and_replace_cards(app, new_schedule_path)
        else:
            log_debug(f"No specific schedule file found for new day, keeping current schedule")
            return False
            
    except Exception as e:
        log_error(f"Failed to check/load new day schedule: {e}")
        return False


def _get_new_day_schedule_path(now: datetime) -> str:
    """
    Get the schedule file path for the new day based on weekday.
    
    Args:
        now: Current datetime
        
    Returns:
        str: Path to the schedule file for the new day
    """
    current_weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    if 0 <= current_weekday <= 6:
        day_schedule_path = f"{get_weekday_name(current_weekday)}_settings.yaml"
        log_debug(f"Checking for schedule file: {day_schedule_path}")
        return day_schedule_path
    
    return "default_settings.yaml"


def _load_new_schedule_and_replace_cards(app, schedule_path: str) -> bool:
    """
    Load a new schedule from file and replace all existing cards.
    
    Args:
        app: The main application instance
        schedule_path: Path to the new schedule file
        
    Returns:
        bool: True if schedule was successfully loaded, False otherwise
    """
    try:
        # Load new schedule from file
        with open(schedule_path, 'r') as f:
            new_schedule = yaml.safe_load(f)
        
        if not new_schedule:
            log_error(f"Empty or invalid schedule in {schedule_path}")
            return False
        
        # Remove all current cards from canvas
        for card_obj in app.cards:
            card_obj.delete()
        app.cards.clear()
        
        # Clear current schedule and load new one
        app.schedule.clear()
        app.schedule.extend(new_schedule)
        
        # Update config path to the new file
        app.config_path = schedule_path
        
        # Ensure all loaded activities have unique IDs
        app.ensure_activity_ids()
        
        # Ensure all tasks have UUIDs
        app.ensure_task_uuids()
        
        # Create new task cards from the loaded schedule
        app.cards = app.create_task_cards()
        
        # Update card positions after size change
        app.update_cards_after_size_change()
        
        # Load task done states from database for the new schedule
        app._load_daily_task_entries()
        
        log_info(f"Successfully loaded new schedule from {schedule_path} with {len(new_schedule)} activities")
        return True
        
    except Exception as e:
        log_error(f"Failed to load new schedule from {schedule_path}: {e}")
        return False


def _create_new_day_task_entries(app) -> None:
    """Create new daily task entries for the new day."""
    try:
        if hasattr(app, 'task_tracking_service') and app.task_tracking_service:
            entries_created = app.task_tracking_service.create_daily_task_entries(app.schedule)
            if entries_created > 0:
                log_info(f"Created {entries_created} new task entries for new day")
        else:
            log_debug("No task tracking service available for creating new day entries")
    except Exception as e:
        log_error(f"Failed to create new day task entries: {e}")
