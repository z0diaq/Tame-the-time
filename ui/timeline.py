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

# Reposition of all timeline elements after pixels per hour change or width change
def reposition_timeline(canvas: Canvas, created_objects, pixels_per_hour: int, offset_y: int, width: int, granularity: int):
    """Reposition all timeline elements after pixels per hour change or width change."""
    # For 60m granularity, objects are [line, text, line, text, ...]
    # For 5m granularity, objects are [line, text, line, text, ...] but not every line has a text
    minute = 0
    obj_idx = 0
    total_objects = len(created_objects)
    while obj_idx < total_objects:
        obj = created_objects[obj_idx]
        coords = canvas.coords(obj)
        y = (minute / 60) * pixels_per_hour + 100 + offset_y
        if len(coords) == 4:  # Line object
            canvas.coords(obj, 0, y, width, y)
            obj_idx += 1
            # Check if next object is a text for this line
            if obj_idx < total_objects:
                next_obj = created_objects[obj_idx]
                next_coords = canvas.coords(next_obj)
                if len(next_coords) == 2:
                    # This is a text object
                    canvas.coords(next_obj, coords[0] if granularity == 60 and minute % 60 == 0 else (36 if granularity < 60 and minute % 60 != 0 else 5), y)
                    obj_idx += 1
        minute += granularity
