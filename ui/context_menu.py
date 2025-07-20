import tkinter as tk
import tkinter.messagebox as messagebox
from ui.card_dialogs import open_edit_card_window, open_card_tasks_window
from ui.task_card import TaskCard
from utils.time_utils import round_to_nearest_5_minutes
from utils.logging import log_debug

def show_canvas_context_menu(app, event):
    # Determine if click is on a card
    items = app.canvas.find_overlapping(event.x, event.y, event.x, event.y)
    card_ids = [card_obj.card for card_obj in app.cards]
    log_debug(f"Context menu requested at {event.x}, {event.y}, items: {items}, card_ids: {card_ids}")
    menu = tk.Menu(app, tearoff=0)
    card_under_cursor = None
    for card_obj in app.cards:
        if card_obj.card in items:
            card_under_cursor = card_obj
            break
    if card_under_cursor:
        # Show context menu for the card under cursor
        def edit_card():
            open_edit_card_window(app, card_under_cursor)
        menu.add_command(label="Edit", command=edit_card)
        def clone_card():
            # Clone the card under cursor
            new_card = card_under_cursor.clone()
            new_card.start_hour = card_under_cursor.end_hour
            new_card.start_minute = card_under_cursor.end_minute
            current_card_length = (card_under_cursor.end_hour - card_under_cursor.start_hour) * 60 + (card_under_cursor.end_minute - card_under_cursor.start_minute)
            new_card.end_hour = (new_card.start_hour + (current_card_length // 60)) % 24
            new_card.end_minute = (new_card.start_minute + current_card_length) % 60
            draw_end_time = True
            for other_card in app.cards:
                if (other_card.start_hour == new_card.end_hour and other_card.start_minute == new_card.end_minute):
                    draw_end_time = False
                    break
            new_card.draw(canvas=app.canvas, now=app.now_provider().time(), draw_end_time=draw_end_time)
            app.bind_mouse_actions(new_card)
            app.cards.append(new_card)
            app.schedule.append(new_card.to_dict())
            app.update_cards_after_size_change()
            app.schedule_changed = True
        menu.add_command(label="Clone", command=clone_card)
        def remove_card():
            if card_under_cursor in app.cards:
                app.cards.remove(card_under_cursor)
                card_under_cursor.delete()
                app.schedule.remove(card_under_cursor.to_dict())
                app.update_cards_after_size_change()
                app.schedule_changed = True
        menu.add_command(label="Remove", command=remove_card)
        def open_card_tasks():
            open_card_tasks_window(app, card_under_cursor)
        activity = app.find_activity_by_name(card_under_cursor.activity["name"])
        if 'tasks' in activity and activity['tasks']:
            menu.add_command(label="Tasks", command=open_card_tasks)
    elif event.y > 30:
        def add_card():
            y_relative = event.y - 100 - app.offset_y
            total_minutes = round_to_nearest_5_minutes(y_relative * 60 / app.pixels_per_hour)
            start_hour = app.start_hour + total_minutes // 60
            start_minute = total_minutes % 60
            total_minutes += 25
            end_hour = app.start_hour + total_minutes // 60
            end_minute = total_minutes % 60
            activity = {
                "name": "New Task",
                "description": [],
                "start_time": f"{start_hour:02d}:{start_minute:02d}",
                "end_time": f"{end_hour:02d}:{end_minute:02d}"
            }
            new_card = TaskCard(
                activity=activity,
                start_of_workday=app.start_hour,
                pixels_per_hour=app.pixels_per_hour,
                offset_y=app.offset_y,
                width=app.winfo_width(),
                now_provider=app.now_provider
            )
            new_card.draw(canvas=app.canvas, draw_end_time=True)
            app.bind_mouse_actions(new_card)
            app.cards.append(new_card)
            app.schedule.append(new_card.to_dict())
            app.update_cards_after_size_change()
            open_edit_card_window(app, new_card)
            app.schedule_changed = True
        menu.add_command(label="New", command=add_card)
        def remove_all_cards():
            if messagebox.askyesno("Confirm", "Are you sure you want to remove all cards?"):
                for card_obj in app.cards:
                    card_obj.delete()
                app.cards.clear()
                app.schedule.clear()
                app.schedule_changed = True
        menu.add_command(label="Remove all", command=remove_all_cards)
    else:
        return
    menu.tk_popup(event.x_root, event.y_root)
