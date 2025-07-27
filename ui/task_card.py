from datetime import time
from tkinter import Canvas
import tkinter as tk
from typing import Dict, List
from utils.logging import log_info, log_debug
from utils.time_utils import TimeUtils
from constants import UIConstants, Colors

class TaskCard:
    def __init__(
            self,
            activity: Dict,
            start_of_workday: int,
            pixels_per_hour: int,
            offset_y: int,
            width: int,
            now_provider=None
        ):
        self.activity = activity
        
        # Use TimeUtils for consistent time parsing
        start_time_obj = TimeUtils.parse_time_with_validation(activity["start_time"])
        end_time_obj = TimeUtils.parse_time_with_validation(activity["end_time"])
        
        self.start_hour, self.start_minute = start_time_obj.hour, start_time_obj.minute
        self.end_hour, self.end_minute = end_time_obj.hour, end_time_obj.minute
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
        self.height = ((self.end_hour - self.start_hour) * pixels_per_hour) + int((self.end_minute - self.start_minute) * pixels_per_hour / 60)
        self.card_left = int(width * UIConstants.CARD_LEFT_RATIO)
        self.card_right = int(width * UIConstants.CARD_RIGHT_RATIO)
        self.card = None
        self.label = None
        self.now_provider = now_provider
        self.time_label = None
        self.canvas = None
        self.being_modified = False

        self.finished_color = Colors.FINISHED_TASK
        self.active_color = Colors.ACTIVE_TASK
        self.inactive_color = Colors.INACTIVE_TASK

    # Make a clone function that will set the same properties as the original TaskCard
    def clone(self):
        """Create a clone of the TaskCard with the same properties."""
        clone = TaskCard(
            activity=self.activity,
            start_of_workday=self.start_hour,
            pixels_per_hour=0,  # Will be set later
            offset_y=0,  # Will be set later
            width=0,  # Will be set later
            now_provider=self.now_provider
        )
        clone.start_hour = self.start_hour
        clone.start_minute = self.start_minute
        clone.end_hour = self.end_hour
        clone.end_minute = self.end_minute
        clone.y = self.y
        clone.height = self.height
        clone.card_left = self.card_left
        clone.card_right = self.card_right
        return clone    

    def set_being_modified(self, being_modified: bool):
        """Set the being_modified flag to control visibility of progress bar."""
        self.being_modified = being_modified

    def setup_card_progress_actions(self, canvas: Canvas):
        log_debug("Binding card actions")
        # On card enter event, hide the progress rectangle
        def on_card_enter(event):
            log_debug(f"Card {self.activity['name']} entered")
            if hasattr(self, 'progress') and self.progress:
                canvas.itemconfig(self.progress, state="hidden")
        # On card leave event, show the progress rectangle
        def on_card_leave(event):
            log_debug(f"Card {self.activity['name']} left")
            if hasattr(self, 'progress') and self.progress and not self.being_modified:
                canvas.itemconfig(self.progress, state="normal")
    
        canvas.tag_bind(self.card, "<Enter>", on_card_enter)
        if hasattr(self, 'progress') and self.progress:
            canvas.tag_bind(self.progress, "<Enter>", on_card_enter)
        canvas.tag_bind(self.label, "<Enter>", on_card_enter)
        canvas.tag_bind(self.card, "<Leave>", on_card_leave)
        canvas.tag_bind(self.label, "<Leave>", on_card_leave)

    def remove_card_progress_actions(self, canvas: Canvas):
        log_debug("Unbinding card actions")
        canvas.tag_unbind(self.card, "<Enter>")
        canvas.tag_unbind(self.label, "<Enter>")
        canvas.tag_unbind(self.card, "<Leave>")
        canvas.tag_unbind(self.label, "<Leave>")
        if hasattr(self, 'progress') and self.progress:
            canvas.tag_unbind(self.progress, "<Enter>")
            canvas.tag_unbind(self.progress, "<Leave>")

    def draw(self, canvas: Canvas, now: time = None, draw_end_time: bool = False):
        self.canvas = canvas
        if now is None:
            now = self.now_provider().time()
        is_active = self.is_active_at(now)
        is_finished = time(self.end_hour, self.end_minute) <= now
        color = (
            self.finished_color if is_finished else
            self.active_color if is_active else
            self.inactive_color
        )
        self.card = canvas.create_rectangle(self.card_left, self.y, self.card_right, self.y + self.height, fill=color, outline=Colors.CARD_OUTLINE)
        # Progress bar for active card
        self.label = canvas.create_text((self.card_left + self.card_right) // 2, self.y + self.height // 2, text=self.activity["name"])
        if is_active:
            total_seconds = (self.end_hour - self.start_hour) * 3600 + (self.end_minute - self.start_minute) * 60
            elapsed_seconds = (now.hour - self.start_hour) * 3600 + (now.minute - self.start_minute) * 60 + now.second
            progress = min(elapsed_seconds / total_seconds, 1) if total_seconds > 0 else 1
            log_info(f"Drawing progress for card {self.activity['name']}: {progress:.2f}")
            fill_right = self.card_left + int((self.card_right - self.card_left) * progress)
            self.progress = canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="black")
            self.setup_card_progress_actions(canvas)
            canvas.tag_raise(self.label)
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
        # Add tasks count label if tasks exist
        tasks = self.activity.get("tasks", [])
        # Use _tasks_done if present, otherwise count all as not done
        tasks_done = getattr(self, '_tasks_done', [False] * len(tasks))
        remaining_tasks = [t for t, done in zip(tasks, tasks_done) if not done]
        if remaining_tasks:
            self.tasks_count_label = canvas.create_text(
                self.card_right - 5, self.y + self.height - 5,
                text=f"Tasks: {len(remaining_tasks)}",
                font=("Arial", 8, "bold"), anchor="se", fill="#0a0a0a"
            )
            canvas.itemconfig(self.tasks_count_label, tags=(tag))
        else:
            self.tasks_count_label = None
        return self

    def delete(self):
        """Delete the card and its associated elements from the canvas."""
        # List of all canvas objects that need cleanup
        canvas_objects = [
            ('card', self.card),
            ('label', self.label),
            ('progress', getattr(self, 'progress', None)),
            ('time_start_label', getattr(self, 'time_start_label', None)),
            ('time_end_label', getattr(self, 'time_end_label', None)),
            ('tasks_count_label', getattr(self, 'tasks_count_label', None))
        ]
        
        # Clean up all canvas objects
        for attr_name, obj_id in canvas_objects:
            if obj_id is not None:
                try:
                    self.canvas.delete(obj_id)
                except tk.TclError:
                    # Object may have already been deleted
                    pass
                setattr(self, attr_name, None)
        
        # Clear canvas reference to prevent memory leaks
        self.canvas = None

    def get_time_range(self):
        return time(self.start_hour, self.start_minute), time(self.end_hour, self.end_minute)
    
    def is_active_at(self, current_time: time) -> bool:
        """Check if this card is active at the given time."""
        start_time = time(self.start_hour, self.start_minute)
        end_time = time(self.end_hour, self.end_minute)
        return start_time <= current_time < end_time

    def update_card_visuals(self, new_start_hour, new_start_minute, start_of_workday, pixels_per_hour, offset_y, now=None, show_start_time=True, show_end_time=True, width=None, is_moving=False):
        """Move/resize the card, update progress bar, and update label positions/visibility. Also update width if provided."""
        if now is None:
            now = self.now_provider().time() if self.now_provider else time(0, 0)
        if width is not None:
            self.card_left = int(width * 0.15)
            self.card_right = int(width * 0.85)
        # Calculate new end time
        card_duration_minutes = (self.end_hour - self.start_hour) * 60 + (self.end_minute - self.start_minute)
        #log_debug(f"Cards duration in minutes: {card_duration_minutes}")
        total_minutes = new_start_hour * 60 + new_start_minute + card_duration_minutes
        total_minutes = total_minutes % (24 * 60)
        self.end_hour = total_minutes // 60
        self.end_minute = total_minutes % 60
        self.start_hour = new_start_hour
        self.start_minute = new_start_minute % 60
        self.y = (self.start_hour - start_of_workday) * pixels_per_hour + 100 + int(self.start_minute * pixels_per_hour / 60) + offset_y
        height = ((self.end_hour - self.start_hour) * pixels_per_hour) + int((self.end_minute - self.start_minute) * pixels_per_hour / 60)
        self.height = height
        # Move/resize card
        self.canvas.coords(self.card, self.card_left, self.y, self.card_right, self.y + height)
        # Update progress bar - always move it with the card even when hidden
        should_show_progress = not is_moving and ( time(self.start_hour, self.start_minute) <= now < time(self.end_hour, self.end_minute) )
        if should_show_progress:
            total_seconds = (self.end_hour - self.start_hour) * 3600 + (self.end_minute - self.start_minute) * 60
            elapsed_seconds = (now.hour - self.start_hour) * 3600 + (now.minute - self.start_minute) * 60 + now.second
            progress = min(elapsed_seconds / total_seconds, 1) if total_seconds > 0 else 1
            fill_right = self.card_left + int((self.card_right - self.card_left) * progress)
            if not hasattr(self, 'progress') or self.progress is None:
                self.progress = self.canvas.create_rectangle(self.card_left, self.y, fill_right, self.y + self.height, fill="green", outline="")
                self.setup_card_progress_actions(self.canvas)
            else:
                self.canvas.coords(self.progress, self.card_left, self.y, fill_right, self.y + self.height)
            self.canvas.itemconfig(self.progress, state="normal")
            self.canvas.itemconfig(self.card, fill=self.active_color)
            self.canvas.tag_raise(self.label)
        else:
            if hasattr(self, 'progress') and self.progress is not None:
                self.canvas.delete(self.progress)
                self.progress = None
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

        # Update or create tasks count label
        tasks = self.activity.get("tasks", [])
        tasks_done = getattr(self, '_tasks_done', [False] * len(tasks))
        remaining_tasks = [t for t, done in zip(tasks, tasks_done) if not done]
        if remaining_tasks:
            tasks_text = f"Tasks: {len(remaining_tasks)}"
            if not hasattr(self, 'tasks_count_label') or self.tasks_count_label is None:
                self.tasks_count_label = self.canvas.create_text(
                    self.card_right - 5, self.y + self.height - 5,
                    text=tasks_text,
                    font=("Arial", 8, "bold"), anchor="se", fill="#0a0a0a"
                )
                tag = f"card_{self.card}"
                self.canvas.itemconfig(self.tasks_count_label, tags=(tag))
            else:
                self.canvas.coords(self.tasks_count_label, self.card_right - 5, self.y + self.height - 5)
                self.canvas.itemconfig(self.tasks_count_label, text=tasks_text, state="normal")
        else:
            if hasattr(self, 'tasks_count_label') and self.tasks_count_label is not None:
                self.canvas.itemconfig(self.tasks_count_label, state="hidden")

        self.being_modified = False  # Reset being_modified flag after updating visuals

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
            next_start_time = TimeUtils.parse_time_with_validation(next_activity["start_time"])
            next_start_hour, next_start_minute = next_start_time.hour, next_start_time.minute
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
