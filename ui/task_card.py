from datetime import datetime, time
from tkinter import Canvas
from typing import Dict, List, Tuple

def create_task_cards(
    canvas: Canvas,
    schedule: List[Dict],
    start_hour: int,
    pixels_per_hour: int,
    offset_y: int,
    width: int
) -> List[Tuple[int, int, Dict]]:
    """Create task cards on the canvas."""
    cards = []
    now = datetime.now().time()
    card_left = int(width * 0.15)
    card_right = int(width * 0.85)
    
    for idx, activity in enumerate(schedule):
        start_hour, start_minute = map(int, activity["start_time"].split(":"))
        end_hour, end_minute = map(int, activity["end_time"].split(":"))
        y = (start_hour - start_hour) * pixels_per_hour + 100 + int(start_minute * pixels_per_hour / 60) + offset_y
        height = ((end_hour - start_hour) * pixels_per_hour) + int((end_minute - start_minute) * pixels_per_hour / 60)
        
        color = (
            "#cccccc" if time(end_hour, end_minute) <= now else
            "#ffff99" if time(start_hour, start_minute) <= now < time(end_hour, end_minute) else
            "#add8e6"
        )
        
        card = canvas.create_rectangle(card_left, y, card_right, y + height, fill=color, outline="black")
        label = canvas.create_text((card_left + card_right) // 2, y + height // 2, text=activity["name"])
        tag = f"card_{card}"
        
        canvas.itemconfig(card, tags=(tag, "card"))
        canvas.itemconfig(label, tags=(tag, "card"))
        
        time_range = f"{start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d}"
        time_label = canvas.create_text(
            (card_left + card_right) // 2,
            y + height // 2 + 12,
            text=time_range,
            font=("Arial", 8)
        )
        
        cards.append((card, label, time_label, activity))
    
    return cards
