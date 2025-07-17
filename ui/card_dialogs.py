import tkinter as tk
import tkinter.messagebox as messagebox
from utils.time_utils import get_current_activity
from utils.logging import log_debug, log_error

def open_edit_card_window(app, card_obj, on_cancel_callback=None):
    edit_win = tk.Toplevel(app)
    edit_win.title("Edit Card")
    edit_win.geometry("350x350")
    edit_win.transient(app)
    edit_win.grab_set()

    tk.Label(edit_win, text="Title:").pack(anchor="w", padx=10, pady=(10, 0))
    title_var = tk.StringVar(value=card_obj.activity.get("name", ""))
    title_entry = tk.Entry(edit_win, textvariable=title_var)
    title_entry.pack(fill="x", padx=10)

    tk.Label(edit_win, text="Description:").pack(anchor="w", padx=10, pady=(10, 0))
    desc_text = tk.Text(edit_win, height=6)
    desc = "\n".join(card_obj.activity.get("description", []))
    desc_text.insert("1.0", desc)
    desc_text.pack(fill="both", expand=True, padx=10)

    # --- Tasks edit box ---
    tk.Label(edit_win, text="Tasks (one per line):").pack(anchor="w", padx=10, pady=(10, 0))
    tasks_text = tk.Text(edit_win, height=5)
    tasks = card_obj.activity.get("tasks", [])
    tasks_text.insert("1.0", "\n".join(tasks))
    tasks_text.pack(fill="both", expand=True, padx=10)

    btn_frame = tk.Frame(edit_win)
    btn_frame.pack(fill="x", pady=10)
    def on_save():
        new_title = title_var.get().strip()
        new_desc = desc_text.get("1.0", "end-1c").strip().splitlines()
        new_tasks = [line.strip() for line in tasks_text.get("1.0", "end-1c").splitlines() if line.strip()]
        # Update schedule and card activity
        activity = app.find_activity_by_name(new_title)
        if activity:
            activity["name"] = new_title
            activity["description"] = new_desc
            activity["tasks"] = new_tasks
        else:
            log_error(f"Activity '{card_obj.activity['name']}' not found in schedule.")
        card_obj.activity["name"] = new_title
        card_obj.activity["description"] = new_desc
        card_obj.activity["tasks"] = new_tasks

        # Normalize tasks_done list
        app.normalize_tasks_done(card_obj)

        # Update card label visual
        card_obj.update_card_visuals(
            card_obj.start_hour,
            card_obj.start_minute,
            app.start_hour,
            app.pixels_per_hour,
            app.offset_y,
            now=app.now_provider().time(),
            width=app.winfo_width()
        )
        # If this is the current activity, update activity_label
        now = app.now_provider()
        current = get_current_activity(app.schedule, now)
        if current and current["name"] == new_title:
            desc = "\n".join(f"{i+1}. {pt}" for i, pt in enumerate(new_desc))
            app.activity_label.config(text=f"Actions:\n{desc}")
        edit_win.destroy()
        app.schedule_changed = True  # Mark schedule as changed
    def on_cancel():
        if on_cancel_callback:
            on_cancel_callback(card_obj)
        edit_win.destroy()
    tk.Button(btn_frame, text="Save", command=on_save).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)
    title_entry.focus_set()

def open_card_tasks_window(app, card_obj):
    tasks_win = tk.Toplevel(app)
    tasks_win.title(f"Tasks for {card_obj.activity['name']}")
    tasks_win.geometry("400x300")
    tasks_win.transient(app)
    tasks_win.grab_set()

    task_listbox = tk.Listbox(tasks_win)
    task_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    app.normalize_tasks_done(card_obj)

    tasks = card_obj.activity.get("tasks", [])
    for i, task in enumerate(tasks):
        display = f"[Done] {task}" if card_obj._tasks_done[i] else task
        task_listbox.insert("end", display)

    def mark_task_done():
        selected_task_index = task_listbox.curselection()
        if selected_task_index:
            idx = selected_task_index[0]
            if not card_obj._tasks_done[idx]:
                card_obj._tasks_done[idx] = True
                task = tasks[idx]
                task_listbox.delete(idx)
                task_listbox.insert(idx, f"[Done] {task}")
                task_listbox.selection_clear(0, "end")
                task_listbox.selection_set(idx)
        tasks_win.lift()

    tk.Button(tasks_win, text="Mark as Done", command=mark_task_done).pack(pady=(0, 10))

    btn_frame = tk.Frame(tasks_win)
    btn_frame.pack(fill="x", pady=10)
    def on_save():
        card_obj.update_card_visuals(
            card_obj.start_hour, card_obj.start_minute, app.start_hour, app.pixels_per_hour, app.offset_y, now=app.now_provider().time(), width=app.winfo_width()
        )
        tasks_win.destroy()
        app.schedule_changed = True
    def on_cancel():
        tasks_win.destroy()
    tk.Button(btn_frame, text="Save", command=on_save).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)
