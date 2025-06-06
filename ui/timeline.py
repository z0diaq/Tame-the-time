from tkinter import Canvas
from datetime import time

def draw_timeline(canvas: Canvas, width: int, start_hour: int, end_hour: int, pixels_per_hour: int, offset_y: int, current_time=None, granularity=60):
    """Draw the timeline on the canvas. granularity in minutes (default 60)."""
    total_minutes = (end_hour - start_hour) * 60
    created_objects = []
    for minute in range(0, total_minutes + 1, granularity):
        hour = start_hour + minute // 60
        min_in_hour = minute % 60
        y = (minute / 60) * pixels_per_hour + 100 + offset_y
        color = "gray" if min_in_hour == 0 else "#dddddd"
        dash = (2, 2) if min_in_hour == 0 else (1, 4)
        line = canvas.create_line(0, y, width, y, fill=color, dash=dash)
        created_objects.append(line)
        if min_in_hour == 0:
            text = canvas.create_text(5, y, anchor="nw", text=f"{hour}:00", fill="black")
            created_objects.append(text)
        elif granularity < 60:
            text = canvas.create_text(36, y, anchor="nw", text=f"{hour:02d}:{min_in_hour:02d}", fill="#888888", font=("Arial", 7))
            created_objects.append(text)

    return created_objects
