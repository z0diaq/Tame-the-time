import tkinter as tk
import tkinter.messagebox as messagebox
from utils.time_utils import get_current_activity
from utils.logging import log_error

def open_edit_card_window(app, card_obj, on_cancel_callback=None):
    """Open a dialog to edit a card's details."""
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
        app.update_status_bar()
    def on_cancel():
        if on_cancel_callback:
            on_cancel_callback(card_obj)
        edit_win.destroy()
    tk.Button(btn_frame, text="Save", command=on_save).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)
    title_entry.focus_set()

def open_card_tasks_window(app, card_obj):
    """Open a dialog to edit the tasks for a card."""
    tasks_win = tk.Toplevel(app)
    tasks_win.title(f"Tasks for {card_obj.activity['name']}")
    tasks_win.geometry("400x350")
    tasks_win.transient(app)
    tasks_win.grab_set()

    task_listbox = tk.Listbox(tasks_win)
    task_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    app.normalize_tasks_done(card_obj)

    # Create a copy of tasks_done for editing (don't modify original until Save)
    tasks_done_copy = card_obj._tasks_done.copy()

    tasks = card_obj.activity.get("tasks", [])
    for i, task in enumerate(tasks):
        display = f"[Done] {task}" if tasks_done_copy[i] else task
        task_listbox.insert("end", display)

    # Create "Mark as Done" button (initially disabled)
    mark_done_btn = tk.Button(tasks_win, text="Mark as Done", state="disabled")
    mark_done_btn.pack(pady=(0, 10))

    def find_first_not_done():
        """Find the index of the first task that is not marked as done."""
        for i, done in enumerate(tasks_done_copy):
            if not done:
                return i
        return None

    def update_button_state():
        """Update the Mark as Done button state based on current selection."""
        selected_indices = task_listbox.curselection()
        if selected_indices:
            idx = selected_indices[0]
            # Enable button only if selected task is not done
            if not tasks_done_copy[idx]:
                mark_done_btn.config(state="normal")
            else:
                mark_done_btn.config(state="disabled")
        else:
            mark_done_btn.config(state="disabled")

    def on_listbox_select(event):
        """Handle listbox selection changes."""
        update_button_state()

    def mark_task_done():
        """Mark the selected task as done."""
        selected_task_index = task_listbox.curselection()
        if selected_task_index:
            idx = selected_task_index[0]
            if not tasks_done_copy[idx]:
                # Mark task as done in the copy
                tasks_done_copy[idx] = True
                task = tasks[idx]
                task_listbox.delete(idx)
                task_listbox.insert(idx, f"[Done] {task}")
                
                # Find and select next not-done task
                next_not_done = find_first_not_done()
                if next_not_done is not None:
                    task_listbox.selection_clear(0, "end")
                    task_listbox.selection_set(next_not_done)
                    task_listbox.see(next_not_done)  # Ensure it's visible
                else:
                    # No more not-done tasks, clear selection
                    task_listbox.selection_clear(0, "end")
                
                # Update button state
                update_button_state()
        tasks_win.lift()

    # Bind listbox selection event
    task_listbox.bind("<<ListboxSelect>>", on_listbox_select)
    
    # Configure the mark_task_done command for the button
    mark_done_btn.config(command=mark_task_done)

    # Select first not-done task when dialog opens
    first_not_done = find_first_not_done()
    if first_not_done is not None:
        task_listbox.selection_set(first_not_done)
        task_listbox.see(first_not_done)  # Ensure it's visible
        update_button_state()

    btn_frame = tk.Frame(tasks_win)
    btn_frame.pack(fill="x", pady=10)
    def on_save():
        # Apply changes from copy to actual card_obj
        card_obj._tasks_done = tasks_done_copy.copy()
        
        card_obj.update_card_visuals(
            card_obj.start_hour,
            card_obj.start_minute,
            app.start_hour,
            app.pixels_per_hour,
            app.offset_y,
            now=app.now_provider().time(),
            width=app.winfo_width()
        )
        tasks_win.destroy()
        if hasattr(card_obj, '_tasks_done_callback'):
            card_obj._tasks_done_callback()
    def on_cancel():
        # Discard changes - don't modify card_obj._tasks_done
        tasks_win.destroy()
    tk.Button(btn_frame, text="Save", command=on_save).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)

    # Focus the listbox when the window opens
    task_listbox.focus_set()