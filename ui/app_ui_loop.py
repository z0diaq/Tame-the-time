from utils.time_utils import get_current_activity
from utils.logging import log_debug, log_error, log_info
from datetime import datetime
from typing import Dict, Optional
from constants import UIConstants
from models.schedule import ScheduledActivity
from ui.timeline import reposition_current_time_line
import os
import yaml
from utils.locale_utils import get_weekday_name
import tkinter.font as tkfont
from ui.day_rollover_dialog import show_day_rollover_dialog


def _is_activity_in_schedule(app, activity_id: str) -> bool:
    """
    Check if an activity with the given ID exists in the current schedule.
    
    Args:
        app: The main TimeboxApp instance
        activity_id: The activity ID to check
    
    Returns:
        True if activity exists in current schedule, False otherwise
    """
    if not activity_id:
        return False
    
    schedule = getattr(app, 'schedule', [])
    for activity in schedule:
        if activity.get('id') == activity_id:
            return True
    
    return False


def truncate_text_to_width(text: str, font, max_width: int) -> str:
    """
    Truncate text to fit within max_width pixels, replacing overflow with '...'.
    
    Args:
        text: The text to truncate (can be multi-line)
        font: tkinter font object
        max_width: Maximum width in pixels
        
    Returns:
        Truncated text with '...' if needed
    """
    if max_width <= 0:
        return text
    
    # Handle multi-line text by processing each line separately
    lines = text.split('\n')
    truncated_lines = []
    
    for line in lines:
        # Measure the line width
        line_width = font.measure(line)
        
        if line_width <= max_width:
            # Line fits, keep as is
            truncated_lines.append(line)
        else:
            # Line doesn't fit, truncate with '...'
            ellipsis = '...'
            ellipsis_width = font.measure(ellipsis)
            
            # Binary search for the right length
            if ellipsis_width >= max_width:
                # Not even room for ellipsis
                truncated_lines.append(ellipsis)
            else:
                # Find how many characters fit
                available_width = max_width - ellipsis_width
                
                # Simple character-by-character truncation
                truncated = line
                for i in range(len(line), 0, -1):
                    test_text = line[:i]
                    if font.measure(test_text) <= available_width:
                        truncated = test_text + ellipsis
                        break
                else:
                    truncated = ellipsis
                
                truncated_lines.append(truncated)
    
    return '\n'.join(truncated_lines)


def update_ui(app):
    """
    Main UI update loop that refreshes all time-dependent UI elements.
    
    This function is the core of the UI update cycle. It:
    - Checks for day rollovers and handles schedule changes
    - Updates time display and current time line position
    - Manages activity notifications and status updates
    - Triggers timeline/card redraws when needed
    - Schedules the next update cycle
    
    Args:
        app: The main TimeboxApp instance containing all UI state and components
    """
    # Pause updates if day rollover dialog is being shown
    if getattr(app, '_day_rollover_dialog_active', False):
        app.after(UIConstants.UI_UPDATE_INTERVAL_MS, lambda: update_ui(app))
        return
    
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
        full_text = f"Actions:\n{desc}"
        
        # Truncate text to fit label width
        label_font = tkfont.Font(font=app.activity_label['font'])
        label_width = app.activity_label.winfo_width()
        # Account for padding and border (approx 10px on each side)
        available_width = max(label_width - 20, 50)
        truncated_text = truncate_text_to_width(full_text, label_font, available_width)
        
        app.activity_label.config(text=truncated_text)
        app._activity_label_full_text = full_text  # Store for resize
        # Activity change notifications are now handled by the notification service
        app.last_activity = activity
    else:
        # --- Show time till next task if no active task ---
        if next_task is None:
            full_text = "No scheduled task was found."
        else:
            seconds_left = int((next_task_start - now).total_seconds())
            if seconds_left < 0:
                # Handle over-midnight: add 24h
                seconds_left += 24*3600
            hours, remainder = divmod(seconds_left, 3600)
            minutes, seconds = divmod(remainder, 60)
            full_text = f"No active task\nNext: {next_task['name']} at {next_task['start_time']}\nTime left: {hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # Truncate text to fit label width
        label_font = tkfont.Font(font=app.activity_label['font'])
        label_width = app.activity_label.winfo_width()
        # Account for padding and border (approx 10px on each side)
        available_width = max(label_width - 20, 50)
        truncated_text = truncate_text_to_width(full_text, label_font, available_width)
        
        app.activity_label.config(text=truncated_text)
        app._activity_label_full_text = full_text  # Store for resize

    # Redraw timeline and cards if no action for threshold time or at the start of each minute
    if should_update:
        log_debug("Redrawing timeline and cards due to inactivity...")
        app.redraw_timeline_and_cards(app.winfo_width(), app.winfo_height())
        if app.card_visual_changed:
            app.restore_card_visuals()
            app.card_visual_changed = False
    else:
        _refresh_active_card_if_undone_tasks(app, activity)
        _refresh_missed_cards_with_undone_tasks(app, app.now_provider().time())

    # Store last update time for optimization
    app._last_ui_update = now
    
    # Update compact view if it's visible
    if hasattr(app, 'compact_view') and app.compact_view.is_visible:
        app.compact_view.update()
        
    app.after(UIConstants.UI_UPDATE_INTERVAL_MS, lambda: update_ui(app))

