import tkinter as tk, tkinter.messagebox as messagebox
from datetime import datetime
from typing import Dict, List
import yaml
import json
import os
import utils.notification

from ui.timeline import draw_timeline, reposition_timeline
from ui.task_card import create_task_cards, TaskCard
from utils.time_utils import get_current_activity, round_to_nearest_5_minutes, parse_time_str
from datetime import datetime, timedelta, time
from utils.logging import log_debug, log_info, log_error
from ui.global_options import open_global_options
from ui.card_dialogs import open_edit_card_window, open_card_tasks_window
from ui.app_ui_events import hide_menu_bar, on_motion, on_close, on_resize, on_mouse_wheel
from ui.app_ui_loop import update_ui
from ui.app_card_handling import on_card_press, on_card_drag, on_card_release, on_card_motion

class TimeboxApp(tk.Tk):
    SETTINGS_PATH = os.path.expanduser("~/.tame_the_time_settings.json")

    def load_settings(self):
        if os.path.exists(self.SETTINGS_PATH):
            with open(self.SETTINGS_PATH, "r") as f:
                return json.load(f)
        return {}

    def save_settings(self):
        settings = {
            "window_position": self.geometry(),
            "gotify_token": utils.notification.gotify_token,
            "gotify_url": utils.notification.gotify_url
        }
        with open(self.SETTINGS_PATH, "w") as f:
            json.dump(settings, f)

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
        self.file_menu.add_command(label="Open", command=self.open_schedule)
        self.file_menu.add_command(label="Clear", command=self.clear_schedule)
        self.file_menu.add_command(label="Save", command=self.save_schedule)
        self.file_menu.add_command(label="Save As", command=self.save_schedule_as)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Global options", command=lambda: open_global_options(self))
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.menu_visible = False
        self.card_visual_changed = False  # Flag to track if card visuals have changed

        self.canvas = tk.Canvas(self, bg="white", width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-4>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind('<Button-5>', lambda event: on_mouse_wheel(self, event))
        self.canvas.bind("<Motion>", lambda event: on_motion(self, event))
        self.canvas.bind("<Button-3>", self.show_canvas_context_menu)

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
        self.poll_mouse()

    def open_schedule(self):
        from tkinter import filedialog
        import yaml
        file_path = filedialog.askopenfilename(
            title="Open Schedule File",
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                new_schedule = yaml.safe_load(f)
            self.config_path = file_path  # Update config path to the new file
            # Remove all current cards from canvas
            for card_obj in self.cards:
                card_obj.delete()
            self.cards.clear()
            self.schedule.clear()
            # Load new schedule
            self.schedule.extend(new_schedule)
            self.cards = self.create_task_cards()
            self.update_cards_after_size_change()
            self.last_action = datetime.now()
            log_info(f"Loaded schedule from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")
            log_error(f"Failed to load file: {e}")

    def save_schedule_as(self):
        import calendar
        from tkinter import filedialog
        # Suggest filename based on current week day
        today = self.now_provider().date()
        weekday_name = calendar.day_name[today.weekday()]
        filename = f"{weekday_name}_settings.yaml"
        file_path = filedialog.asksaveasfilename(
            title="Save Schedule As",
            defaultextension=".yaml",
            initialfile=filename,
            filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w') as f:
                yaml.safe_dump(self.schedule, f)
            messagebox.showinfo("Saved", f"Schedule saved to {file_path}")
            log_info(f"Schedule saved to {file_path}")
            self.config_path = file_path  # Update config path to the new file
            self.schedule_changed = False # Reset schedule changed flag
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
            log_error(f"Failed to save file: {e}")
    
    def save_schedule(self, ask_for_confirmation: bool = True):
        """Save current schedule to the default JSON file."""
        # Ask for confirmation if file exists
        if ask_for_confirmation and os.path.exists(self.SETTINGS_PATH):
            if not messagebox.askyesno("Confirm", "Schedule file already exists. Do you want to overwrite it?"):
                return
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.safe_dump(self.schedule, f)
            if ask_for_confirmation:
                messagebox.showinfo("Saved", f"Schedule saved to {self.config_path}")
            log_info(f"Schedule saved to {self.config_path}")
            self.schedule_changed = False  # Reset schedule changed flag
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")
            log_error(f"Failed to save file: {e}")

    def clear_schedule(self):
        """Clear all cards and schedule, with confirmation if there are unsaved changes."""
        if self.schedule_changed:
            if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to close and lose them?"):
                return
        for card_obj in self.cards:
            card_obj.delete()
        self.cards.clear()
        self.schedule.clear()
        self.schedule_changed = False
        self.update_cards_after_size_change()

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

    def move_timelines_and_cards(self, delta_y):
        # Move both timelines and all cards by delta_y
        for tid in getattr(self, 'timeline_1h_ids', []):
            self.canvas.move(tid, 0, delta_y)
        for tid in getattr(self, 'timeline_5m_ids', []):
            self.canvas.move(tid, 0, delta_y)
        now = self.now_provider().time()
        # Move all cards
        for card_obj in self.cards:
            card_obj.y += delta_y
            for cid in [card_obj.card, card_obj.label]:
                if cid:
                    self.canvas.move(cid, 0, delta_y)
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )
    
    def is_mouse_in_window(self):
        x, y = self.winfo_pointerx(), self.winfo_pointery()
        x0, y0 = self.winfo_rootx(), self.winfo_rooty()
        x1, y1 = x0 + self.winfo_width(), y0 + self.winfo_height()

        # If menu is visible, extend the top boundary upward
        menu_bar_height = 30 if self.menu_visible else 0  # Adjust if your menu is taller/shorter
        y0 -= menu_bar_height
        return x0 <= x <= x1 and y0 <= y <= y1

    def poll_mouse(self):
        if self.menu_visible and not self.is_mouse_in_window():
            # Mouse is outside the window, hide menu bar or take action
            hide_menu_bar(self)
        self.after(200, self.poll_mouse)  # Check every 200ms

    def zoom(self, event, delta: int):
        zoom_step = 0.1
        a = self.zoom_factor + (-zoom_step if delta > 0 else zoom_step)
        self.zoom_factor = max(0.5, min(6, a))
        old_pph = self.pixels_per_hour
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        mouse_y = event.y
        rel_y = mouse_y - 100 - self.offset_y
        scale = self.pixels_per_hour / old_pph
        self.offset_y = min(100, int(mouse_y - 100 - rel_y * scale))
        self.resize_timelines_and_cards()
        self.last_action = datetime.now()

    def resize_timelines_and_cards(self):
        log_debug(f"Resizing timelines and cards, new PPH: {self.pixels_per_hour}, Offset Y: {self.offset_y}")
        # Resize all cards
        now = self.now_provider().time()
        for card_obj in self.cards:
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )
        # Update both timelines
        reposition_timeline(self.canvas, self.timeline_1h_ids, self.pixels_per_hour, self.offset_y, self.winfo_width(), granularity=60)
        reposition_timeline(self.canvas, self.timeline_5m_ids, self.pixels_per_hour, self.offset_y, self.winfo_width(), granularity=5)

        # Also resize activity label
        self.activity_label.place(x=10, y=40, width=self.winfo_width() - 20)

    def scroll(self, event, delta: int):
        log_debug(f"Scrolling: {delta}, PPH: {self.pixels_per_hour}, Current Offset Y: {self.offset_y}")
        if self.pixels_per_hour > 50:
            scroll_step = -40 if delta > 0 else 40
            self.offset_y += scroll_step
            self.move_timelines_and_cards(scroll_step)
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
            self.move_timelines_and_cards(delta_y)
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
        self.card_visual_changed = False

    def update_cards_after_size_change(self):
        # Update all cards after window size change
        now = self.now_provider().time()
        for card_obj in self.cards:
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )

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

    
    def show_canvas_context_menu(self, event):
        # Determine if click is on a card
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        card_ids = [card_obj.card for card_obj in self.cards]
        log_debug(f"Context menu requested at {event.x}, {event.y}, items: {items}, card_ids: {card_ids}")
        menu = tk.Menu(self, tearoff=0)
        card_under_cursor = None
        for card_obj in self.cards:
            if card_obj.card in items:
                card_under_cursor = card_obj
                break
        if card_under_cursor:
            # Show context menu for the card under cursor
            def edit_card():
                open_edit_card_window(self, card_under_cursor)
            menu.add_command(label="Edit", command=edit_card)
            def clone_card():
                # Clone the card under cursor
                # Card's text labels have to be created separately
                new_card = card_under_cursor.clone()
                # New start time is at current card's end time exctly
                new_card.start_hour = card_under_cursor.end_hour
                new_card.start_minute = card_under_cursor.end_minute
                # Card's end time is set to start time + length of original card
                current_card_length = (card_under_cursor.end_hour - card_under_cursor.start_hour) * 60 + (card_under_cursor.end_minute - card_under_cursor.start_minute)
                new_card.end_hour = (new_card.start_hour + (current_card_length // 60)) % 24
                new_card.end_minute = (new_card.start_minute + current_card_length) % 60

                # Is there any card starting at the same time as the new card ends ?
                draw_end_time = True
                for other_card in self.cards:
                    if (other_card.start_hour == new_card.end_hour and
                        other_card.start_minute == new_card.end_minute):
                        draw_end_time = False
                        break
                new_card.draw(canvas=self.canvas, now=self.now_provider().time(), draw_end_time=draw_end_time)
                self.bind_mouse_actions(new_card)
                self.cards.append(new_card)
                self.schedule.append(new_card.to_dict())
                self.update_cards_after_size_change()
                self.schedule_changed = True  # Mark schedule as changed
            menu.add_command(label="Clone", command=clone_card)
            def remove_card():
                # Remove the card under cursor
                if card_under_cursor in self.cards:
                    self.cards.remove(card_under_cursor)
                    card_under_cursor.delete()
                    self.schedule.remove(card_under_cursor.to_dict())
                    self.update_cards_after_size_change()
                    self.schedule_changed = True  # Mark schedule as changed
            menu.add_command(label="Remove", command=remove_card)
            def open_card_tasks():
                # Open tasks window for the card
                open_card_tasks_window(self, card_under_cursor)
            activity = self.find_activity_by_name(card_under_cursor.activity["name"])
            if 'tasks' in activity and activity['tasks']:
                menu.add_command(label="Tasks", command=open_card_tasks)
        elif event.y > 30:  # Not in top menu area
            def add_card():
                # Create a new card at the clicked position
                # Compute the start hour based on the clicked position
                y_relative = event.y - 100 - self.offset_y
                total_minutes = round_to_nearest_5_minutes(y_relative * 60 / self.pixels_per_hour)
                start_hour = self.start_hour + total_minutes // 60
                start_minute = total_minutes % 60
                total_minutes += 25
                end_hour = self.start_hour + total_minutes // 60
                end_minute = total_minutes % 60

                # Create a dict with default values for the new card
                activity = {
                    "name": "New Task",
                    "description": [],
                    "start_time": f"{start_hour:02d}:{start_minute:02d}",
                    "end_time": f"{end_hour:02d}:{end_minute:02d}"
                }

                new_card = TaskCard(
                    activity=activity,
                    start_of_workday=self.start_hour,
                    pixels_per_hour=self.pixels_per_hour,
                    offset_y=self.offset_y,
                    width=self.winfo_width(),
                    now_provider=self.now_provider
                )
                new_card.draw(canvas=self.canvas, draw_end_time=True)
                self.bind_mouse_actions(new_card)
                self.cards.append(new_card)
                self.schedule.append(new_card.to_dict())
                self.update_cards_after_size_change()
                open_edit_card_window(self, new_card)
                self.schedule_changed = True  # Mark schedule as changed

            menu.add_command(label="New", command=add_card)
            def remove_all_cards():
                # Ask for confirmation before removing all cards
                if messagebox.askyesno("Confirm", "Are you sure you want to remove all cards?"):
                    for card_obj in self.cards:
                        card_obj.delete()
                    self.cards.clear()
                    self.schedule.clear()
                    self.schedule_changed = True  # Mark schedule as changed
            menu.add_command(label="Remove all", command=remove_all_cards)
        else:
            return  # Don't show menu in top menu area
        menu.tk_popup(event.x_root, event.y_root)

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
        self.canvas.tag_bind(tag, "<ButtonPress-1>", lambda event: on_card_press(self, event))
        self.canvas.tag_bind(tag, "<B1-Motion>", lambda event: on_card_drag(self, event))
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", lambda event: on_card_release(self, event))
        self.canvas.tag_bind(tag, "<Motion>", lambda event: on_card_motion(self, event))
