from datetime import datetime, time
from tkinter import Canvas
from typing import Dict, List, Tuple

class TaskCard:
    def __init__(self, activity: Dict, start_of_workday: int, pixels_per_hour: int, offset_y: int, width: int):
        self.activity = activity
        self.start_hour, self.start_minute = map(int, activity["start_time"].split(":"))
        self.end_hour, self.end_minute = map(int, activity["end_time"].split(":"))
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
        self.height = ((self.end_hour - self.start_hour) * pixels_per_hour) + int((self.end_minute - self.start_minute) * pixels_per_hour / 60)
        self.card_left = int(width * 0.15)
        self.card_right = int(width * 0.85)
        self.card = None
        self.label = None
        self.time_label = None

    def draw(self, canvas: Canvas, now: time):
        is_active = time(self.start_hour, self.start_minute) <= now < time(self.end_hour, self.end_minute)
        is_finished = time(self.end_hour, self.end_minute) <= now
        color = (
            "#cccccc" if is_finished else
            "#ffff99" if is_active else
            "#add8e6"
        )
        self.card = canvas.create_rectangle(self.card_left, self.y, self.card_right, self.y + self.height, fill=color, outline="black")
        # Progress bar for active card
        if is_active:
            total_minutes = (self.end_hour - self.start_hour) * 60 + (self.end_minute - self.start_minute)
            elapsed_minutes = (now.hour - self.start_hour) * 60 + (now.minute - self.start_minute)
            progress = min(max(elapsed_minutes / total_minutes, 0), 1) if total_minutes > 0 else 1
            fill_right = self.card_left + int((self.card_right - self.card_left) * progress)
            canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="")
        self.label = canvas.create_text((self.card_left + self.card_right) // 2, self.y + self.height // 2, text=self.activity["name"])
        tag = f"card_{self.card}"
        canvas.itemconfig(self.card, tags=(tag, "card"))
        canvas.itemconfig(self.label, tags=(tag, "card"))
        self.time_label = canvas.create_text(
            self.card_left - 10, self.y, text=f"{self.start_hour:02d}:{self.start_minute:02d}", font=("Arial", 8), anchor="e"
        )
        return self

    def get_time_range(self):
        return time(self.start_hour, self.start_minute), time(self.end_hour, self.end_minute)

    def move_to_time(self, new_start_hour, new_start_minute, start_of_workday, pixels_per_hour, offset_y):
        # Update y based on new start time
        self.start_hour = new_start_hour
        self.start_minute = new_start_minute
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y


def create_task_cards(
    canvas: Canvas,
    schedule: List[Dict],
    start_of_workday: int,
    pixels_per_hour: int,
    offset_y: int,
    width: int
) -> List[TaskCard]:
    """Create task card objects and draw them on the canvas."""
    cards = []
    now = datetime.now().time()
    active_y = None
    for activity in schedule:
        card_obj = TaskCard(activity, start_of_workday, pixels_per_hour, offset_y, width)
        card_obj.draw(canvas, now)
        # Find active card's y for green arrows
        start_time, end_time = card_obj.get_time_range()
        if start_time <= now < end_time:
            minutes_since_start = (now.hour*60+now.minute) - (card_obj.start_hour*60+card_obj.start_minute)
            active_y = card_obj.y + int(minutes_since_start * pixels_per_hour / 60)
        cards.append(card_obj)
    # Draw green arrows at the current time if within any card
    if active_y is not None and cards:
        card_left = cards[0].card_left
        card_right = cards[0].card_right
        #canvas.create_line(card_left-30, active_y, card_left, active_y, fill="green", width=2, arrow="last", arrowshape=(16,20,6))
        #canvas.create_line(card_right+30, active_y, card_right, active_y, fill="green", width=2, arrow="last", arrowshape=(16,20,6))
    return cards
