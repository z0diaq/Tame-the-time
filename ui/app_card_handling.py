from utils.time_utils import round_to_nearest_5_minutes
from utils.logging import log_debug
import tkinter as tk

def on_card_drag(app, event):
    if not app._drag_data["item_ids"] or abs(event.y - app._drag_data["start_y"]) <= 20:
        return
    app.last_action = app.now_provider()
    app._drag_data["dragging"] = True
    dragged_id = app._drag_data["item_ids"][0]
    app.schedule_changed = True  # Mark schedule as changed
    if app._drag_data.get("resize_mode") == "top":
        # Resize from top
        y_card_bottom = app.canvas.coords(dragged_id)[3]
        new_top = min(event.y, y_card_bottom - 20)
        snapped_minutes = round_to_nearest_5_minutes(int((new_top - 100 - app.offset_y) * 60 / app.pixels_per_hour))
        snapped_y = int(snapped_minutes * app.pixels_per_hour / 60) + 100 + app.offset_y
        app.canvas.coords(dragged_id, app.canvas.coords(dragged_id)[0], snapped_y, app.canvas.coords(dragged_id)[2], y_card_bottom)
    elif app._drag_data.get("resize_mode") == "bottom":
        # Resize from bottom
        y_card_top = app.canvas.coords(dragged_id)[1]
        new_bottom = max(event.y, y_card_top + 20)
        snapped_minutes = round_to_nearest_5_minutes(int((new_bottom - 100 - app.offset_y) * 60 / app.pixels_per_hour))
        snapped_y = int(snapped_minutes * app.pixels_per_hour / 60) + 100 + app.offset_y
        app.canvas.coords(dragged_id, app.canvas.coords(dragged_id)[0], y_card_top, app.canvas.coords(dragged_id)[2], snapped_y)
    else:
        # Normal drag (move)
        y = event.y
        y_relative = y - 100 - app.offset_y - app._drag_data["diff_y"]
        total_minutes = int(y_relative * 60 / app.pixels_per_hour)
        snapped_minutes = round_to_nearest_5_minutes(total_minutes)
        snapped_y = int(snapped_minutes * app.pixels_per_hour / 60) + 100 + app.offset_y
        delta_y = snapped_y - app.canvas.coords(dragged_id)[1]
        log_debug(f"Item_ids: {app._drag_data['item_ids']}")
        for item_id in app._drag_data["item_ids"]:
            app.canvas.move(item_id, 0, delta_y)
        app._drag_data["offset_y"] = event.y + (snapped_y - y)

def on_card_press(app, event):
    tags = app.canvas.gettags(tk.CURRENT)
    log_debug(f"Card pressed: {tags}")
    app._drag_data["item_ids"] = app.canvas.find_withtag(tags[0])
    app._drag_data["offset_y"] = event.y
    app._drag_data["start_y"] = event.y
    app._drag_data["dragging"] = False
    app._drag_data["resize_mode"] = None
    dragged_id = app._drag_data["item_ids"][0]
    y_card_top = app.canvas.coords(dragged_id)[1]
    app._drag_data["diff_y"] = event.y - y_card_top
    log_debug(f"Dragging card: {dragged_id}, Tags: {tags}")
    # Detect if click is near top or bottom for resize
    y_card_top = app.canvas.coords(dragged_id)[1]
    y_card_bottom = app.canvas.coords(dragged_id)[3]
    if abs(event.y - y_card_top) <= 10:
        app.config(cursor="top_side")
        app._drag_data["resize_mode"] = "top"
    elif abs(event.y - y_card_bottom) <= 10:
        app.config(cursor="bottom_side")
        app._drag_data["resize_mode"] = "bottom"
    else:
        app.config(cursor="fleur")
        app._drag_data["resize_mode"] = None
    # Make all other cards barely visible
    for card_obj in app.cards:
        if card_obj.card != dragged_id:
            app.canvas.itemconfig(card_obj.card, stipple="gray25")
            if card_obj.label:
                app.canvas.itemconfig(card_obj.label, fill="#cccccc")
        else:
            app.canvas.itemconfig(card_obj.card, stipple="")
            card_obj.set_being_modified(True)
            if card_obj.label:
                app.canvas.itemconfig(card_obj.label, fill="black")
    app.card_visual_changed = True
    if app.timeline_granularity != 5:
        app.timeline_granularity = 5
        app.show_timeline(granularity=5)

