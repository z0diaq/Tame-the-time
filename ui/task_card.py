from datetime import datetime, time
from tkinter import Canvas
from typing import Dict, List

class TaskCard:
    def __init__(self, activity: Dict, start_of_workday: int, pixels_per_hour: int, offset_y: int, width: int, now_provider=None):
        self.activity = activity
        self.start_hour, self.start_minute = map(int, activity["start_time"].split(":"))
        self.end_hour, self.end_minute = map(int, activity["end_time"].split(":"))
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
        self.height = ((self.end_hour - self.start_hour) * pixels_per_hour) + int((self.end_minute - self.start_minute) * pixels_per_hour / 60)
        self.card_left = int(width * 0.15)
        self.card_right = int(width * 0.85)
        self.card = None
        self.label = None
        self.now_provider = now_provider
        self.time_label = None

    def draw(self, canvas: Canvas, now: time = None, hide_start_time: bool = False):
        if now is None:
            now = self.now_provider().time()
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
            canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="black")
        self.label = canvas.create_text((self.card_left + self.card_right) // 2, self.y + self.height // 2, text=self.activity["name"])
        tag = f"card_{self.card}"
        canvas.itemconfig(self.card, tags=(tag, "card"))
        canvas.itemconfig(self.label, tags=(tag, "card"))
        if not hide_start_time:
            self.time_label = canvas.create_text(
                self.card_left - 10, self.y, text=f"{self.start_hour:02d}:{self.start_minute:02d}", font=("Arial", 8), anchor="e"
            )
        else:
            self.time_label = None
        return self

    def get_time_range(self):
        return time(self.start_hour, self.start_minute), time(self.end_hour, self.end_minute)

    def move_to_time(self, new_start_hour, new_start_minute, start_of_workday, pixels_per_hour, offset_y):
        # Update the end time based on the new start time
        card_duration_minutes = (self.end_hour - self.start_hour) * 60 + (self.end_minute - self.start_minute)
        # Calculate new end time
        # Convert everything to total minutes since midnight
        total_minutes = new_start_hour * 60 + new_start_minute + card_duration_minutes
        
        # Handle negative times (wrap to previous day)
        # Modulo operation ensures we stay within 24-hour range
        total_minutes = total_minutes % (24 * 60)
        
        # Convert back to hours and minutes
        self.end_hour = total_minutes // 60
        self.end_minute = total_minutes % 60

        # Update y based on new start time
        self.start_hour = new_start_hour
        self.start_minute = new_start_minute
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
    
    def to_dict(self):
        """Convert the TaskCard to a dictionary representation."""
        return {
            "name": self.activity["name"],
            "start_time": f"{self.start_hour:02d}:{self.start_minute:02d}",
            "end_time": f"{self.end_hour:02d}:{self.end_minute:02d}",
            "description": self.activity["description"]
        }

def create_task_cards(
    canvas: Canvas,
    schedule: List[Dict],
    start_of_workday: int,
    pixels_per_hour: int,
    offset_y: int,
    width: int,
    now_provider=None,
    hide_start_time: bool = False
) -> List[TaskCard]:
    """Create task card objects and draw them on the canvas."""
    cards = []
    now = now_provider().time()
    active_y = None
    for activity in schedule:
        card_obj = TaskCard(activity, start_of_workday, pixels_per_hour, offset_y, width, now_provider=now_provider)
        card_obj.draw(canvas, now, hide_start_time=hide_start_time)
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
