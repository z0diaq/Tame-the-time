import tkinter as tk, tkinter.messagebox as messagebox
from datetime import datetime
from typing import Dict, List
import yaml
import json
import os
import uuid
import utils.notification
from constants import UIConstants, Colors
import utils.notification
from services.notification_service import NotificationService
from utils.translator import init_translator, t

from ui.timeline import draw_timeline, draw_current_time_line, reposition_current_time_line
from ui.task_card import create_task_cards, TaskCard
from utils.time_utils import parse_time_str
from datetime import datetime, timedelta, time
from utils.logging import log_debug, log_info, log_error
from ui.global_options import open_global_options
from ui.app_ui_events import on_motion, on_close, on_resize, on_mouse_wheel
from ui.app_ui_loop import update_ui
from ui.app_card_handling import on_card_press, on_card_drag, on_card_release, on_card_motion
from ui.schedule_management import open_schedule, save_schedule_as, save_schedule, clear_schedule
from ui.context_menu import show_canvas_context_menu
from ui.zoom_and_scroll import move_timelines_and_cards, poll_mouse
from services.task_tracking_service import TaskTrackingService
from ui.statistics_dialog import open_task_statistics_dialog
from constants import NotificationConstants

class TimeboxApp(tk.Tk):
    SETTINGS_PATH = os.path.expanduser("~/.tame_the_time_settings.json")

    def load_settings(self):
        """Load settings from file."""
        if os.path.exists(self.SETTINGS_PATH):
            with open(self.SETTINGS_PATH, "r") as f:
                return json.load(f)
        return {}

    def save_settings(self, immediate=False):
        """Save settings with optional debouncing to prevent frequent file I/O."""
        if immediate:
            self._save_settings_immediate()
        else:
            self._schedule_settings_save()
    
    def _save_settings_immediate(self):
        """Immediately save settings to file."""
        settings = {
            "window_position": self.geometry(),
            "gotify_token": utils.notification.gotify_token,
            "gotify_url": utils.notification.gotify_url,
            "always_on_top": self.always_on_top,
            "advance_notification_enabled": getattr(self, 'advance_notification_enabled', True),
            "advance_notification_seconds": getattr(self, 'advance_notification_seconds', NotificationConstants.DEFAULT_ADVANCE_WARNING_SECONDS),
            "statistics_show_known_only": getattr(self, 'statistics_show_known_only', True ),
            "statistics_show_current_schedule_only": getattr(self, 'statistics_show_current_schedule_only', True),
            "current_language": getattr(self, 'current_language', 'en'),
            "day_start": getattr(self, 'day_start', 0),
            "disable_auto_centering": getattr(self, 'disable_auto_centering', False)
        }
        with open(self.SETTINGS_PATH, "w") as f:
            json.dump(settings, f)
    
    def _schedule_settings_save(self):
        """Schedule a debounced settings save operation."""
        # Cancel any existing save timer
        if hasattr(self, '_save_timer') and self._save_timer:
            self.after_cancel(self._save_timer)
        
        # Schedule new save operation
        self._save_timer = self.after(UIConstants.SETTINGS_SAVE_DEBOUNCE_MS, self._save_settings_immediate)

    def __init__(self, schedule: List[Dict], config_path: str, db_path: str = None, now_provider=datetime.now):
        """Initialize the application with the given schedule and configuration."""
        super().__init__()
        self.now_provider = now_provider
        self.settings = self.load_settings()
        self.config_path = config_path
        self.db_path = db_path
        self.schedule_changed = False
        
        # Initialize language from settings
        self.current_language = self.settings.get('current_language', 'en')
        init_translator(self.current_language)
        
        # Initialize advance notification settings from saved config
        self.advance_notification_enabled = self.settings.get('advance_notification_enabled', True)
        self.advance_notification_seconds = self.settings.get('advance_notification_seconds', NotificationConstants.DEFAULT_ADVANCE_WARNING_SECONDS)
        
        # Initialize notification service
        self.notification_service = NotificationService(now_provider, on_activity_change=self.update_status_bar)
        
        # Configure notification service with advance notification settings
        self.notification_service.set_advance_notification_settings(
            self.advance_notification_enabled, 
            self.advance_notification_seconds
        )
        
        # Initialize task tracking service
        self.task_tracking_service = TaskTrackingService(db_path)
        
        # Store schedule reference
        self.schedule = schedule
        
        # Ensure all activities have unique IDs (migrate existing data)
        self.ensure_activity_ids()
        
        # Ensure all tasks have UUIDs (migrate from string to object format)
        self.ensure_task_uuids()
        
        # Create daily task entries for today if needed
        self._ensure_daily_task_entries()

        now = now_provider().time()
        self.last_hour = now.hour
        self.last_minute = now.minute

        # Restore window position if available
        if "window_position" in self.settings:
            self.geometry(self.settings["window_position"])
        utils.notification.gotify_token = self.settings.get("gotify_token", "")
        utils.notification.gotify_url = self.settings.get("gotify_url", "")
        self.title(t("window.main_title"))
        self.geometry("400x700")
        # Initialize day_start from settings, default to 0 (midnight)
        self.day_start = self.settings.get("day_start", 0)
        # Maintain backward compatibility with start_hour/end_hour
        self.start_hour = self.day_start
        self.end_hour = (self.day_start + 24) % 24 if self.day_start != 0 else 24
        self.zoom_factor = 6.0
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        self.offset_y = 0
        self.cards = []  # List[TaskCard]
        self.timeline_1h_ids = []
        self.timeline_5m_ids = []
        self.current_time_ids = []
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        self._last_size = (self.winfo_width(), self.winfo_height())
        self.timeline_granularity = 60
        self.menu_hide_job = None
        self.last_action = datetime.now()
        self.last_activity = None  # Track last activity for notifications
        self.always_on_top = False  # Track always on top state
        
        # Load settings and apply always on top state
        settings = self.load_settings()
        self.always_on_top = settings.get("always_on_top", False)
        self.wm_attributes("-topmost", self.always_on_top)
        
        # Load disable_auto_centering setting (default: False = auto-centering enabled)
        self.disable_auto_centering = settings.get("disable_auto_centering", False)
        
        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label=t("menu.open"), command=lambda: open_schedule(self))
        self.file_menu.add_command(label=t("menu.clear"), command=lambda: clear_schedule(self))
        self.file_menu.add_command(label=t("menu.save"), command=lambda: save_schedule(self))
        self.file_menu.add_command(label=t("menu.save_as"), command=lambda: save_schedule_as(self))
        self.file_menu.add_separator()
        self.file_menu.add_checkbutton(label=t("menu.disable_auto_centering"), command=self.toggle_disable_auto_centering)
        self.menu_bar.add_cascade(label=t("menu.file"), menu=self.file_menu)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label=t("menu.global_options"), command=lambda: open_global_options(self))
        self.options_menu.add_separator()
        self.options_menu.add_checkbutton(label=t("menu.always_on_top"), command=self.toggle_always_on_top)
        self.menu_bar.add_cascade(label=t("menu.options"), menu=self.options_menu)
        
        # Add Statistics menu
        self.statistics_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.statistics_menu.add_command(label=t("menu.tasks"), command=lambda: open_task_statistics_dialog(self, self.db_path))
        self.menu_bar.add_cascade(label=t("menu.statistics"), menu=self.statistics_menu)
        
        # Configure the menu bar on the window
        self.config(menu=self.menu_bar)
        
        # Set initial checkbutton states based on loaded settings
        if self.always_on_top:
            self.options_menu.invoke(2)  # Index 2 is the always_on_top checkbutton
        if self.disable_auto_centering:
            self.file_menu.invoke(5)  # Index 5 is the disable_auto_centering checkbutton
        
        self.menu_visible = False
        self.statistics_show_known_only = settings.get("statistics_show_known_only", True)
        self.statistics_show_current_schedule_only = settings.get("statistics_show_current_schedule_only", True)
        self.card_visual_changed = False  # Flag to track if card visuals have changed

        self.status_bar = tk.Label(self, font=("Arial", 10), anchor="w", bg=Colors.STATUS_BAR_BG, fg=Colors.STATUS_BAR_TEXT, relief="sunken", bd=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self, bg=Colors.CANVAS_BG, width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-4>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-5>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind("<Motion>", lambda event: on_motion(self, event))
        self.canvas.bind("<Button-3>", lambda event: show_canvas_context_menu(self, event))

        self.time_label = tk.Label(self, font=("Arial", 14, "bold"), bg=Colors.TIME_LABEL_BG)
        self.time_label.place(x=10, y=10)
        self.activity_label = tk.Label(self, font=("Arial", 12), anchor="w", justify="left", bg=Colors.ACTIVITY_LABEL_BG, fg=Colors.ACTIVITY_LABEL_TEXT, relief="solid", bd=2)
        self.activity_label.place(x=10, y=40, width=380)
        
        self.bind("<Configure>", lambda event: on_resize(self, event))

        # Center view on current time
        now = self.now_provider().time()
        minutes_since_start = (now.hour - self.start_hour) * 60 + now.minute
        center_y = int(minutes_since_start * self.pixels_per_hour / 60) + 100
        
        # both these calls are needed to ensure the correct offset_y is calculated
        self.offset_y = (self.winfo_height() // 2) - center_y
        self.skip_redraw = True  # Skip initial redraw when computing window's size to avoid flickering
        self.update_idletasks()  # Ensure window size is correct before centering
        self.offset_y = (self.winfo_height() // 2) - center_y
        # --- Create both timelines and all cards only once ---
        self.timeline_1h_ids = self.create_timeline(granularity=60)
        self.timeline_5m_ids = self.create_timeline(granularity=5)
        self.current_time_ids = self.create_current_time_line()
        self.show_timeline(granularity=60)
        self.cards = self.create_task_cards()
        
        # Load task done states from database after cards are created
        self._load_daily_task_entries()
        
        self.skip_redraw = False  # Allow redraws after initial setup
        update_ui(self)

        self.protocol("WM_DELETE_WINDOW", lambda: on_close(self))
        poll_mouse(self)

        self.update_status_bar()

    def create_timeline(self, granularity=60):
        """Create timeline with the given granularity."""
        now = self.now_provider().time()
        return draw_timeline(
            self.canvas, self.winfo_width(), self.start_hour, self.end_hour, self.pixels_per_hour, self.offset_y,
            current_time=now, granularity=granularity
        )

    def create_current_time_line(self):
        """Create current time line visualization."""
        now = self.now_provider().time()
        mouse_inside = self._is_mouse_inside_window()
        return draw_current_time_line(
            self.canvas, self.winfo_width(), self.start_hour, self.pixels_per_hour, self.offset_y,
            current_time=now, mouse_inside_window=mouse_inside
        )

    def _is_mouse_inside_window(self):
        """Check if mouse is inside the window area."""
        try:
            mouse_x = self.winfo_pointerx()
            mouse_y = self.winfo_pointery()
            window_x = self.winfo_rootx()
            window_y = self.winfo_rooty()
            window_width = self.winfo_width()
            window_height = self.winfo_height()
            
            return (window_x <= mouse_x <= window_x + window_width and 
                    window_y <= mouse_y <= window_y + window_height)
        except Exception:
            return False

    def show_timeline(self, granularity=60):
        """Show only the timeline with the given granularity."""
        for tid in getattr(self, 'timeline_1h_ids', []):
            self.canvas.itemconfig(tid, state="normal" if granularity == 60 else "hidden")
        for tid in getattr(self, 'timeline_5m_ids', []):
            self.canvas.itemconfig(tid, state="normal" if granularity == 5 else "hidden")

    def scroll(self, event, delta: int):
        """Handle scroll events."""
        log_debug(f"Scrolling: {delta}, PPH: {self.pixels_per_hour}, Current Offset Y: {self.offset_y}")
        if self.pixels_per_hour > 50:
            scroll_step = -40 if delta > 0 else 40
            self.offset_y += scroll_step
            move_timelines_and_cards(self, scroll_step)
            self.last_action = datetime.now()

    def create_task_cards(self):
        """Create task cards from schedule."""
        cards = create_task_cards(
            self.canvas,
            self.schedule,
            self.start_hour,
            self.pixels_per_hour,
            self.offset_y,
            self.winfo_width(),
            now_provider=self.now_provider
        )
        for card_obj in cards:
            # Bind events to each card
            self.bind_mouse_actions(card_obj)
        return cards

    def redraw_timeline_and_cards(self, width: int, height: int, center: bool = True):
        """No deletion, just move/hide/show"""
        # Only center if auto-centering is enabled (disable_auto_centering is False)
        if center and not getattr(self, 'disable_auto_centering', False):
            now = self.now_provider().time()
            minutes_since_start = (now.hour - self.start_hour) * 60 + now.minute
            center_y = int(minutes_since_start * self.pixels_per_hour / 60) + 100
            new_offset = (height // 2) - center_y
            delta_y = new_offset - self.offset_y
            self.offset_y = new_offset
            move_timelines_and_cards(self, delta_y)
        # Show correct timeline granularity
        self.show_timeline(granularity=self.timeline_granularity)
        self.last_action = datetime.now()

    def restore_card_visuals(self):
        """Restore visuals of all cards after drag or resize."""
        now = self.now_provider().time()
        for card_obj in self.cards:
            self.canvas.itemconfig(card_obj.card, stipple="")
            if card_obj.label:
                self.canvas.itemconfig(card_obj.label, fill=Colors.CARD_LABEL_TEXT)
            card_obj.set_being_modified(False)
            
            # Immediately restore progress bar if card is currently active
            if card_obj.is_active_at(now):
                card_obj.update_card_visuals(
                    card_obj.start_hour, card_obj.start_minute, 
                    self.start_hour, self.pixels_per_hour, self.offset_y, 
                    now=now, width=self.winfo_width()
                )
        self.card_visual_changed = False

    def update_status_bar(self):
        """Update status bar with today's tasks statistics and unsaved task warnings"""
        # Check for unsaved tasks first
        has_unsaved_tasks = self._check_for_unsaved_tasks()
        
        # Calculate task statistics
        today = self.now_provider().date()
        missed = 0
        todo = 0
        active = 0
        done = 0
        incoming = 0
        now = self.now_provider()
        for card_obj in self.cards:
            activity = card_obj.activity
            if 'tasks' in activity:
                start_time = parse_time_str(activity["start_time"])
                end_time = parse_time_str(activity["end_time"])
                start_dt = datetime.combine(today, start_time)
                end_dt = datetime.combine(today, end_time)
                is_previous = end_dt < now
                is_current = start_dt <= now <= end_dt
                is_future = start_dt > now
                done_count = 0
                # Use _tasks_done if present, otherwise count all as not done
                tasks_done = getattr(card_obj, '_tasks_done', [False] * len(activity.get('tasks', [])))
                done_count = sum(tasks_done)
                missed_count = len(activity.get('tasks', [])) - done_count
                done += done_count
                if is_previous:
                    missed += missed_count
                elif is_future:
                    incoming += missed_count
                elif is_current:
                    active += missed_count
        
        # Build task statistics message
        tasks_info = t("status.no_tasks_today")
        if missed > 0 or todo > 0 or incoming > 0 or done > 0:
            tasks_info = t("status.today_statistics")
            if missed > 0:
                tasks_info += f"{missed} {t('status.missed')}, "
            if todo > 0:
                tasks_info += f"{todo} {t('status.todo')}, "
            if incoming > 0:
                tasks_info += f"{incoming} {t('status.incoming')}, "
            if active > 0:
                tasks_info += f"{active} {t('status.active')}, "
            if done > 0:
                tasks_info += f"{done} {t('status.done')}"
            tasks_info = tasks_info.rstrip(", ")
        
        # Display logic: show warning if unsaved tasks, otherwise show statistics
        log_debug(f"Status bar update: has_unsaved_tasks={has_unsaved_tasks}, tasks_info='{tasks_info}'")
        if has_unsaved_tasks:
            log_debug("Triggering unsaved task warning display")
            self._show_unsaved_task_warning(tasks_info)
        else:
            log_debug("No unsaved tasks, showing normal status bar")
            # Cancel any pending warning timers when no unsaved tasks
            if hasattr(self, '_warning_timer_id') and self._warning_timer_id:
                self.after_cancel(self._warning_timer_id)
                self._warning_timer_id = None
            if hasattr(self, '_normal_timer_id') and self._normal_timer_id:
                self.after_cancel(self._normal_timer_id)
                self._normal_timer_id = None
            self.status_bar.config(text=tasks_info, fg=Colors.STATUS_BAR_TEXT)
    
    def _check_for_unsaved_tasks(self) -> bool:
        """Check if there are any unsaved tasks in the current schedule"""
        if not hasattr(self, 'task_tracking_service') or not self.task_tracking_service:
            log_debug("No task tracking service available")
            return False
            
        unsaved_count = 0
        for card_obj in self.cards:
            activity = card_obj.activity
            if self.task_tracking_service.has_unsaved_tasks(activity):
                unsaved_tasks = self.task_tracking_service.get_unsaved_tasks(activity)
                log_debug(f"Activity '{activity.get('name', 'Unknown')}' has unsaved tasks: {unsaved_tasks}")
                unsaved_count += len(unsaved_tasks)
        
        has_unsaved = unsaved_count > 0
        log_debug(f"Total unsaved tasks found: {unsaved_count}, has_unsaved: {has_unsaved}")
        return has_unsaved
    
    def _show_unsaved_task_warning(self, normal_text: str):
        """Show red warning for 2 seconds, then return to normal text for 5 seconds"""
        log_debug(f"Starting unsaved task warning cycle with normal_text: '{normal_text}'")
        
        # Cancel any existing timers
        if hasattr(self, '_warning_timer_id') and self._warning_timer_id:
            self.after_cancel(self._warning_timer_id)
        if hasattr(self, '_normal_timer_id') and self._normal_timer_id:
            self.after_cancel(self._normal_timer_id)
        
        # Show normal text for 5 seconds
        self.status_bar.config(text=normal_text, fg=Colors.STATUS_BAR_TEXT)
        log_debug("Status bar set to normal text (black)")
        
        # After 5 seconds, show red warning for 2 seconds
        def show_warning():
            log_debug("Showing white text on red background warning message")
            self.status_bar.config(text=t("status.save_schedule_warning"), fg=Colors.STATUS_BAR_WARNING_TEXT, bg=Colors.STATUS_BAR_WARNING_BG)
            # After 2 seconds, return to normal text
            self._normal_timer_id = self.after(2000, lambda: self._return_to_normal(normal_text))
        
        self._warning_timer_id = self.after(5000, show_warning)
    
    def _return_to_normal(self, normal_text: str):
        """Return status bar to normal text and check if we need to continue cycling"""
        log_debug("Returning to normal text")
        self.status_bar.config(text=normal_text, fg=Colors.STATUS_BAR_TEXT, bg=Colors.STATUS_BAR_BG)
        
        # Check if we still have unsaved tasks and need to continue cycling
        if self._check_for_unsaved_tasks():
            log_debug("Still have unsaved tasks, continuing warning cycle")
            # Continue the cycle by calling the warning method again
            self._warning_timer_id = self.after(5000, lambda: self._show_red_warning(normal_text))
        else:
            log_debug("No more unsaved tasks, stopping warning cycle")
            self._warning_timer_id = None
            self._normal_timer_id = None
    
    def _show_red_warning(self, normal_text: str):
        """Show the red warning part of the cycle"""
        log_debug("Showing red warning message (cycle)")
        self.status_bar.config(text=t("status.save_schedule_warning"), fg=Colors.STATUS_BAR_WARNING_TEXT, bg=Colors.STATUS_BAR_WARNING_BG)
        # After 2 seconds, return to normal text
        self._normal_timer_id = self.after(2000, lambda: self._return_to_normal(normal_text))

    def update_cards_after_size_change(self):
        """Update all cards after window size change."""
        now = self.now_provider().time()
        for card_obj in self.cards:
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )
        #self.update_status_bar()

    def get_next_task_and_time(self, now):
        """Returns (next_task_dict, next_task_start_datetime)."""
        if not self.schedule or len(self.schedule) == 0:
            return None, None
        today = now.date()
        
        ''' Weekend handling
        # If weekend, find first task on Monday
        if now.weekday() >= 5:
            # Find next Monday
            days_ahead = 0 if now.weekday() == 0 else (7 - now.weekday())
            monday = today + timedelta(days=days_ahead)
            first = self.schedule[0]
            next_time = datetime.combine(monday, parse_time_str(first['start_time']))
            return first, next_time
        '''
        
        # Find next task after now
        for task in self.schedule:
            t = parse_time_str(task['start_time'])
            task_dt = datetime.combine(today, t)
            if task_dt > now:
                return task, task_dt
        # If none found, return first task of next day
        tomorrow = today + timedelta(days=1)
        first = self.schedule[0]
        next_time = datetime.combine(tomorrow, parse_time_str(first['start_time']))
        return first, next_time

    def on_cancel_callback(self, card_obj):
        """Callback for when the edit window is cancelled."""
        log_debug(f"Edit cancelled for card: {card_obj.activity['name']}")
        # Optionally, you can remove the card if it was created in the edit window
        if card_obj in self.cards:
            card_obj.delete()
            self.cards.remove(card_obj)
            self.schedule.remove(card_obj.to_dict())
            self.update_cards_after_size_change()
    
    def find_activity_by_id(self, activity_id):
        """Find a schedule item by its unique ID."""
        for activity in self.schedule:
            if activity.get("id") == activity_id:
                return activity
        return None
    
    def ensure_activity_ids(self):
        """Ensure all activities have unique IDs, generating them if missing."""
        for activity in self.schedule:
            if "id" not in activity or not activity["id"]:
                activity["id"] = str(uuid.uuid4())
                log_debug(f"Generated ID {activity['id']} for activity '{activity['name']}'")
    
    def ensure_task_uuids(self):
        """Ensure all tasks have UUIDs, migrating from string to object format if needed."""
        migration_needed = False
        
        for activity in self.schedule:
            if "tasks" in activity:
                tasks = activity["tasks"]
                for i, task in enumerate(tasks):
                    if isinstance(task, str):
                        # Convert string task to object with UUID
                        task_uuid = str(uuid.uuid4())
                        tasks[i] = {
                            "name": task,
                            "uuid": task_uuid
                        }
                        migration_needed = True
                        log_debug(f"Migrated task '{task}' to object format with UUID: {task_uuid}")
                    elif isinstance(task, dict) and "name" in task:
                        # Ensure UUID exists for object tasks
                        if "uuid" not in task:
                            task_uuid = str(uuid.uuid4())
                            task["uuid"] = task_uuid
                            migration_needed = True
                            log_debug(f"Added UUID to existing task object '{task['name']}': {task_uuid}")
        
        if migration_needed:
            self.schedule_changed = True
            log_info("Schedule migrated to include task UUIDs")
    
    def toggle_always_on_top(self):
        """Toggle the always on top state of the window."""
        self.always_on_top = not self.always_on_top
        self.wm_attributes("-topmost", self.always_on_top)
        log_debug(f"Always on top toggled to: {self.always_on_top}")
        # Save settings immediately when toggled
        self.save_settings(immediate=True)
    
    def toggle_disable_auto_centering(self):
        """Toggle the automatic centering of timeline on current time."""
        self.disable_auto_centering = not self.disable_auto_centering
        log_debug(f"Disable auto-centering toggled to: {self.disable_auto_centering}")
        # Save settings immediately when toggled
        self.save_settings(immediate=True)
    
    def generate_activity_id(self):
        """Generate a new unique activity ID."""
        return str(uuid.uuid4())
    
    def _ensure_daily_task_entries(self):
        """Ensure that task entries exist for today's tasks."""
        try:
            entries_created = self.task_tracking_service.create_daily_task_entries(self.schedule)
            if entries_created > 0:
                log_info(f"Created {entries_created} task entries for today")
        except Exception as e:
            log_error(f"Failed to create daily task entries: {e}")
    
    def _load_daily_task_entries(self):
        """Load task done states for current date from database."""
        try:
            # Get task done states from database for today (UUID -> bool mapping)
            done_states = self.task_tracking_service.get_task_done_states()
            
            if not done_states:
                log_debug("No task done states found in database for today")
                return
            
            # Update task cards with loaded done states
            for card_obj in self.cards:
                activity_id = card_obj.activity.get("id")
                if not activity_id:
                    log_debug(f"Activity '{card_obj.activity.get('name', 'Unknown')}' has no ID, skipping task loading")
                    continue
                    
                tasks = card_obj.activity.get("tasks", [])
                
                # Initialize _tasks_done if not present
                if not hasattr(card_obj, '_tasks_done') or card_obj._tasks_done is None:
                    card_obj._tasks_done = [False] * len(tasks)
                
                # Initialize _task_uuids to store UUID mappings for each task
                if not hasattr(card_obj, '_task_uuids') or card_obj._task_uuids is None:
                    card_obj._task_uuids = [None] * len(tasks)
                
                # Update done states from database using UUIDs
                for i, task in enumerate(tasks):
                    # Handle both string and object task formats
                    if isinstance(task, str):
                        task_name = task
                        task_uuid = None
                    elif isinstance(task, dict) and "name" in task:
                        task_name = task["name"]
                        task_uuid = task.get("uuid")
                    else:
                        log_error(f"Invalid task format: {task}")
                        continue
                    
                    # Use UUID from YAML if available, otherwise look up in database
                    if task_uuid:
                        # UUID available from YAML - use it directly
                        card_obj._task_uuids[i] = task_uuid
                        if task_uuid in done_states:
                            card_obj._tasks_done[i] = done_states[task_uuid]
                            log_debug(f"Loaded done state for '{task_name}' (UUID from YAML: {task_uuid}): {done_states[task_uuid]}")
                    else:
                        # No UUID in YAML - look up in database for backward compatibility
                        task_uuids = self.task_tracking_service.get_task_uuids_by_activity_and_name(activity_id, task_name)
                        
                        if task_uuids:
                            # Use the first UUID found (there should typically be only one per day)
                            task_uuid = task_uuids[0]
                            card_obj._task_uuids[i] = task_uuid
                            
                            if task_uuid in done_states:
                                card_obj._tasks_done[i] = done_states[task_uuid]
                                log_debug(f"Loaded done state for '{task_name}' (UUID from DB: {task_uuid}): {done_states[task_uuid]}")
            
            log_info(f"Loaded {len(done_states)} task done states from database")
            
        except Exception as e:
            log_error(f"Failed to load daily task entries: {e}")

    def normalize_tasks_done(self, card_obj):
        """Ensure that the _tasks_done and _task_uuids lists match the number of tasks in the card's activity."""
        tasks_length = len(card_obj.activity.get('tasks', []))
        
        # Normalize _tasks_done
        if not hasattr(card_obj, '_tasks_done') or card_obj._tasks_done is None:
            card_obj._tasks_done = [False] * tasks_length
        else:
            tasks_done_length = len(card_obj._tasks_done)
            if tasks_done_length < tasks_length:
                card_obj._tasks_done.extend([False] * (tasks_length - tasks_done_length))
            elif tasks_done_length > tasks_length:
                card_obj._tasks_done = card_obj._tasks_done[:tasks_length]
        
        # Normalize _task_uuids
        if not hasattr(card_obj, '_task_uuids') or card_obj._task_uuids is None:
            card_obj._task_uuids = [None] * tasks_length
        else:
            task_uuids_length = len(card_obj._task_uuids)
            if task_uuids_length < tasks_length:
                card_obj._task_uuids.extend([None] * (tasks_length - task_uuids_length))
            elif task_uuids_length > tasks_length:
                card_obj._task_uuids = card_obj._task_uuids[:tasks_length]

    def refresh_ui_after_language_change(self):
        """Refresh all UI elements after language change."""
        # Update window title
        self.title(t("window.main_title"))
        
        # Update file menu items
        self.file_menu.entryconfig(0, label=t("menu.open"))
        self.file_menu.entryconfig(1, label=t("menu.clear"))
        self.file_menu.entryconfig(2, label=t("menu.save"))
        self.file_menu.entryconfig(3, label=t("menu.save_as"))
        # Index 4 is separator
        self.file_menu.entryconfig(5, label=t("menu.disable_auto_centering"))
        
        # Update options menu items
        self.options_menu.entryconfig(0, label=t("menu.global_options"))
        self.options_menu.entryconfig(2, label=t("menu.always_on_top"))
        
        # Update statistics menu items
        self.statistics_menu.entryconfig(0, label=t("menu.tasks"))
        
        # Update menu bar cascade labels by recreating them
        # Remove existing cascades and recreate with new labels
        self.menu_bar.delete(0, "end")
        self.menu_bar.add_cascade(label=t("menu.file"), menu=self.file_menu)
        self.menu_bar.add_cascade(label=t("menu.options"), menu=self.options_menu)
        self.menu_bar.add_cascade(label=t("menu.statistics"), menu=self.statistics_menu)
        
        # Update status bar
        self.update_status_bar()
        
        # Save language preference
        self.save_settings(immediate=True)

    def bind_mouse_actions(self, card):
        """Bind mouse actions to the card."""
        tag = f"card_{card.card}"
        card._tasks_done_callback = self.update_status_bar
        self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda event: on_card_press(self, event))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda event: on_card_drag(self, event))
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: on_card_release(self, event))
        self.canvas.tag_bind(tag, "<Motion>", lambda event: on_card_motion(self, event))
            