def on_card_release(app, event):
    app.config(cursor="")
    if not app._drag_data["item_ids"] or not app._drag_data["dragging"]:
        app._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
        app.timeline_granularity = 60
        app.show_timeline(granularity=60)
        return
    card_id = app._drag_data["item_ids"][0]
    if app._drag_data.get("resize_mode"):
        handle_card_resize(app, card_id, event.y, app._drag_data["resize_mode"])
    else:
        handle_card_snap(app, card_id, event.y)
    app._drag_data = {"item_ids": [], "offset_y": 0, "start_y": 0, "dragging": False, "resize_mode": None}
    app.timeline_granularity = 60
    app.restore_card_visuals()
    app.show_timeline(granularity=60)

def handle_card_snap(app, card_id: int, y: int):
    moved_card = next(card for card in app.cards if card.card == card_id)
    log_debug(f"Moved card: {moved_card.card}")
    y_relative = y - 100 - app.offset_y - app._drag_data["diff_y"]
    total_minutes = round_to_nearest_5_minutes(int(y_relative * 60 / app.pixels_per_hour))
    new_hour = app.start_hour + total_minutes // 60
    new_minute = total_minutes % 60
    log_debug(f"Moving card {moved_card.activity['name']} to {new_hour:02d}:{new_minute:02d}")
    idx = app.cards.index(moved_card)
    allow_end_time_label = True
    if idx < len(app.cards) - 1:
        next_card = app.cards[idx + 1]
        if next_card.start_hour == moved_card.end_hour and next_card.start_minute == moved_card.end_minute:
            allow_end_time_label = False
    now = app.now_provider().time()
    app.cards[idx].update_card_visuals(
        new_hour, new_minute, app.start_hour, app.pixels_per_hour, app.offset_y, now=now, show_end_time=allow_end_time_label, width=app.winfo_width()
    )
    app.schedule[idx] = app.cards[idx].to_dict()

def handle_card_resize(app, card_id: int, y: int, mode: str):
    moved_card = next(card for card in app.cards if card.card == card_id)
    y_card_top = app.canvas.coords(card_id)[1]
    y_card_bottom = app.canvas.coords(card_id)[3]
    if mode == "top":
        new_top = min(y, y_card_bottom - 20)
        snapped_minutes = round_to_nearest_5_minutes(int((new_top - 100 - app.offset_y) * 60 / app.pixels_per_hour))
        new_start_minutes = snapped_minutes
        new_end_minutes = int((y_card_bottom - 100 - app.offset_y) * 60 / app.pixels_per_hour)
    else:
        new_top = y_card_top
        new_bottom = max(y, y_card_top + 20)
        snapped_minutes = round_to_nearest_5_minutes(int((new_bottom - 100 - app.offset_y) * 60 / app.pixels_per_hour))
        new_start_minutes = int((y_card_top - 100 - app.offset_y) * 60 / app.pixels_per_hour)
        new_end_minutes = snapped_minutes
    new_start_hour = app.start_hour + new_start_minutes // 60
    new_start_minute = new_start_minutes % 60
    new_end_hour = app.start_hour + new_end_minutes // 60
    new_end_minute = new_end_minutes % 60
    for activity in app.schedule:
        if activity["name"] == moved_card.activity["name"]:
            activity["start_time"] = f"{new_start_hour:02d}:{new_start_minute:02d}"
            activity["end_time"] = f"{new_end_hour:02d}:{new_end_minute:02d}"
            break
    allow_end_time_label = True
    idx = app.cards.index(moved_card)
    if idx < len(app.cards) - 1:
        next_card = app.cards[idx + 1]
        if next_card.start_hour == new_end_hour and next_card.start_minute == new_end_minute:
            allow_end_time_label = False
    now = app.now_provider().time()
    moved_card.start_hour = new_start_hour
    moved_card.start_minute = new_start_minute
    moved_card.end_hour = new_end_hour
    moved_card.end_minute = new_end_minute
    moved_card.update_card_visuals(
        new_start_hour, new_start_minute, app.start_hour, app.pixels_per_hour, app.offset_y, now=now, show_end_time=allow_end_time_label, width=app.winfo_width()
    )

def on_card_motion(app, event):
    tags = app.canvas.gettags(tk.CURRENT)
    log_debug(f"Tags = {tags}")
    if not tags:
        app.config(cursor="")
        return
    dragged_id = app.canvas.find_withtag(tags[0])[0]
    y_card_top = app.canvas.coords(dragged_id)[1]
    y_card_bottom = app.canvas.coords(dragged_id)[3]
    if abs(event.y - y_card_top) <= 8:
        app.config(cursor="top_side")
    elif abs(event.y - y_card_bottom) <= 8:
        app.config(cursor="bottom_side")
    else:
        app.config(cursor="fleur")
