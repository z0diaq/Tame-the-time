import tkinter as tk
from datetime import datetime
from typing import Dict, List, Tuple
from ui.timeline import draw_timeline
from ui.task_card import create_task_cards
from utils.time_utils import get_current_activity, format_time
from datetime import datetime, timedelta, time
import json
import os
import utils.notification

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

    def __init__(self, schedule: List[Dict], now_provider=datetime.now):
        super().__init__()
        self.now_provider = now_provider
        self.settings = self.load_settings()
        
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
        self.cards: List[Tuple[int, int, int, Dict]] = []
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        self._last_size = (self.winfo_width(), self.winfo_height())
        self.timeline_granularity = 60  # 60 min (1h) by default
        self.hide_card_start_times = False
        self.menu_hide_job = None
        
        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open")
        self.file_menu.add_command(label="Close")
        self.file_menu.add_command(label="Save")
        self.file_menu.add_command(label="New")
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.options_menu.add_command(label="Global options")
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.menu_visible = False

        self.canvas = tk.Canvas(self, bg="white", width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)
        self.canvas.bind("<Motion>", self.on_motion)

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
        self.canvas.delete("all")
        self.draw_timeline()
        self.create_task_cards()
        self.skip_redraw = False  # Allow redraws after initial setup
        self.update_ui()

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.poll_mouse()

    def on_close(self):
        self.save_settings()
        self.destroy()

    def on_resize(self, event):
        if event.widget == self:
            width, height = event.width, event.height
            last_width, last_height = self._last_size
            if any(abs(d) >= 10 for d in [width - last_width, height - last_height]):
                self._last_size = (width, height)
                self.canvas.config(width=width, height=height)
                if not self.skip_redraw:
                    self.redraw_timeline_and_cards(width, height, center=False)

    def on_mouse_wheel(self, event):
        ctrl_held = (event.state & 0x0004) != 0
        print(f"Mouse Wheel Event: {event.num}, Delta: {event.delta}, Ctrl Held: {ctrl_held}")
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
        self.zoom_factor = max(0.5, min(6, a ))
        old_pph = self.pixels_per_hour
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        
        mouse_y = event.y
        rel_y = mouse_y - 100 - self.offset_y
        scale = self.pixels_per_hour / old_pph
        self.offset_y = min(100, int(mouse_y - 100 - rel_y * scale))
        self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height(), center=False)

    def scroll(self, event, delta: int):
        print(f"Scrolling: {delta}, PPH: {self.pixels_per_hour}, Current Offset Y: {self.offset_y}")
        if self.pixels_per_hour > 50:
            scroll_step = -40 if delta > 0 else 40
            self.offset_y += scroll_step
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height(), center=False)

    def draw_timeline(self):
        # Pass current time to draw_timeline for green line
        now = self.now_provider().time()
        self.timeline_objects_ids = draw_timeline(
            self.canvas, self.winfo_width(), self.start_hour, self.end_hour, self.pixels_per_hour, self.offset_y, 
            current_time=now, granularity=self.timeline_granularity
        )

    def redraw_timeline(self):
        """Redraw the timeline without creating task cards."""
        self.canvas.delete("timeline")
        self.draw_timeline()

    def on_card_motion(self, event):
        tags = self.canvas.gettags(tk.CURRENT)
        print(f"Tags = {tags}")
        if not tags:
            self.config(cursor="")
            return
        dragged_id = self.canvas.find_withtag(tags[0])[0]
        y_card_top = self.canvas.coords(dragged_id)[1]
        y_card_bottom = self.canvas.coords(dragged_id)[3]
        if abs(event.y - y_card_top) <= 10:
            self.config(cursor="top_side")
        elif abs(event.y - y_card_bottom) <= 10:
            self.config(cursor="bottom_side")
        else:
            self.config(cursor="fleur")

    def create_task_cards(self):
        self.cards = create_task_cards(
            self.canvas,
            self.schedule,
            self.start_hour,
            self.pixels_per_hour,
            self.offset_y,
            self.winfo_width(),
            now_provider=self.now_provider,
            hide_start_time=self.hide_card_start_times
        )
        for card_obj in self.cards:
            tag = f"card_{card_obj.card}"
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_card_press)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_card_drag)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_card_release)
            self.canvas.tag_bind(tag, "<Motion>", self.on_card_motion)

    def redraw_timeline_and_cards(self, width: int, height: int, center: bool = True):

        if center:
            # Center view on current time before redraw
            now = self.now_provider().time()
            minutes_since_start = (now.hour - self.start_hour) * 60 + now.minute
            center_y = int(minutes_since_start * self.pixels_per_hour / 60) + 100
            self.offset_y = (height // 2) - center_y

        self.canvas.delete("all")
        self.draw_timeline()
        self.create_task_cards()

    def on_card_press(self, event):
        tags = self.canvas.gettags(tk.CURRENT)
        print(f"Card pressed: {tags}")
        self._drag_data["item_ids"] = self.canvas.find_withtag(tags[0])
        self._drag_data["offset_y"] = event.y
        self._drag_data["start_y"] = event.y
        self._drag_data["dragging"] = False
        self._drag_data["resize_mode"] = None
        dragged_id = self._drag_data["item_ids"][0]
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
                if card_obj.label:
                    self.canvas.itemconfig(card_obj.label, fill="black")
        if self.timeline_granularity != 5:
            self.timeline_granularity = 5
            self.hide_card_start_times = True
            for item in getattr(self, 'timeline_objects_ids', []):
                self.canvas.delete(item)
            self.draw_timeline()

    def round_to_nearest_5_minutes(self, minutes: int) -> int:
        """Round minutes to the nearest 5 minutes."""
        return 5 * round(minutes / 5)

    def on_card_drag(self, event):
        if not self._drag_data["item_ids"] or abs(event.y - self._drag_data["start_y"]) <= 20:
            return
        self._drag_data["dragging"] = True
        dragged_id = self._drag_data["item_ids"][0]
        if self._drag_data.get("resize_mode") == "top":
            # Resize from top
            y_card_bottom = self.canvas.coords(dragged_id)[3]
            new_top = min(event.y, y_card_bottom - 20)
            snapped_minutes = self.round_to_nearest_5_minutes(int((new_top - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            self.canvas.coords(dragged_id, self.canvas.coords(dragged_id)[0], snapped_y, self.canvas.coords(dragged_id)[2], y_card_bottom)
        elif self._drag_data.get("resize_mode") == "bottom":
            # Resize from bottom
            y_card_top = self.canvas.coords(dragged_id)[1]
            new_bottom = max(event.y, y_card_top + 20)
            snapped_minutes = self.round_to_nearest_5_minutes(int((new_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            self.canvas.coords(dragged_id, self.canvas.coords(dragged_id)[0], y_card_top, self.canvas.coords(dragged_id)[2], snapped_y)
        else:
            # Normal drag (move)
            y = event.y
            y_relative = y - 100 - self.offset_y
            total_minutes = int(y_relative * 60 / self.pixels_per_hour)
            snapped_minutes = self.round_to_nearest_5_minutes(total_minutes)
            snapped_y = int(snapped_minutes * self.pixels_per_hour / 60) + 100 + self.offset_y
            delta_y = snapped_y - self.canvas.coords(dragged_id)[1]
            for item_id in self._drag_data["item_ids"]:
                self.canvas.move(item_id, 0, delta_y)
            self._drag_data["offset_y"] = event.y + (snapped_y - y)

    def on_card_release(self, event):
        self.config(cursor="")
        if not self._drag_data["item_ids"] or not self._drag_data["dragging"]:
            self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
            self.timeline_granularity = 60
            self.hide_card_start_times = False
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height(), center=False)
            return
        card_id = self._drag_data["item_ids"][0]
        if self._drag_data.get("resize_mode"):
            self.handle_card_resize(card_id, event.y, self._drag_data["resize_mode"])
        else:
            self.handle_card_snap(card_id, event.y)
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        self.timeline_granularity = 60
        self.hide_card_start_times = False
        for card_obj in self.cards:
            self.canvas.itemconfig(card_obj.card, stipple="")
            if card_obj.label:
                self.canvas.itemconfig(card_obj.label, fill="black")
        self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height(), center=False)

    def handle_card_snap(self, card_id: int, y: int):
        # Find the TaskCard object for the moved card
        moved_card = next(card for card in self.cards if card.card == card_id)

        # Compute new start time from y position
        y_relative = y - 100 - self.offset_y
        total_minutes = int(y_relative * 60 / self.pixels_per_hour)
        new_hour = self.start_hour + total_minutes // 60
        new_minute = self.round_to_nearest_5_minutes(total_minutes % 60)
        print(f"Moving card {moved_card.activity['name']} to {new_hour:02d}:{new_minute:02d}")

        # Clamp to valid range
        if new_hour < self.start_hour:
            new_hour, new_minute = self.start_hour, 0
        if new_hour > self.end_hour or (new_hour == self.end_hour and new_minute > 0):
            new_hour, new_minute = self.end_hour, 0
        
        idx = self.cards.index(moved_card)
        self.cards[idx].move_to_time(new_hour, new_minute, self.start_hour, self.pixels_per_hour, self.offset_y)
        self.schedule = [card.to_dict() for card in self.cards]

    def handle_card_resize(self, card_id: int, y: int, mode: str):
        moved_card = next(card for card in self.cards if card.card == card_id)
        y_card_top = self.canvas.coords(card_id)[1]
        y_card_bottom = self.canvas.coords(card_id)[3]
        if mode == "top":
            new_top = min(y, y_card_bottom - 20)
            snapped_minutes = self.round_to_nearest_5_minutes(int((new_top - 100 - self.offset_y) * 60 / self.pixels_per_hour))
            new_start_minutes = snapped_minutes
            new_end_minutes = int((y_card_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour)
        else:
            new_top = y_card_top
            new_bottom = max(y, y_card_top + 20)
            snapped_minutes = self.round_to_nearest_5_minutes(int((new_bottom - 100 - self.offset_y) * 60 / self.pixels_per_hour))
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

    def update_card_positions(self):
        card_positions = sorted(
            [(card, label, time_label, self.canvas.bbox(card)[1], self.canvas.bbox(card)[3], activity)
             for card, label, time_label, activity in self.cards],
            key=lambda t: t[3]
        )
        
        current_time = self.now_provider().time()
        for idx, (card, label, time_label, top, bottom, activity) in enumerate(card_positions):
            start_minutes = 0 if idx == 0 else int((card_positions[idx-1][4] - 100 - self.offset_y) * 60 / self.pixels_per_hour)
            end_minutes = start_minutes + int((bottom - top) * 60 / self.pixels_per_hour)
            
            start_time = (datetime.combine(self.now_provider(), time(self.start_hour)) + timedelta(minutes=start_minutes)).time()
            end_time = (datetime.combine(self.now_provider(), time(self.start_hour)) + timedelta(minutes=end_minutes)).time()
            
            self.canvas.itemconfig(label, text=activity["name"])
            self.canvas.delete(time_label)
            time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
            new_time_label = self.canvas.create_text(
                (self.canvas.bbox(card)[0] + self.canvas.bbox(card)[2]) // 2,
                (top + bottom) // 2 + 12,
                text=time_range,
                font=("Arial", 8)
            )
            self.cards[idx] = (card, label, new_time_label, activity)
            
            color = (
                "#cccccc" if end_time <= current_time else
                "#ffff99" if start_time <= current_time < end_time else
                "#add8e6"
            )
            self.canvas.itemconfig(card, fill=color)
            
            if idx > 0 and top < card_positions[idx-1][4]:
                delta_y = card_positions[idx-1][4] - top
                for item in (card, label, new_time_label):
                    self.canvas.move(item, 0, delta_y)

    def update_ui(self):

        global last_activity

        now = self.now_provider()
        self.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
        activity = get_current_activity(self.schedule, now)
        if activity:
            desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(activity["description"]))
            self.activity_label.config(
                text=f"Actions:\n{desc}"
            )
            # Send notification if activity changed and notifications are allowed
            if (last_activity is None or last_activity["name"] != activity["name"]) and allow_notification:
                utils.notification.send_gotify_notification(activity)
                print(f"Notification sent for activity: {activity['name']}")

            last_activity = activity
        else:
            text = (
                "WEEKEND\nEnjoy your time off!\nSchedule resumes Monday 8:00 AM." if now.weekday() >= 5 else
                "Before work hours\nWork day starts at 8:00 AM" if now.time() < time(8, 0) else
                "End of work day\nSee you tomorrow at 8:00 AM!"
            )
            self.activity_label.config(text=text)

        # Redraw everything every full minute
        if now.second == 0:
            self.config(cursor="")
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height())
        self.after(1000, self.update_ui)