def _refresh_active_card_if_undone_tasks(app, activity):
    """
    Refresh only the currently active card to update visual indicators for undone tasks.
    
    This lightweight update is used to show the blinking tasks count indicator
    without redrawing the entire timeline. It finds the card corresponding to
    the active activity and updates only that card's visuals.
    
    Args:
        app: The main TimeboxApp instance
        activity: Dictionary containing the current activity data, or None if no active task
    """
    if not activity:
        return
    
    tasks = activity.get("tasks", [])
    if not tasks:
        return
    
    # Find the corresponding card object to check _tasks_done using ID-based matching
    activity_id = activity.get("id")
    
    # Skip if activity is not in current schedule
    if not _is_activity_in_schedule(app, activity_id):
        log_debug(f"Skipping refresh for activity '{activity.get('name')}' - not in current schedule")
        return
    
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

def _refresh_missed_cards_with_undone_tasks(app, now):
    """
    Refresh cards for activities that have finished but have undone tasks.
    
    This function checks all cards to find those where:
    - The activity's end time is before the current time (finished/past)
    - There are undone tasks remaining
    - The activity exists in the current schedule
    
    For such cards, it triggers a visual refresh to show the blinking red/black
    status indicator, alerting the user to missed tasks.
    
    Args:
        app: The main TimeboxApp instance
        now: Current time object
    """
    for card_obj in getattr(app, 'cards', []):
        activity_id = card_obj.activity.get('id')
        
        # Skip if activity is not in current schedule
        if not _is_activity_in_schedule(app, activity_id):
            log_debug(f"Skipping refresh for card '{card_obj.activity.get('name')}' - not in current schedule")
            continue
        
        tasks = card_obj.activity.get("tasks", [])
        if not tasks:
            continue
        
        # Check if card is finished (end time is before current time)
        from datetime import time
        end_time = time(card_obj.end_hour, card_obj.end_minute)
        if end_time > now:
            continue  # Card is not finished yet
        
        # Check if there are any undone tasks
        tasks_done = getattr(card_obj, '_tasks_done', [False] * len(tasks))
        if any(not done for done in tasks_done):
            log_debug(f"Refreshing missed card '{card_obj.activity.get('name')}' due to undone tasks")
            card_obj.update_card_visuals(
                card_obj.start_hour,
                card_obj.start_minute,
                app.start_hour,
                app.pixels_per_hour,
                app.offset_y,
                now=now,
                width=app.winfo_width()
            )

def _is_mouse_inside_window(app) -> bool:
    """
    Check if the mouse cursor is currently inside the application window boundaries.
    
    Used to prevent UI updates while the user is interacting with the window,
    which could interfere with mouse-based operations like dragging or clicking.
    
    Args:
        app: The main TimeboxApp instance
        
    Returns:
        bool: True if mouse is inside window boundaries, False otherwise or on error
    """
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
    """
    Determine if a full UI redraw is needed based on various conditions.
    
    This function implements the logic to minimize unnecessary UI redraws while
    ensuring the UI stays current. It checks multiple conditions:
    - First run (no previous update)
    - Mouse position (avoid interfering with user interaction)
    - Card visual changes
    - Active task progress (every 10 seconds)
    - Inactivity threshold (every 20 seconds)
    - Minute changes (to show active card transitions)
    
    Args:
        app: The main TimeboxApp instance
        now: Current datetime for comparison
        activity: Current activity dictionary, or None if no active task
        
    Returns:
        bool: True if full UI redraw should occur, False to skip redraw
    """
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
    
    # 5. When keeping current schedule, reload task states from database and refresh cards
    if not schedule_loaded:
        app._load_daily_task_entries()
        _refresh_all_cards(app, now)
    
    # 6. Update status bar to reflect new day statistics
    app.update_status_bar()
    
    log_info(f"Day rollover completed at {now.strftime('%H:%M:%S %Y-%m-%d')}")
    
    # Mark last action time to prevent immediate UI updates
    app.last_action = now


