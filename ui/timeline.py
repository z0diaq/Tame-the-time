from tkinter import Canvas
from datetime import time
from constants import Colors

def draw_current_time_line(canvas: Canvas, width: int, start_hour: int, pixels_per_hour: int, offset_y: int, current_time, mouse_inside_window: bool):
    """Draw current time line and text on the timeline."""
    if not current_time:
        return []
    
    # Calculate position based on current time
    current_minutes = current_time.hour * 60 + current_time.minute + current_time.second / 60.0
    start_minutes = start_hour * 60
    y = ((current_minutes - start_minutes) / 60) * pixels_per_hour + 100 + offset_y
    
    # Create green dotted line with same style as hour lines
    line = canvas.create_line(0, y, width, y, fill=Colors.TIMELINE_CURRENT_TIME_LINE, dash=(2, 2))
    
    # Create time text with format based on mouse position
    time_format = "%H:%M:%S" if mouse_inside_window else "%H:%M"
    time_text = current_time.strftime(time_format)
    # Position text on the right side with some padding from the edge
    text_x = width - 5
    text = canvas.create_text(text_x, y, anchor="ne", text=time_text, fill=Colors.TIMELINE_CURRENT_TIME_TEXT, font=("Arial", 9, "bold"))
    
    return [line, text]

def draw_timeline(canvas: Canvas, width: int, start_hour: int, end_hour: int, pixels_per_hour: int, offset_y: int, current_time=None, granularity=60):
    """Draw the timeline on the canvas. granularity in minutes (default 60)."""
    total_minutes = (end_hour - start_hour) * 60
    created_objects = []
    for minute in range(0, total_minutes + 1, granularity):
        hour = start_hour + minute // 60
        min_in_hour = minute % 60
        y = (minute / 60) * pixels_per_hour + 100 + offset_y
        color = Colors.TIMELINE_HOUR_LINE if min_in_hour == 0 else Colors.TIMELINE_MINUTE_LINE
        dash = (2, 2) if min_in_hour == 0 else (1, 4)
        line = canvas.create_line(0, y, width, y, fill=color, dash=dash)
        created_objects.append(line)
        if min_in_hour == 0:
            text = canvas.create_text(5, y, anchor="nw", text=f"{hour}:00", fill=Colors.TIMELINE_TEXT)
            created_objects.append(text)
        elif granularity < 60:
            text = canvas.create_text(36, y, anchor="nw", text=f"{hour:02d}:{min_in_hour:02d}", fill=Colors.TIMELINE_MINUTE_TEXT, font=("Arial", 7))
            created_objects.append(text)

    return created_objects

def reposition_current_time_line(canvas: Canvas, current_time_objects, start_hour: int, pixels_per_hour: int, offset_y: int, width: int, current_time, mouse_inside_window: bool):
    """Reposition current time line and update text format based on mouse position."""
    if not current_time_objects or len(current_time_objects) != 2:
        return
    
    # Calculate new position
    current_minutes = current_time.hour * 60 + current_time.minute + current_time.second / 60.0
    start_minutes = start_hour * 60
    y = ((current_minutes - start_minutes) / 60) * pixels_per_hour + 100 + offset_y
    
    # Reposition line
    line = current_time_objects[0]
    canvas.coords(line, 0, y, width, y)
    
    # Reposition and update text
    text = current_time_objects[1]
    time_format = "%H:%M:%S" if mouse_inside_window else "%H:%M"
    time_text = current_time.strftime(time_format)
    # Position text on the right side with some padding from the edge
    text_x = width - 5
    canvas.coords(text, text_x, y)
    canvas.itemconfig(text, text=time_text)

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
