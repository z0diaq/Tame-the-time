from tkinter import Canvas

def draw_timeline(canvas: Canvas, width: int, start_hour: int, end_hour: int, pixels_per_hour: int, offset_y: int):
    """Draw the timeline on the canvas."""
    for hour in range(start_hour, end_hour + 1):
        y = (hour - start_hour) * pixels_per_hour + 100 + offset_y
        canvas.create_line(0, y, width, y, fill="gray", dash=(2, 2))
        canvas.create_text(5, y, anchor="nw", text=f"{hour}:00", fill="black")
