import tkinter as tk
import tkinter.messagebox as messagebox
from ui.card_dialogs import open_edit_card_window, open_card_tasks_window
from ui.task_card import TaskCard
from utils.time_utils import round_to_nearest_5_minutes
from utils.logging import log_debug
from utils.translator import t

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
            """Open a dialog to edit the card under cursor."""
            open_edit_card_window(app, card_under_cursor)
        menu.add_command(label=t("context_menu.edit"), command=edit_card)
        def clone_card():
            """Clone the card under cursor."""
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
        menu.add_command(label=t("context_menu.clone"), command=clone_card)
        def open_card_tasks():
            """Open a dialog to edit the tasks for the card under cursor."""
            open_card_tasks_window(app, card_under_cursor)
        # Check for tasks in the card's activity directly, then fallback to schedule lookup
        activity = card_under_cursor.activity
        if 'tasks' not in activity or not activity['tasks']:
            # Fallback: try to find updated activity in schedule
            activity_id = card_under_cursor.activity.get("id")
            schedule_activity = app.find_activity_by_id(activity_id) if activity_id else None
            if schedule_activity:
                activity = schedule_activity
        
        # Show Tasks menu option if there are tasks
        if 'tasks' in activity and activity['tasks']:
            menu.add_command(label=t("context_menu.tasks"), command=open_card_tasks)
        
        def remove_card():
            """Remove the card under cursor with confirmation."""
            card_name = card_under_cursor.activity.get('name', 'this card')
            if messagebox.askyesno(t("dialog.confirm_removal"), t("message.confirm_remove_card", card_name=card_name)):
                if card_under_cursor in app.cards:
                    app.cards.remove(card_under_cursor)
                    card_under_cursor.delete()
                    
                    # Find and remove the corresponding activity from schedule
                    # Try to find by ID first, then by matching properties
                    activity_id = card_under_cursor.activity.get("id")
                    activity_to_remove = None
                    
                    if activity_id:
                        # Find by ID
                        for activity in app.schedule:
                            if activity.get("id") == activity_id:
                                activity_to_remove = activity
                                break
                    
                    if not activity_to_remove:
                        # Fallback: find by matching name and times
                        card_dict = card_under_cursor.to_dict()
                        for activity in app.schedule:
                            if (activity.get("name") == card_dict["name"] and
                                activity.get("start_time") == card_dict["start_time"] and
                                activity.get("end_time") == card_dict["end_time"]):
                                activity_to_remove = activity
                                break
                    
                    if activity_to_remove:
                        app.schedule.remove(activity_to_remove)
                    else:
                        log_debug(f"Warning: Could not find activity to remove for card '{card_name}'")
                    
                    app.update_cards_after_size_change()
                    app.schedule_changed = True
        menu.add_command(label=t("context_menu.remove"), command=remove_card)
    elif event.y > 30:
        def add_card():
            """Add a new card at the cursor position."""
            y_relative = event.y - 100 - app.offset_y
            total_minutes = round_to_nearest_5_minutes(y_relative * 60 / app.pixels_per_hour)
            start_hour = app.start_hour + total_minutes // 60
            start_minute = total_minutes % 60
            total_minutes += 25
            end_hour = app.start_hour + total_minutes // 60
            end_minute = total_minutes % 60
            activity = {
                "id": app.generate_activity_id(),
                "name": t("context_menu.new_task"),
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
        menu.add_command(label=t("context_menu.new"), command=add_card)
        def remove_all_cards():
            """Remove all cards from the schedule."""
            if messagebox.askyesno(t("dialog.confirm_remove_all"), t("message.confirm_remove_all_cards")):
                for card_obj in app.cards:
                    card_obj.delete()
                app.cards.clear()
                app.schedule.clear()
                app.schedule_changed = True
        menu.add_command(label=t("context_menu.remove_all"), command=remove_all_cards)
        menu.add_separator()
        # Add disable auto-centering checkbutton
        disable_centering_var = tk.BooleanVar(value=getattr(app, 'disable_auto_centering', False))
        menu.add_checkbutton(
            label=t("menu.disable_auto_centering"), 
            variable=disable_centering_var,
            command=app.toggle_disable_auto_centering
        )
    else:
        return
    menu.tk_popup(event.x_root, event.y_root)
