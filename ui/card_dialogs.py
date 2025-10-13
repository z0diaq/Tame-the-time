import tkinter as tk
import tkinter.messagebox as messagebox
from utils.time_utils import get_current_activity
from utils.logging import log_error, log_info
from utils.translator import t

def open_edit_card_window(app, card_obj, on_cancel_callback=None):
    """Open a dialog to edit a card's details."""
    edit_win = tk.Toplevel(app)
    edit_win.title(t("window.edit_card"))
    edit_win.geometry("350x350")
    edit_win.transient(app)
    edit_win.grab_set()

    tk.Label(edit_win, text=t("label.title")).pack(anchor="w", padx=10, pady=(10, 0))
    title_var = tk.StringVar(value=card_obj.activity.get("name", ""))
    title_entry = tk.Entry(edit_win, textvariable=title_var)
    title_entry.pack(fill="x", padx=10)

    tk.Label(edit_win, text=t("label.description")).pack(anchor="w", padx=10, pady=(10, 0))
    desc_text = tk.Text(edit_win, height=6)
    desc = "\n".join(card_obj.activity.get("description", []))
    desc_text.insert("1.0", desc)
    desc_text.pack(fill="both", expand=True, padx=10)

    # --- Tasks edit box ---
    tk.Label(edit_win, text=t("label.tasks_one_per_line")).pack(anchor="w", padx=10, pady=(10, 0))
    tasks_text = tk.Text(edit_win, height=5)
    tasks = card_obj.activity.get("tasks", [])
    task_names = [
        task.get("name") if isinstance(task, dict) else task
        for task in tasks
    ]
    tasks_text.insert("1.0", "\n".join(task_names))
    tasks_text.pack(fill="both", expand=True, padx=10)

    btn_frame = tk.Frame(edit_win)
    btn_frame.pack(fill="x", pady=10)
    def on_save():
        new_title = title_var.get().strip()
        new_desc = desc_text.get("1.0", "end-1c").strip().splitlines()
        new_tasks = [line.strip() for line in tasks_text.get("1.0", "end-1c").splitlines() if line.strip()]
        
        # Check for duplicate task names within this activity
        task_counts = {}
        for task in new_tasks:
            task_counts[task] = task_counts.get(task, 0) + 1
        
        duplicates = [task for task, count in task_counts.items() if count > 1]
        if duplicates:
            duplicate_list = ", ".join(duplicates)
            result = messagebox.askyesno(
                t("dialog.duplicate_task_names"),
                t("message.duplicate_tasks", duplicate_list=duplicate_list),
                parent=edit_win
            )
            if not result:
                return  # User chose "No", stay in dialog
        
        # Get original tasks for comparison (extract names from both formats)
        original_tasks = set()
        original_task_objects = card_obj.activity.get("tasks", [])
        for task in original_task_objects:
            if isinstance(task, str):
                original_tasks.add(task)
            elif isinstance(task, dict) and "name" in task:
                original_tasks.add(task["name"])
        
        new_tasks_set = set(new_tasks)
        
        # Find removed and added tasks
        removed_tasks = original_tasks - new_tasks_set
        added_tasks = new_tasks_set - original_tasks
        
        # Build new task objects preserving UUIDs for existing tasks
        new_task_objects = []
        for new_task_name in new_tasks:
            # Find if this task existed before (to preserve UUID)
            existing_task_obj = None
            for orig_task in original_task_objects:
                if isinstance(orig_task, str) and orig_task == new_task_name:
                    existing_task_obj = orig_task
                    break
                elif isinstance(orig_task, dict) and orig_task.get("name") == new_task_name:
                    existing_task_obj = orig_task
                    break
            
            if existing_task_obj and isinstance(existing_task_obj, dict):
                # Preserve existing task object with UUID
                new_task_objects.append(existing_task_obj)
            elif existing_task_obj and isinstance(existing_task_obj, str):
                # Convert string to object format (will get UUID during migration)
                new_task_objects.append({
                    "name": new_task_name,
                    "uuid": str(__import__('uuid').uuid4())
                })
            else:
                # New task - create object format
                new_task_objects.append({
                    "name": new_task_name,
                    "uuid": str(__import__('uuid').uuid4())
                })
        
        # Update schedule and card activity using ID-based lookup
        activity_id = card_obj.activity.get("id")
        if activity_id:
            activity = app.find_activity_by_id(activity_id)
            if activity:
                activity["name"] = new_title
                activity["description"] = new_desc
                activity["tasks"] = new_task_objects  # Use new task objects with UUIDs
            else:
                log_error(f"Activity with ID '{activity_id}' not found in schedule.")
        else:
            log_error(f"Activity '{card_obj.activity['name']}' has no ID - cannot update schedule.")
        card_obj.activity["name"] = new_title
        card_obj.activity["description"] = new_desc
        card_obj.activity["tasks"] = new_task_objects  # Use new task objects with UUIDs
        
        # Handle added tasks - add to database
        if added_tasks and hasattr(app, 'task_tracking_service'):
            activity_id = card_obj.activity.get("id")
            if not activity_id:
                log_error(f"Activity '{new_title}' has no ID, cannot add task entries")
            else:
                for task_name in added_tasks:
                    # Find the UUID for this task from new_task_objects
                    existing_uuid = None
                    for task_obj in new_task_objects:
                        if isinstance(task_obj, dict) and task_obj.get("name") == task_name:
                            existing_uuid = task_obj.get("uuid")
                            break
                    
                    task_uuid = app.task_tracking_service.add_new_task_entry(activity_id, task_name, existing_uuid)
                    if task_uuid:
                        log_info(f"Added new task entry for '{task_name}' with UUID '{task_uuid}' in activity '{new_title}'")
                    else:
                        log_error(f"Failed to add task entry for '{task_name}' in activity '{new_title}'")

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
        # Raise timeline above cards after card update
        app.raise_timeline_above_cards()
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
    # Check if the activity has unsaved tasks
    if hasattr(app, 'task_tracking_service'):
        if app.task_tracking_service.has_unsaved_tasks(card_obj.activity):
            unsaved_tasks = app.task_tracking_service.get_unsaved_tasks(card_obj.activity)
            unsaved_list = "\n".join([f"• {task}" for task in unsaved_tasks])
            
            messagebox.showwarning(
                t("dialog.unsaved_tasks"),
                t("message.unsaved_tasks_warning", unsaved_list=unsaved_list),
                parent=app
            )
            return  # Don't open the dialog
    
    tasks_win = tk.Toplevel(app)
    tasks_win.title(t("window.tasks_for", activity_name=card_obj.activity['name']))
    tasks_win.geometry("400x350")
    tasks_win.transient(app)
    tasks_win.grab_set()

    task_listbox = tk.Listbox(tasks_win)
    task_listbox.pack(fill="both", expand=True, padx=10, pady=10)

    app.normalize_tasks_done(card_obj)
    
    # Load task done states from database if available
    if hasattr(app, 'task_tracking_service'):
        try:
            done_states = app.task_tracking_service.get_task_done_states()
            activity_id = card_obj.activity.get("id")
            if activity_id:
                tasks = card_obj.activity.get("tasks", [])
                for i, task in enumerate(tasks):
                    # Handle both string and object task formats
                    if isinstance(task, str):
                        task_name = task
                        task_uuid = None
                    elif isinstance(task, dict) and "name" in task:
                        task_name = task["name"]
                        task_uuid = task.get("uuid")
                    else:
                        continue
                    
                    # Get task UUIDs for this activity and task name (if not from YAML)
                    if not task_uuid:
                        task_uuids = app.task_tracking_service.get_task_uuids_by_activity_and_name(activity_id, task_name)
                        if task_uuids:
                            task_uuid = task_uuids[0]
                    
                    if task_uuid and task_uuid in done_states:
                        card_obj._tasks_done[i] = done_states[task_uuid]
                        # Store UUID for later use
                        if not hasattr(card_obj, '_task_uuids'):
                            card_obj._task_uuids = [None] * len(tasks)
                        card_obj._task_uuids[i] = task_uuid
        except Exception as e:
            log_error(f"Failed to load task done states from database: {e}")

    # Create a copy of tasks_done for editing (don't modify original until Save)
    tasks_done_copy = card_obj._tasks_done.copy()

    tasks = card_obj.activity.get("tasks", [])
    for i, task in enumerate(tasks):
        # Handle both string and object task formats for display
        if isinstance(task, str):
            task_name = task
        elif isinstance(task, dict) and "name" in task:
            task_name = task["name"]
        else:
            task_name = str(task)  # Fallback
        
        display = f"{t('task.done_prefix')} {task_name}" if tasks_done_copy[i] else task_name
        task_listbox.insert("end", display)

    # Create "Toggle Done" button (initially disabled)
    toggle_done_btn = tk.Button(tasks_win, text=t("button.mark_as_done"), state="disabled")
    toggle_done_btn.pack(pady=(0, 10))

    def find_first_not_done():
        """Find the index of the first task that is not marked as done."""
        for i, done in enumerate(tasks_done_copy):
            if not done:
                return i
        return None

    def update_button_state():
        """Update the Toggle Done button state and text based on current selection."""
        selected_indices = task_listbox.curselection()
        if selected_indices:
            idx = selected_indices[0]
            if not tasks_done_copy[idx]:
                toggle_done_btn.config(state="normal", text=t("button.mark_as_done"))
            else:
                toggle_done_btn.config(state="normal", text=t("button.mark_as_undone"))
        else:
            toggle_done_btn.config(state="disabled", text=t("button.mark_as_done"))

    def on_listbox_select(event):
        """Handle listbox selection changes."""
        update_button_state()

    def toggle_task_done():
        """Toggle the done state of the selected task."""
        selected_task_index = task_listbox.curselection()
        if selected_task_index:
            idx = selected_task_index[0]
            task = tasks[idx]
            
            # Handle both string and object task formats
            if isinstance(task, str):
                task_name = task
                task_uuid_from_yaml = None
            elif isinstance(task, dict) and "name" in task:
                task_name = task["name"]
                task_uuid_from_yaml = task.get("uuid")
            else:
                log_error(f"Invalid task format: {task}")
                return
            
            if not tasks_done_copy[idx]:
                # Mark task as done
                tasks_done_copy[idx] = True
                task_listbox.delete(idx)
                task_listbox.insert(idx, f"{t('task.done_prefix')} {task_name}")
                
                # Update database if task tracking service is available
                if hasattr(app, 'task_tracking_service'):
                    # Get or create task UUID for this task
                    task_uuid = task_uuid_from_yaml  # Use UUID from YAML if available
                    if not task_uuid and hasattr(card_obj, '_task_uuids') and card_obj._task_uuids and idx < len(card_obj._task_uuids):
                        task_uuid = card_obj._task_uuids[idx]
                    
                    if not task_uuid:
                        # Create new task entry if UUID doesn't exist
                        activity_id = card_obj.activity.get("id")
                        if activity_id:
                            # Try to get UUID from the task object if available
                            task_uuid_to_use = None
                            if isinstance(task, dict):
                                task_uuid_to_use = task.get("uuid")
                            
                            task_uuid = app.task_tracking_service.add_new_task_entry(activity_id, task_name, task_uuid_to_use)
                            if not hasattr(card_obj, '_task_uuids'):
                                card_obj._task_uuids = [None] * len(tasks)
                            card_obj._task_uuids[idx] = task_uuid
                    
                    if task_uuid:
                        success = app.task_tracking_service.mark_task_done(task_uuid)
                        if success:
                            log_info(f"Marked task '{task_name}' (UUID: {task_uuid}) as done in database")
                        else:
                            log_error(f"Failed to mark task '{task_name}' (UUID: {task_uuid}) as done in database")
                    else:
                        log_error(f"Could not get or create UUID for task '{task_name}'")
                
                # Find and select next not-done task
                next_not_done = find_first_not_done()
                if next_not_done is not None:
                    task_listbox.selection_clear(0, "end")
                    task_listbox.selection_set(next_not_done)
                    task_listbox.see(next_not_done)  # Ensure it's visible
                else:
                    # Keep current selection
                    task_listbox.selection_set(idx)
            else:
                # Mark task as undone
                tasks_done_copy[idx] = False
                task_listbox.delete(idx)
                task_listbox.insert(idx, task_name)
                
                # Update database if task tracking service is available
                if hasattr(app, 'task_tracking_service'):
                    # Get task UUID for this task (prefer YAML UUID, then stored UUID)
                    task_uuid = task_uuid_from_yaml
                    if not task_uuid and hasattr(card_obj, '_task_uuids') and card_obj._task_uuids and idx < len(card_obj._task_uuids):
                        task_uuid = card_obj._task_uuids[idx]
                    
                    if task_uuid:
                        success = app.task_tracking_service.mark_task_undone(task_uuid)
                        if success:
                            log_info(f"Marked task '{task_name}' (UUID: {task_uuid}) as undone in database")
                        else:
                            log_error(f"Failed to mark task '{task_name}' (UUID: {task_uuid}) as undone in database")
                    else:
                        log_error(f"Could not find UUID for task '{task_name}' to mark as undone")
                
                # Keep current selection
                task_listbox.selection_set(idx)
            
            # Update button state
            update_button_state()
        tasks_win.lift()

    # Bind listbox selection event
    task_listbox.bind("<<ListboxSelect>>", on_listbox_select)
    
    # Configure the toggle_task_done command for the button
    toggle_done_btn.config(command=toggle_task_done)

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
        # Raise timeline above cards after card update
        app.raise_timeline_above_cards()
        tasks_win.destroy()
        if hasattr(card_obj, '_tasks_done_callback'):
            card_obj._tasks_done_callback()
    def on_cancel():
        # Discard changes - don't modify card_obj._tasks_done
        tasks_win.destroy()
    tk.Button(btn_frame, text=t("button.save"), command=on_save).pack(side="left", padx=20)
    tk.Button(btn_frame, text=t("button.cancel"), command=on_cancel).pack(side="right", padx=20)

    # Focus the listbox when the window opens
    task_listbox.focus_set()