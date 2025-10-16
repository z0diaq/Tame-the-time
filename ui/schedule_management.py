import os
import yaml
from datetime import datetime
import tkinter.messagebox as messagebox
from tkinter import filedialog
from utils.logging import log_info, log_error
from utils.locale_utils import get_weekday_name

def open_schedule(app):
    """Open a dialog to load a schedule file."""
    file_path = filedialog.askopenfilename(
        title="Open Schedule File",
        filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
    )
    if not file_path:
        return
    try:
        with open(file_path, 'r') as f:
            new_schedule = yaml.safe_load(f)
        app.config_path = file_path  # Update config path to the new file
        # Remove all current cards from canvas
        for card_obj in app.cards:
            card_obj.delete()
        app.cards.clear()
        app.schedule.clear()
        # Load new schedule
        app.schedule.extend(new_schedule)
        # Ensure all loaded activities have unique IDs
        app.ensure_activity_ids()
        # Ensure all tasks have UUIDs (migrate from string to object format)
        app.ensure_task_uuids()
        # Create daily task entries for today if needed
        app._ensure_daily_task_entries()
        # Create cards
        app.cards = app.create_task_cards()
        # Load task done states from database after cards are created
        app._load_daily_task_entries()
        app.update_cards_after_size_change()
        app.last_action = datetime.now()
        
        # Save the loaded schedule path to settings (use absolute path)
        app.last_schedule_path = os.path.abspath(file_path)
        app.save_settings(immediate=True)
        
        log_info(f"Loaded schedule from {file_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")
        log_error(f"Failed to load file: {e}")

def save_schedule_as(app):
    """Open a dialog to save the schedule to a file."""
    # Suggest filename based on current week day (localized)
    today = app.now_provider().date()
    weekday_name = get_weekday_name(today.weekday())
    filename = f"{weekday_name}_settings.yaml"
    file_path = filedialog.asksaveasfilename(
        title="Save Schedule As",
        defaultextension=".yaml",
        initialfile=filename,
        filetypes=[("YAML files", "*.yaml"), ("All files", "*.*")]
    )
    if not file_path:
        return
    try:
        # Save tasks to database first
        if hasattr(app, 'task_tracking_service'):
            new_tasks_count = app.task_tracking_service.save_tasks_to_db(app.schedule)
            if new_tasks_count > 0:
                log_info(f"Saved {new_tasks_count} new tasks to database")
        
        with open(file_path, 'w') as f:
            yaml.safe_dump(app.schedule, f)
        messagebox.showinfo("Saved", f"Schedule saved to {file_path}")
        log_info(f"Schedule saved to {file_path}")
        app.config_path = file_path
        app.schedule_changed = False  # Reset schedule changed flag
        
        # Save the schedule path to settings (use absolute path)
        app.last_schedule_path = os.path.abspath(file_path)
        app.save_settings(immediate=True)
        
        # Create daily task entries for today if needed
        if hasattr(app, 'task_tracking_service'):
            app._ensure_daily_task_entries()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")
        log_error(f"Failed to save file: {e}")

def save_schedule(app, ask_for_confirmation: bool = True):
    """Save current schedule to the default YAML file."""
    # Ask for confirmation if file exists
    if ask_for_confirmation and os.path.exists(app.config_path):
        if not messagebox.askyesno("Confirm", "Schedule file already exists. Do you want to overwrite it?"):
            return
    try:
        # Save tasks to database first
        if hasattr(app, 'task_tracking_service'):
            new_tasks_count = app.task_tracking_service.save_tasks_to_db(app.schedule)
            if new_tasks_count > 0:
                log_info(f"Saved {new_tasks_count} new tasks to database")
        
        with open(app.config_path, 'w') as f:
            yaml.safe_dump(app.schedule, f)
        if ask_for_confirmation:
            messagebox.showinfo("Saved", f"Schedule saved to {app.config_path}")
        log_info(f"Schedule saved to {app.config_path}")
        app.schedule_changed = False  # Reset schedule changed flag
        
        # Save the schedule path to settings (use absolute path)
        app.last_schedule_path = os.path.abspath(app.config_path)
        app.save_settings(immediate=True)
        
        # Create daily task entries for today if needed
        if hasattr(app, 'task_tracking_service'):
            app._ensure_daily_task_entries()
            
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")
        log_error(f"Failed to save file: {e}")

def clear_schedule(app):
    """Clear all cards and schedule, with confirmation if there are unsaved changes."""
    if app.schedule_changed:
        if not messagebox.askyesno("Unsaved Changes", "You have unsaved changes. Do you want to close and lose them?"):
            return
    for card_obj in app.cards:
        card_obj.delete()
    app.cards.clear()
    app.schedule.clear()
    app.schedule_changed = False
    app.update_cards_after_size_change()