def _reset_timeline_to_top(app, now: datetime) -> None:
    """
    Reset timeline view to center on the current time for the new day.
    
    This function is called during day rollover to reposition the timeline
    so the current time is visible in the center of the window. Respects
    the 'disable_auto_centering' setting - if enabled, no repositioning occurs.
    
    Args:
        app: The main TimeboxApp instance
        now: Current datetime used to calculate the center position
    """
    try:
        # Only center if auto-centering is enabled (disable_auto_centering is False)
        if not getattr(app, 'disable_auto_centering', False):
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
        else:
            log_debug("Auto-centering disabled, skipping timeline reset on day rollover")
    except Exception as e:
        log_error(f"Failed to reset timeline to top: {e}")


def _reset_all_task_completion_status(app) -> None:
    """
    Reset all task completion status to undone for the new day.
    
    Iterates through all task cards and resets their _tasks_done arrays to False,
    then triggers visual updates to reflect the reset state. This gives users
    a fresh start for task tracking each day.
    
    Args:
        app: The main TimeboxApp instance containing the task cards to reset
    """
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


def _refresh_all_cards(app, now: datetime) -> None:
    """
    Refresh all card visuals to correctly mark them as new for the new day.
    
    This ensures that all activity cards have their visual state updated to reflect
    the new day's task tracking data loaded from the database. This is called when
    keeping the current schedule during day rollover to ensure cards show correct
    task completion indicators.
    
    Args:
        app: The main TimeboxApp instance containing the task cards to refresh
        now: Current datetime for visual calculations
    """
    try:
        current_time = now.time()
        for card_obj in getattr(app, 'cards', []):
            # Refresh card visuals with current task states
            card_obj.update_card_visuals(
                card_obj.start_hour,
                card_obj.start_minute,
                app.start_hour,
                app.pixels_per_hour,
                app.offset_y,
                now=current_time,
                width=app.winfo_width()
            )
        
        log_debug(f"Refreshed {len(app.cards)} cards for new day")
    except Exception as e:
        log_error(f"Failed to refresh cards for new day: {e}")


def _check_and_load_new_day_schedule(app, now: datetime) -> bool:
    """
    Check if a schedule file exists for the new day and ask user whether to load it.
    
    This function shows a modal dialog to ask the user if they want to load the new
    schedule or keep the current one. Timeline updates are paused during the dialog.
    
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
            
            # Get weekday name for display
            current_weekday = now.weekday()  # 0=Monday, 6=Sunday
            weekday_name = get_weekday_name(current_weekday)
            
            # Set flag to pause UI updates during dialog
            app._day_rollover_dialog_active = True
            
            try:
                # Show modal dialog and wait for user choice
                user_wants_new_schedule = show_day_rollover_dialog(
                    app, weekday_name, new_schedule_path
                )
                
                if user_wants_new_schedule:
                    log_info("User chose to load new schedule")
                    return _load_new_schedule_and_replace_cards(app, new_schedule_path)
                else:
                    log_info("User chose to keep current schedule")
                    return False
            finally:
                # Always clear the pause flag
                app._day_rollover_dialog_active = False
        else:
            log_debug(f"No specific schedule file found for new day, keeping current schedule")
            return False
            
    except Exception as e:
        log_error(f"Failed to check/load new day schedule: {e}")
        app._day_rollover_dialog_active = False  # Ensure flag is cleared on error
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
        
        # Save the loaded schedule path to settings
        app.last_schedule_path = os.path.abspath(schedule_path)
        app.save_settings(immediate=True)
        
        log_info(f"Successfully loaded new schedule from {schedule_path} with {len(new_schedule)} activities")
        return True
        
    except Exception as e:
        log_error(f"Failed to load new schedule from {schedule_path}: {e}")
        return False


def _create_new_day_task_entries(app) -> None:
    """
    Create new daily task tracking entries in the database for the new day.
    
    Uses the task tracking service to create database entries for all tasks
    in the current schedule. This enables completion tracking and statistics
    for the new day's activities.
    
    Args:
        app: The main TimeboxApp instance with task_tracking_service and schedule
    """
    try:
        if hasattr(app, 'task_tracking_service') and app.task_tracking_service:
            day_start = getattr(app, 'day_start', 0)
            entries_created = app.task_tracking_service.create_daily_task_entries(app.schedule, day_start_hour=day_start)
            if entries_created > 0:
                log_info(f"Created {entries_created} new task entries for new day")
        else:
            log_debug("No task tracking service available for creating new day entries")
    except Exception as e:
        log_error(f"Failed to create new day task entries: {e}")
