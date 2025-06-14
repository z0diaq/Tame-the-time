from datetime import datetime, time
from tkinter import Canvas
from typing import Dict, List
from utils.logging import log_info, log_debug



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
        self.canvas = None

        self.finished_color = "#cccccc"  # Color for finished tasks
        self.active_color = "#ffff99"
        self.inactive_color = "#add8e6"  # Color for inactive tasks
    
    def draw(self, canvas: Canvas, now: time = None, draw_end_time: bool = False):
        self.canvas = canvas
        if now is None:
            now = self.now_provider().time()
        is_active = time(self.start_hour, self.start_minute) <= now < time(self.end_hour, self.end_minute)
        is_finished = time(self.end_hour, self.end_minute) <= now
        color = (
            self.finished_color if is_finished else
            self.active_color if is_active else
            self.inactive_color
        )
        self.card = canvas.create_rectangle(self.card_left, self.y, self.card_right, self.y + self.height, fill=color, outline="black")
        # Progress bar for active card
        if is_active:
            total_seconds = (self.end_hour - self.start_hour) * 3600 + (self.end_minute - self.start_minute) * 60
            elapsed_seconds = (now.hour - self.start_hour) * 3600 + (now.minute - self.start_minute) * 60 + now.second
            progress = min(elapsed_seconds / total_seconds, 1) if total_seconds > 0 else 1
            log_info(f"Drawing progress for card {self.activity['name']}: {progress:.2f}")
            fill_right = self.card_left + int((self.card_right - self.card_left) * progress)
            self.progress = canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="black")
        self.label = canvas.create_text((self.card_left + self.card_right) // 2, self.y + self.height // 2, text=self.activity["name"])
        tag = f"card_{self.card}"
        canvas.itemconfig(self.card, tags=(tag))
        canvas.itemconfig(self.label, tags=(tag))

        self.time_start_label = canvas.create_text(
            self.card_left - 10, self.y, text=f"{self.start_hour:02d}:{self.start_minute:02d}", font=("Arial", 8), anchor="e"
        )
        # Hide time_start_label if at 0 minutes
        if self.start_minute == 0:
            canvas.itemconfig(self.time_start_label, state="hidden")
        
        end_time_text = f"{self.end_hour:02d}:{self.end_minute:02d}"
        self.time_end_label = canvas.create_text(
            self.card_left - 10, self.y + self.height, text=end_time_text, font=("Arial", 8), anchor="e"
        )
        # Hide time_end_label if at 0 minutes
        if self.end_minute == 0 or not draw_end_time:
            canvas.itemconfig(self.time_end_label, state="hidden")
        return self

    def get_time_range(self):
        return time(self.start_hour, self.start_minute), time(self.end_hour, self.end_minute)

    def update_card_visuals(self, new_start_hour, new_start_minute, start_of_workday, pixels_per_hour, offset_y, now=None, show_start_time=True, show_end_time=True, width=None):
        """Move/resize the card, update progress bar, and update label positions/visibility. Also update width if provided."""
        if now is None:
            now = self.now_provider().time() if self.now_provider else time(0, 0)
        if width is not None:
            self.card_left = int(width * 0.15)
            self.card_right = int(width * 0.85)
        # Calculate new end time
        card_duration_minutes = (self.end_hour - self.start_hour) * 60 + (self.end_minute - self.start_minute)
        log_debug(f"Cards duration in minutes: {card_duration_minutes}")
        total_minutes = new_start_hour * 60 + new_start_minute + card_duration_minutes
        total_minutes = total_minutes % (24 * 60)
        self.end_hour = total_minutes // 60
        self.end_minute = total_minutes % 60
        self.start_hour = new_start_hour
        self.start_minute = new_start_minute % 60
        prev_y = self.y
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
        height = ((self.end_hour - self.start_hour) * pixels_per_hour) + int((self.end_minute - self.start_minute) * pixels_per_hour / 60)
        self.height = height
        diff_y = self.y - prev_y
        # Move/resize card
        self.canvas.coords(self.card, self.card_left, self.y, self.card_right, self.y + height)
        # Update progress bar
        should_show_progress = time(self.start_hour, self.start_minute) <= now < time(self.end_hour, self.end_minute)
        if should_show_progress:
            total_seconds = (self.end_hour - self.start_hour) * 3600 + (self.end_minute - self.start_minute) * 60
            elapsed_seconds = (now.hour - self.start_hour) * 3600 + (now.minute - self.start_minute) * 60 + now.second
            progress = min(elapsed_seconds / total_seconds, 1) if total_seconds > 0 else 1
            fill_right = self.card_left + int((self.card_right - self.card_left) * progress)
            if not hasattr(self, 'progress') or self.progress is None:
                self.progress = self.canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="")
            else:
                self.canvas.coords(self.progress, self.card_left, self.y, fill_right, self.y + self.height)
            self.canvas.itemconfig(self.progress, state="normal")
            self.canvas.itemconfig(self.card, fill=self.active_color)
            self.canvas.tag_raise(self.label)
        else:
            if hasattr(self, 'progress') and self.progress is not None:
                self.canvas.itemconfig(self.progress, state="hidden")
            color = self.finished_color if time(self.end_hour, self.end_minute) <= now else self.inactive_color
            self.canvas.itemconfig(self.card, fill=color)

        # Update text labels
        self.canvas.itemconfig(self.time_start_label, text=f"{self.start_hour:02d}:{self.start_minute:02d}")
        self.canvas.coords(self.time_start_label, self.card_left - 10, self.y)
        self.canvas.itemconfig(self.time_start_label, state="hidden" if self.start_minute == 0 or not show_start_time else "normal")

        self.canvas.itemconfig(self.time_end_label, text=f"{self.end_hour:02d}:{self.end_minute:02d}")
        self.canvas.coords(self.time_end_label, self.card_left - 10, self.y + self.height)
        self.canvas.itemconfig(self.time_end_label, state="hidden" if self.end_minute == 0 or not show_end_time else "normal")

        self.canvas.coords(self.label, (self.card_left + self.card_right) // 2, self.y + self.height // 2)
        self.canvas.itemconfig(self.label, text=self.activity["name"])

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
    now_provider=None
) -> List[TaskCard]:
    """Create task card objects and draw them on the canvas."""
    cards = []
    now = now_provider().time()
    active_y = None
    count = len(schedule)
    for index, activity in enumerate(schedule):
        card_obj = TaskCard(activity, start_of_workday, pixels_per_hour, offset_y, width, now_provider=now_provider)
        draw_end_time = False
        # Draw end time if there is a gap between this and the next card
        if index < count - 1:
            next_activity = schedule[index + 1]
            next_start_hour, next_start_minute = map(int, next_activity["start_time"].split(":"))
            if (next_start_hour, next_start_minute) != (card_obj.end_hour, card_obj.end_minute):
                draw_end_time = True
        else:
            draw_end_time = True
        card_obj.draw(canvas, now, draw_end_time=draw_end_time)
        # Find active card's y for green arrows
        start_time, end_time = card_obj.get_time_range()
        if start_time <= now < end_time:
            minutes_since_start = (now.hour*60+now.minute) - (card_obj.start_hour*60+card_obj.start_minute)
            active_y = card_obj.y + int(minutes_since_start * pixels_per_hour / 60)
        cards.append(card_obj)
    return cards
