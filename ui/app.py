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
        self.zoom_factor = 6.0
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        self.offset_y = 0
        self.cards: List[Tuple[int, int, int, Dict]] = []
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False}
        self._last_size = (self.winfo_width(), self.winfo_height())
        
        self.canvas = tk.Canvas(self, bg="white", width=400, height=700)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)
        self.canvas.bind('<Button-4>', self.on_mouse_wheel)
        self.canvas.bind('<Button-5>', self.on_mouse_wheel)
        
        self.time_label = tk.Label(self, font=("Arial", 14, "bold"), bg="#0f8000")
        self.time_label.place(x=10, y=10)
        self.activity_label = tk.Label(self, font=("Arial", 12), anchor="w", justify="left", bg="#ffff99", relief="solid", bd=2)
        self.activity_label.place(x=10, y=40, width=380)
        
        self.bind("<Configure>", self.on_resize)

        # Center view on current time
        now = datetime.now().time()
        minutes_since_start = (now.hour - self.start_hour) * 60 + now.minute
        center_y = int(minutes_since_start * self.pixels_per_hour / 60) + 100
        
        # both these calls are needed to ensure the correct offset_y is calculated
        self.offset_y = (self.winfo_height() // 2) - center_y
        self.update_idletasks()  # Ensure window size is correct before centering
        self.offset_y = (self.winfo_height() // 2) - center_y
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
                self.redraw_timeline_and_cards(width, height, center=False)

    def on_mouse_wheel(self, event):
        ctrl_held = (event.state & 0x0004) != 0
        print(f"Mouse Wheel Event: {event.num}, Delta: {event.delta}, Ctrl Held: {ctrl_held}")
        delta = 0
        if event.num == 4:  # Scroll up
            delta = -1
        elif event.num == 5:  # Scroll down
            delta = 1
        
        if ctrl_held:
            self.zoom(event, delta)
        else:
            self.scroll(event, delta)

    def zoom(self, event, delta: int):
        zoom_step = 0.1
        a = self.zoom_factor + (-zoom_step if delta > 0 else zoom_step)
        print(f"Zooming: {a:.2f} (Delta: {delta})")
        self.zoom_factor = max(0.5, min(6, a ))
        old_pph = self.pixels_per_hour
        self.pixels_per_hour = max(50, int(50 * self.zoom_factor))
        
        mouse_y = event.y
        rel_y = mouse_y - 100 - self.offset_y
        scale = self.pixels_per_hour / old_pph
        print(f"Zooming: {self.zoom_factor:.2f}, PPH: {self.pixels_per_hour}, Mouse Y: {mouse_y}, Rel Y: {rel_y}, Scale: {scale}")
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
        now = datetime.now().time()
        draw_timeline(self.canvas, self.winfo_width(), self.start_hour, self.end_hour, self.pixels_per_hour, self.offset_y, current_time=now)

    def create_task_cards(self):
        self.cards = create_task_cards(
            self.canvas, self.schedule, self.start_hour, self.pixels_per_hour, self.offset_y, self.winfo_width()
        )
        for card_obj in self.cards:
            tag = f"card_{card_obj.card}"
            self.canvas.tag_bind(tag, "<ButtonPress-1>", self.on_card_press)
            self.canvas.tag_bind(tag, "<B1-Motion>", self.on_card_drag)
            self.canvas.tag_bind(tag, "<ButtonRelease-1>", self.on_card_release)

    def redraw_timeline_and_cards(self, width: int, height: int, center: bool = True):

        if center:
            # Center view on current time before redraw
            now = datetime.now().time()
            minutes_since_start = (now.hour - self.start_hour) * 60 + now.minute
            center_y = int(minutes_since_start * self.pixels_per_hour / 60) + 100
            self.offset_y = (height // 2) - center_y

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
        self.handle_card_snap(card_id, event.y)
        self._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False}

    def handle_card_snap(self, card_id: int, y: int):
        # Find the TaskCard object for the moved card
        moved_card = next(card for card in self.cards if card.card == card_id)

        # Compute new start time from y position
        y_relative = y - 100 - self.offset_y
        total_minutes = int(y_relative * 60 / self.pixels_per_hour)
        new_hour = self.start_hour + total_minutes // 60
        new_minute = total_minutes % 60
        print(f"Moving card {moved_card.activity['name']} to {new_hour:02d}:{new_minute:02d}")

        # Clamp to valid range
        if new_hour < self.start_hour:
            new_hour, new_minute = self.start_hour, 0
        if new_hour > self.end_hour or (new_hour == self.end_hour and new_minute > 0):
            new_hour, new_minute = self.end_hour, 0

        # Check for overlap with other cards
        sorted_cards = sorted(self.cards, key=lambda c: (c.start_hour, c.start_minute))
        idx = sorted_cards.index(moved_card)

        # Remove moved card from list
        sorted_cards.pop(idx)

        # Find new index for moved card
        insert_idx = 0
        for i, card in enumerate(sorted_cards):
            if (card.start_hour, card.start_minute) > (new_hour, new_minute):
                break
            insert_idx = i + 1

        # Insert moved card at new position
        sorted_cards.insert(insert_idx, moved_card)

        # Update times for all cards in order
        cur_hour, cur_minute = self.start_hour, 0
        for card in sorted_cards:
            duration = (card.end_hour - card.start_hour) * 60 + (card.end_minute - card.start_minute)
            card.move_to_time(cur_hour, cur_minute, self.start_hour, self.pixels_per_hour, self.offset_y)
            cur_hour = cur_hour + (cur_minute + duration) // 60
            cur_minute = (cur_minute + duration) % 60

        # Update moved card last
        duration = (moved_card.end_hour - moved_card.start_hour) * 60 + (moved_card.end_minute - moved_card.start_minute)
        moved_card.move_to_time(new_hour, new_minute, self.start_hour, self.pixels_per_hour, self.offset_y)
        cur_hour = new_hour + (new_minute + duration) // 60
        cur_minute = (new_minute + duration) % 60

        # Rebuild self.cards in new order
        self.cards = []
        inserted = False
        for i, card in enumerate(sorted_cards):
            if not inserted and (card.start_hour, card.start_minute) > (moved_card.start_hour, moved_card.start_minute):
                self.cards.append(moved_card)
                inserted = True
            self.cards.append(card)
        if not inserted:
            self.cards.append(moved_card)
        self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height(), center=False)

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
                text=f"Actions:\n{desc}"
            )
        else:
            text = (
                "WEEKEND\nEnjoy your time off!\nSchedule resumes Monday 8:00 AM." if now.weekday() >= 5 else
                "Before work hours\nWork day starts at 8:00 AM" if now.time() < time(8, 0) else
                "End of work day\nSee you tomorrow at 8:00 AM!"
            )
            self.activity_label.config(text=text)

        # Redraw everything every full minute
        if now.second == 0:
            self.redraw_timeline_and_cards(self.winfo_width(), self.winfo_height())
        self.after(1000, self.update_ui)
