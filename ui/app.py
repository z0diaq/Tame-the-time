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

last_activity = None  # Global variable to track the last activity for notifications
allow_notification = True

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
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Button-3>", self.show_canvas_context_menu)

        self.time_label = tk.Label(self, font=("Arial", 14, "bold"), bg="#0f8000")
        self.time_label.place(x=10, y=10)
        self.activity_label = tk.Label(self, font=("Arial", 12), anchor="w", justify="left", bg="#ffff99", relief="solid", bd=2)
        self.activity_label.place(x=10, y=40, width=380)
        
        self.bind("<Configure>", self.on_resize)

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
        self.update_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
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

    def on_close(self):
        self.save_settings()
        if self.schedule_changed:
            if messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to save them?"):
                self.save_schedule(ask_for_confirmation=False)
        self.destroy()

    def on_resize(self, event):
        if event.widget == self:
            width, height = event.width, event.height
            last_width, last_height = self._last_size
            if any(abs(d) >= 10 for d in [width - last_width, height - last_height]):
                self._last_size = (width, height)
                self.canvas.config(width=width, height=height)
                if not self.skip_redraw:
                    self.resize_timelines_and_cards()

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

    def on_mouse_wheel(self, event):
        ctrl_held = (event.state & 0x0004) != 0
        log_debug(f"Mouse Wheel Event: {event.num}, Delta: {event.delta}, Ctrl Held: {ctrl_held}")
        delta = 0
        if event.num == 4 or event.delta > 0:  # Scroll up
            delta = -1
        elif event.num == 5 or event.delta < 0:  # Scroll down
            delta = 1
        
        if ctrl_held:
            self.zoom(event, delta)
        else:
            self.scroll(event, delta)
    
    def show_menu_bar(self):
        if not self.menu_visible:
            self.config(menu=self.menu_bar)
            self.menu_visible = True
        if self.menu_hide_job:
            self.after_cancel(self.menu_hide_job)
            self.menu_hide_job = None

    def hide_menu_bar(self):
        self.config(menu="")
        self.menu_visible = False
        self.menu_hide_job = None

    def on_motion(self, event):
        # Show menu bar if mouse is near the top of the canvas
        if event.y < 30:
            self.show_menu_bar()
        else:
            if self.menu_visible and not self.menu_hide_job:
                self.menu_hide_job = self.after(500, self.hide_menu_bar)
        # Reset mouse cursor if not hovering over a card
        items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        card_ids = [card_obj.card for card_obj in self.cards]
        if not any(item in card_ids for item in items):
            self.config(cursor="")

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
            self.hide_menu_bar()
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

    def on_card_press(self, event):
        tags = self.canvas.gettags(tk.CURRENT)
        log_debug(f"Card pressed: {tags}")
        self._drag_data["item_ids"] = self.canvas.find_withtag(tags[0])
        self._drag_data["offset_y"] = event.y
        self._drag_data["start_y"] = event.y
        self._drag_data["dragging"] = False
        self._drag_data["resize_mode"] = None
        dragged_id = self._drag_data["item_ids"][0]
        y_card_top = self.canvas.coords(dragged_id)[1]
        self._drag_data["diff_y"] = event.y - y_card_top
        log_debug(f"Dragging card: {dragged_id}, Tags: {tags}")
        # Detect if click is near top or bottom for resize
        y_card_top = self.canvas.coords(dragged_id)[1]
        y_card_bottom = self.canvas.coords(dragged_id)[3]
        if abs(event.y - y_card_top) <= 10:
            self.config(cursor="top_side")
            self._drag_data["resize_mode"] = "top"
        elif abs(event.y - y_card_bottom) <= 10:
            self.config(cursor="bottom_side")
            self._drag_data["resize_mode"] = "bottom"
        else:
            self.config(cursor="fleur")
            self._drag_data["resize_mode"] = None
        # Make all other cards barely visible
        for card_obj in self.cards:
            if card_obj.card != dragged_id:
                self.canvas.itemconfig(card_obj.card, stipple="gray25")
                if card_obj.label:
                    self.canvas.itemconfig(card_obj.label, fill="#cccccc")
            else:
                self.canvas.itemconfig(card_obj.card, stipple="")
                card_obj.set_being_modified(True)
                if card_obj.label:
                    self.canvas.itemconfig(card_obj.label, fill="black")
        self.card_visual_changed = True
        if self.timeline_granularity != 5:
            self.timeline_granularity = 5
            self.show_timeline(granularity=5)

    def restore_card_visuals(self):
        """Restore visuals of all cards after drag or resize."""
        for card_obj in self.cards:
            self.canvas.itemconfig(card_obj.card, stipple="")
            if card_obj.label:
                self.canvas.itemconfig(card_obj.label, fill="black")
            if hasattr(card_obj, 'progress'):
                self.canvas.itemconfig(card_obj.progress, state="normal")
        self.card_visual_changed = False

    def on_card_drag(self, event):
        if not self._drag_data["item_ids"] or abs(event.y - self._drag_data["start_y"]) <= 20:
            return
        
        self.last_action = datetime.now()
        self._drag_data["dragging"] = True
        dragged_id = self._drag_data["item_ids"][0]
        self.schedule_changed = True  # Mark schedule as changed
        if self._drag_data.get("resize_mode") == "top":
            # Resize from top
            y_card_bottom = self.canvas.coords(dragged_id)[3]
            new_top = min(event.y, y_card_bottom - 20)
            snapped_minutes = round_to_nearest_5_minutes(int((new_top - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            self.canvas.coords(dragged_id, self.canvas.coords(dragged_id)[0], snapped_y, self.canvas.coords(dragged_id)[2], y_card_bottom)
        elif self._drag_data.get("resize_mode") == "bottom":
            # Resize from bottom
            y_card_top = self.canvas.coords(dragged_id)[1]
            new_bottom = max(event.y, y_card_top + 20)
            snapped_minutes = round_to_nearest_5_minutes(int((new_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            self.canvas.coords(dragged_id, self.canvas.coords(dragged_id)[0], y_card_top, self.canvas.coords(dragged_id)[2], snapped_y)
        else:
            # Normal drag (move)
            y = event.y
            y_relative = y - 100 - self.offset_y - self._drag_data["diff_y"]
            total_minutes = int(y_relative * 60 / self.pixels_per_hour)
            snapped_minutes = round_to_nearest_5_minutes(total_minutes)
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            delta_y = snapped_y - self.canvas.coords(dragged_id)[1]
            log_debug(f"Item_ids: {self._drag_data['item_ids']}")
            for item_id in self._drag_data["item_ids"]:
                self.canvas.move(item_id, 0, delta_y)
            self._drag_data["offset_y"] = event.y + (snapped_y - y)

    def on_card_release(self, event):
        self.config(cursor="")
        if not self._drag_data["item_ids"] or not self._drag_data["dragging"]:
            self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
            self.timeline_granularity = 60
            self.show_timeline(granularity=60)
            return
        card_id = self._drag_data["item_ids"][0]
        if self._drag_data.get("resize_mode"):
            self.handle_card_resize(card_id, event.y, self._drag_data["resize_mode"])
        else:
            self.handle_card_snap(card_id, event.y)
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        self.timeline_granularity = 60
        self.restore_card_visuals()
        self.show_timeline(granularity=60)

    def handle_card_snap(self, card_id: int, y: int):
        moved_card = next(card for card in self.cards if card.card == card_id)
        log_debug(f"Moved card: {moved_card.card}")
        y_relative = y - 100 - self.offset_y - self._drag_data["diff_y"]
        total_minutes = round_to_nearest_5_minutes(int(y_relative * 60 / self.pixels_per_hour))
        new_hour = self.start_hour + total_minutes // 60
        new_minute = total_minutes % 60
        log_debug(f"Moving card {moved_card.activity['name']} to {new_hour:02d}:{new_minute:02d}")
        idx = self.cards.index(moved_card)
        # End time label is allowed if there is a gap to the next card
        allow_end_time_label = True
        if idx < len(self.cards) - 1:
            next_card = self.cards[idx + 1]
            if next_card.start_hour == moved_card.end_hour and next_card.start_minute == moved_card.end_minute:
                allow_end_time_label = False
        now = self.now_provider().time()
        self.cards[idx].update_card_visuals(
            new_hour, new_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, show_end_time=allow_end_time_label, width=self.winfo_width()
        )
        self.schedule[idx] = self.cards[idx].to_dict()  # Update schedule with new time

    def handle_card_resize(self, card_id: int, y: int, mode: str):
        moved_card = next(card for card in self.cards if card.card == card_id)
        y_card_top = self.canvas.coords(card_id)[1]
        y_card_bottom = self.canvas.coords(card_id)[3]
        if mode == "top":
            new_top = min(y, y_card_bottom - 20)
            snapped_minutes = round_to_nearest_5_minutes(int((new_top - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            new_start_minutes = snapped_minutes
            new_end_minutes = int((y_card_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour)
        else:
            new_top = y_card_top
            new_bottom = max(y, y_card_top + 20)
            snapped_minutes = round_to_nearest_5_minutes(int((new_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            new_start_minutes = int((y_card_top - 100 - self.offset_y) * 60 / self.pixels_per_hour)
            new_end_minutes = snapped_minutes
        new_start_hour = self.start_hour + new_start_minutes // 60
        new_start_minute = new_start_minutes % 60
        new_end_hour = self.start_hour + new_end_minutes // 60
        new_end_minute = new_end_minutes % 60
        # Update schedule for this card only
        for activity in self.schedule:
            if activity["name"] == moved_card.activity["name"]:
                activity["start_time"] = f"{new_start_hour:02d}:{new_start_minute:02d}"
                activity["end_time"] = f"{new_end_hour:02d}:{new_end_minute:02d}"
                break
        # End time label is allowed if there is a gap to the next card
        allow_end_time_label = True
        idx = self.cards.index(moved_card)
        if idx < len(self.cards) - 1:
            next_card = self.cards[idx + 1]
            if next_card.start_hour == new_end_hour and next_card.start_minute == new_end_minute:
                allow_end_time_label = False
        now = self.now_provider().time()
        # Update the card's start and end time attributes before calling update_card_visuals
        moved_card.start_hour = new_start_hour
        moved_card.start_minute = new_start_minute
        moved_card.end_hour = new_end_hour
        moved_card.end_minute = new_end_minute
        moved_card.update_card_visuals(
            new_start_hour, new_start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, show_end_time=allow_end_time_label, width=self.winfo_width()
        )

    def update_cards_after_size_change(self):
        # Update all cards after window size change
        now = self.now_provider().time()
        for card_obj in self.cards:
            card_obj.update_card_visuals(
                card_obj.start_hour, card_obj.start_minute, self.start_hour, self.pixels_per_hour, self.offset_y, now=now, width=self.winfo_width()
            )

    def update_ui(self):
        global last_activity
        now = self.now_provider()
        self.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
        activity = get_current_activity(self.schedule, now)
        next_task, next_task_start = self.get_next_task_and_time(now)
        # --- 30 seconds before next task notification ---
        if allow_notification and next_task and 0 <= (next_task_start - now).total_seconds() <= 30:
            if not hasattr(self, '_notified_next_task') or self._notified_next_task != next_task['name']:
                utils.notification.send_gotify_notification({
                    'name': f"30 seconds to start {next_task['name']}",
                    'description': [f"{next_task['name']} starts at {next_task['start_time']}"]
                }, is_delayed=True)
                self._notified_next_task = next_task['name']
        elif hasattr(self, '_notified_next_task') and (not next_task or (next_task_start - now).total_seconds() > 30 or (next_task_start - now).total_seconds() < 0):
            self._notified_next_task = None
        # --- UI update logic ---
        if activity:
            desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(activity["description"]))
            self.activity_label.config(
                text=f"Actions:\n{desc}"
            )
            # Send notification if activity changed and notifications are allowed
            if (last_activity is None or last_activity["name"] != activity["name"]) and allow_notification:
                utils.notification.send_gotify_notification(activity)
                log_debug(f"Notification sent for activity: {activity['name']}")
            last_activity = activity
        else:
            # --- Show time till next task if no active task ---
            
            ''' Weekend handling
            if now.weekday() >= 5:
                text = "WEEKEND\nEnjoy your time off!\nSchedule resumes Monday 8:00 AM."
            el'''
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
            self.activity_label.config(text=text)
        # Redraw everything every 20 seconds
        seconds_since_last_action = (datetime.now() - self.last_action).total_seconds()

        # Redraw timeline and cards if no action for 20 seconds or at the start of each minute
        if seconds_since_last_action >= 20 or (now.second == 0 and seconds_since_last_action > 5):
            #self.config(cursor="")
            log_debug("Redrawing timeline and cards due to inactivity...")
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height())
            if self.card_visual_changed:
                self.restore_card_visuals()

        self.after(1000, self.update_ui)

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

    def on_card_motion(self, event):
        tags = self.canvas.gettags(tk.CURRENT)
        log_debug(f"Tags = {tags}")
        if not tags:
            self.config(cursor="")
            return
        dragged_id = self.canvas.find_withtag(tags[0])[0]
        y_card_top = self.canvas.coords(dragged_id)[1]
        y_card_bottom = self.canvas.coords(dragged_id)[3]
        if abs(event.y - y_card_top) <= 8:
            self.config(cursor="top_side")
        elif abs(event.y - y_card_bottom) <= 8:
            self.config(cursor="bottom_side")
        else:
            self.config(cursor="fleur")
    
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
        self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_card_press)
        self.canvas.tag_bind(tag, "<B1-Motion>", self.on_card_drag)
        self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_card_release)
        self.canvas.tag_bind(tag, "<Motion>", self.on_card_motion)
