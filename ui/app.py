import tkinter as tk
from datetime import datetime
from typing import Dict, List, Tuple
from ui.timeline import draw_timeline
from ui.task_card import create_task_cards
from utils.time_utils import get_current_activity, format_time
from datetime import datetime, timedelta, time

class TimeboxApp(tk.Tk):
    def __init__(self, schedule: List[Dict]):
        super().__init__()
        self.title("Timeboxing Timeline")
        self.geometry("400x700")
        self.schedule = schedule
        self.start_hour = 8
        self.end_hour = 17
        self.pixels_per_hour = 50
        self.offset_y = 0
        self.zoom_factor = 1.0
        self.cards: List[Tuple[int, int, int, Dict]] = []
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False}
        self._last_size = (self.winfo_width(), self.winfo_height())
        
        self.canvas = tk.Canvas(self, bg="white", width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)
        
        self.time_label = tk.Label(self, font=("Arial", 14, "bold"))
        self.time_label.place(x=10, y=10)
        self.activity_label = tk.Label(self, font=("Arial", 12), anchor="w", justify="left")
        self.activity_label.place(x=10, y=40, width=380)
        
        self.bind("<Configure>", self.on_resize)
        self.draw_timeline()
        self.create_task_cards()
        self.update_ui()

    def on_resize(self, event):
        if event.widget == self:
            width, height = event.width, event.height
            last_width, last_height = self._last_size
            if any(abs(d) >= 10 for d in [width - last_width, height - last_height]):
                self._last_size = (width, height)
                self.canvas.config(width=width, height=height)
                self.redraw_timeline_and_cards(width, height)

    def on_mouse_wheel(self, event):
        ctrl_held = (event.state & 0x0004) != 0
        delta = event.delta if hasattr(event, 'delta') else (-1 if event.num == 4 else 1 if event.num == 5 else 0)
        
        if ctrl_held:
            self.zoom(event, delta)
        else:
            self.scroll(event, delta)

    def zoom(self, event, delta: int):
        zoom_step = 0.1
        self.zoom_factor = max(0.5, min(2.5, self.zoom_factor + (-zoom_step if delta > 0 else zoom_step)))
        old_pph = self.pixels_per_hour
        self.pixels_per_hour = max(30, int(50 * self.zoom_factor))
        
        mouse_y = event.y
        rel_y = mouse_y - 100 - self.offset_y
        scale = self.pixels_per_hour / old_pph
        self.offset_y = int(mouse_y - 100 - rel_y * scale)
        self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height())

    def scroll(self, event, delta: int):
        if self.pixels_per_hour > 50:
            scroll_step = 40 if delta > 0 else -40
            self.offset_y = max(
                min(0, 100 - (self.pixels_per_hour * (self.end_hour - self.start_hour) + 100 - self.winfo_height())),
                min(self.offset_y + scroll_step, 0)
            )
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height())

    def draw_timeline(self):
        draw_timeline(self.canvas, self.winfo_width(), self.start_hour, self.end_hour, self.pixels_per_hour, self.offset_y)

    def create_task_cards(self):
        self.cards = create_task_cards(
            self.canvas, self.schedule, self.start_hour, self.pixels_per_hour, self.offset_y, self.winfo_width()
        )
        for card, _, _, _ in self.cards:
            tag = f"card_{card}"
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_card_press)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_card_drag)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_card_release)

    def redraw_timeline_and_cards(self, width: int, height: int):
        self.canvas.delete("all")
        self.draw_timeline()
        self.create_task_cards()

    def on_card_press(self, event):
        tags = self.canvas.gettags(tk.CURRENT)
        self._drag_data["item_ids"] = self.canvas.find_withtag(tags[0])
        self._drag_data["offset_y"] = event.y
        self._drag_data["start_y"] = event.y
        self._drag_data["dragging"] = False

    def on_card_drag(self, event):
        if not self._drag_data["item_ids"] or abs(event.y - self._drag_data["start_y"]) <= 20:
            return
        self._drag_data["dragging"] = True
        delta_y = event.y - self._drag_data["offset_y"]
        for item_id in self._drag_data["item_ids"]:
            self.canvas.move(item_id, 0, delta_y)
        self._drag_data["offset_y"] = event.y

    def on_card_release(self, event):
        if not self._drag_data["item_ids"] or not self._drag_data["dragging"]:
            self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False}
            return
        
        card_id = self._drag_data["item_ids"][0]
        self.handle_card_snap(card_id)
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False}

    def handle_card_snap(self, card_id: int):
        x0, y0, x1, y1 = self.canvas.bbox(card_id)
        card_positions = [
            (card, label, time_label, self.canvas.bbox(card)[1], self.canvas.bbox(card)[3], activity)
            for card, label, time_label, activity in self.cards
        ]
        moved_card = next(t for t in card_positions if t[0] == card_id)
        moved_top, moved_bottom = moved_card[3], moved_card[4]
        
        other_cards = sorted([t for t in card_positions if t[0] != card_id], key=lambda t: t[3])
        snapped = False
        
        for _, _, _, top, bottom, _ in other_cards:
            if bottom <= moved_top and abs(moved_top - bottom) <= 10:
                delta_y = bottom - moved_top
                for item_id in self._drag_data["item_ids"]:
                    self.canvas.move(item_id, 0, delta_y)
                snapped = True
                break
        
        if not snapped and all(moved_top <= t[3] for t in other_cards):
            delta_y = 100 - moved_top
            for item_id in self._drag_data["item_ids"]:
                self.canvas.move(item_id, 0, delta_y)
        
        self.update_card_positions()

    def update_card_positions(self):
        card_positions = sorted(
            [(card, label, time_label, self.canvas.bbox(card)[1], self.canvas.bbox(card)[3], activity)
             for card, label, time_label, activity in self.cards],
            key=lambda t: t[3]
        )
        
        current_time = datetime.now().time()
        for idx, (card, label, time_label, top, bottom, activity) in enumerate(card_positions):
            start_minutes = 0 if idx == 0 else int((card_positions[idx-1][4] - 100 - self.offset_y) * 60 / self.pixels_per_hour)
            end_minutes = start_minutes + int((bottom - top) * 60 / self.pixels_per_hour)
            
            start_time = (datetime.combine(datetime.today(), time(self.start_hour)) + timedelta(minutes=start_minutes)).time()
            end_time = (datetime.combine(datetime.today(), time(self.start_hour)) + timedelta(minutes=end_minutes)).time()
            
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
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S %A, %Y-%m-%d"))
        activity = get_current_activity(self.schedule, now)
        
        if activity:
            desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(activity["description"]))
            self.activity_label.config(
                text=f"Current: {activity['name']}\n{format_time(activity['start_time'])} - {format_time(activity['end_time'])}\n{desc}"
            )
        else:
            text = (
                "WEEKEND\nEnjoy your time off!\nSchedule resumes Monday 8:00 AM." if now.weekday() >= 5 else
                "Before work hours\nWork day starts at 8:00 AM" if now.time() < time(8, 0) else
                "End of work day\nSee you tomorrow at 8:00 AM!"
            )
            self.activity_label.config(text=text)
        
        self.after(1000, self.update_ui)
