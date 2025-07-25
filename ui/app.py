import tkinter as tk, tkinter.messagebox as messagebox
from datetime import datetime
from typing import Dict, List
import yaml
import json
import os
import utils.notification
from constants import UIConstants

from ui.timeline import draw_timeline
from ui.task_card import create_task_cards, TaskCard
from utils.time_utils import parse_time_str
from datetime import datetime, timedelta, time
from utils.logging import log_debug
from ui.global_options import open_global_options
from ui.app_ui_events import on_motion, on_close, on_resize, on_mouse_wheel
from ui.app_ui_loop import update_ui
from ui.app_card_handling import on_card_press, on_card_drag, on_card_release, on_card_motion
from ui.schedule_management import open_schedule, save_schedule_as, save_schedule, clear_schedule
from ui.context_menu import show_canvas_context_menu
from ui.zoom_and_scroll import move_timelines_and_cards, poll_mouse

class TimeboxApp(tk.Tk):
    SETTINGS_PATH = os.path.expanduser("~/.tame_the_time_settings.json")

    def load_settings(self):
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
            "gotify_url": utils.notification.gotify_url
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

    def __init__(self, schedule: List[Dict], config_path: str, now_provider=datetime.now):
        super().__init__()
        self.now_provider = now_provider
        self.settings = self.load_settings()
        self.config_path = config_path
        self.schedule_changed = False

        now = now_provider().time()
        self.last_hour = now.hour
        self.last_minute = now.minute

        # Restore window position if available
        if "window_position" in self.settings:
            self.geometry(self.settings["window_position"])
        utils.notification.gotify_token = self.settings.get("gotify_token", "")
        utils.notification.gotify_url = self.settings.get("gotify_url", "")
        self.title("Timeboxing Timeline")
        self.geometry("400x700")
        self.schedule = schedule
        self.start_hour = 0
        self.end_hour = 24
        self.zoom_factor = 6.0
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        self.offset_y = 0
        self.cards = []  # List[TaskCard]
        self.timeline_1h_ids = []
        self.timeline_5m_ids = []
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        self._last_size = (self.winfo_width(), self.winfo_height())
        self.timeline_granularity = 60
        self.menu_hide_job = None
        self.last_action = datetime.now()
        self.last_activity = None  # Track last activity for notifications
        
        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=lambda: open_schedule(self))
        self.file_menu.add_command(label="Clear", command=lambda: clear_schedule(self))
        self.file_menu.add_command(label="Save", command=lambda: save_schedule(self))
        self.file_menu.add_command(label="Save As", command=lambda: save_schedule_as(self))
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Global options", command=lambda: open_global_options(self))
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.menu_visible = False
        self.card_visual_changed = False  # Flag to track if card visuals have changed

        self.status_bar = tk.Label(self, font=("Arial", 10), anchor="w", bg="#e0e0e0", relief="sunken", bd=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(self, bg="white", width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-4>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-5>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind("<Motion>", lambda event: on_motion(self, event))
        self.canvas.bind("<Button-3>", lambda event: show_canvas_context_menu(self, event))

        self.time_label = tk.Label(self, font=("Arial", 14, "bold"), bg="#0f8000")
        self.time_label.place(x=10, y=10)
        self.activity_label = tk.Label(self, font=("Arial", 12), anchor="w", justify="left", bg="#ffff99", relief="solid", bd=2)
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
        self.show_timeline(granularity=60)
        self.cards = self.create_task_cards()
        self.skip_redraw = False  # Allow redraws after initial setup
        update_ui(self)

        self.protocol("WM_DELETE_WINDOW", lambda: on_close(self))
        poll_mouse(self)

        self.update_status_bar()

    def create_timeline(self, granularity=60):
        now = self.now_provider().time()
        return draw_timeline(
            self.canvas, self.winfo_width(), self.start_hour, self.end_hour, self.pixels_per_hour, self.offset_y,
            current_time=now, granularity=granularity
        )

    def show_timeline(self, granularity=60):
        # Show only the timeline with the given granularity
        for tid in getattr(self, 'timeline_1h_ids', []):
            self.canvas.itemconfig(tid, state="normal" if granularity == 60 else "hidden")
        for tid in getattr(self, 'timeline_5m_ids', []):
            self.canvas.itemconfig(tid, state="normal" if granularity == 5 else "hidden")

    def scroll(self, event, delta: int):
        log_debug(f"Scrolling: {delta}, PPH: {self.pixels_per_hour}, Current Offset Y: {self.offset_y}")
        if self.pixels_per_hour > 50:
            scroll_step = -40 if delta > 0 else 40
            self.offset_y += scroll_step
            move_timelines_and_cards(self, scroll_step)
            self.last_action = datetime.now()

    def create_task_cards(self):
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
        # No deletion, just move/hide/show
        if center:
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
        for card_obj in self.cards:
            self.canvas.itemconfig(card_obj.card, stipple="")
            if card_obj.label:
                self.canvas.itemconfig(card_obj.label, fill="black")
            if hasattr(card_obj, 'progress'):
                self.canvas.itemconfig(card_obj.progress, state="normal")
                card_obj.setup_card_progress_actions(self.canvas)
        self.card_visual_changed = False

    def update_status_bar(self):
        today = self.now_provider().date()
        missed = 0
        done = 0
        incoming = 0
        now = self.now_provider()
        for card_obj in self.cards:
            activity = card_obj.activity
            start_time = parse_time_str(activity["start_time"])
            end_time = parse_time_str(activity["end_time"])
            start_dt = datetime.combine(today, start_time)
            end_dt = datetime.combine(today, end_time)
            # Check if task is for today
            if start_dt.date() != today:
                continue
            # Determine if done (all tasks done or card_obj._tasks_done is all True)
            if hasattr(card_obj, '_tasks_done') and card_obj._tasks_done:
                if all(card_obj._tasks_done):
                    done += 1
                elif end_dt < now:
                    missed += 1
                elif start_dt > now:
                    incoming += 1
                else:
                    # Ongoing but not done
                    pass
            else:
                if end_dt < now:
                    missed += 1
                elif start_dt > now:
                    incoming += 1
        self.status_bar.config(text=f"Tasks statistics for today - missed: {missed}, done: {done}, incoming: {incoming}")

    def update_cards_after_size_change(self):
        # Update all cards after window size change
        now = self.now_provider().time()
        for card_obj in self.cards:
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )
        #self.update_status_bar()

    def get_next_task_and_time(self, now):
        # Returns (next_task_dict, next_task_start_datetime)
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
        # Callback for when the edit window is cancelled
        log_debug(f"Edit cancelled for card: {card_obj.activity['name']}")
        # Optionally, you can remove the card if it was created in the edit window
        if card_obj in self.cards:
            card_obj.delete()
            self.cards.remove(card_obj)
            self.schedule.remove(card_obj.to_dict())
            self.update_cards_after_size_change()
    
    def find_activity_by_name(self, name):
        """Find a schedule item by its name."""
        for activity in self.schedule:
            if activity["name"] == name:
                return activity
        return None
    
    def normalize_tasks_done(self, card_obj):
        """Ensure that the _tasks_done list matches the number of tasks in the card's activity."""
        if not hasattr(card_obj, '_tasks_done') or card_obj._tasks_done is None:
            card_obj._tasks_done = [False] * len(card_obj.activity.get('tasks', []))
        else:
            tasks_length = len(card_obj.activity.get('tasks', []))
            tasks_done_length = len(card_obj._tasks_done)
            if tasks_done_length < tasks_length:
                card_obj._tasks_done.extend([False] * (tasks_length - tasks_done_length))
            elif tasks_done_length > tasks_length:
                card_obj._tasks_done = card_obj._tasks_done[:tasks_length]

    def bind_mouse_actions(self, card):
        # Bind mouse actions to the card
        tag = f"card_{card.card}"
        card._tasks_done_callback = self.update_status_bar
        self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda event: on_card_press(self, event))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda event: on_card_drag(self, event))
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: on_card_release(self, event))
        self.canvas.tag_bind(tag, "<Motion>", lambda event: on_card_motion(self, event))
            
