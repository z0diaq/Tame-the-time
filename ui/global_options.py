import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk
import utils.notification
import re

def open_global_options(app):
    """Open a dialog to edit global options."""
    options_win = tk.Toplevel(app)
    options_win.title("Global Options")
    options_win.geometry("400x350")
    options_win.transient(app)
    options_win.grab_set()

    # Start hour setting
    tk.Label(options_win, text="Start hour:").pack(anchor="w", padx=10, pady=(15, 0))
    start_hour_var = tk.IntVar(value=app.start_hour)
    start_hour_entry = tk.Entry(options_win, textvariable=start_hour_var)
    start_hour_entry.pack(fill="x", padx=10)

    # End hour setting
    tk.Label(options_win, text="End hour:").pack(anchor="w", padx=10, pady=(10, 0))
    end_hour_var = tk.IntVar(value=app.end_hour)
    end_hour_entry = tk.Entry(options_win, textvariable=end_hour_var)
    end_hour_entry.pack(fill="x", padx=10)

    # Notification settings
    tk.Label(options_win, text="Notification:").pack(anchor="w", padx=10, pady=(15, 0))
    notification_var = tk.StringVar()
    notification_combo = ttk.Combobox(options_win, textvariable=notification_var, 
                                     values=["Disabled", "Gotify"], state="readonly")
    notification_combo.pack(fill="x", padx=10)
    
    # Set current notification type based on whether Gotify is configured
    current_gotify_url = utils.notification.gotify_url or ""
    current_gotify_token = utils.notification.gotify_token or ""
    if current_gotify_url and current_gotify_token:
        notification_var.set("Gotify")
    else:
        notification_var.set("Disabled")

    # Gotify URL field
    gotify_url_label = tk.Label(options_win, text="Gotify URL:")
    gotify_url_var = tk.StringVar(value=current_gotify_url)
    gotify_url_entry = tk.Entry(options_win, textvariable=gotify_url_var)

    # Gotify Token field
    gotify_token_label = tk.Label(options_win, text="Gotify Token:")
    gotify_token_var = tk.StringVar(value=current_gotify_token)
    gotify_token_entry = tk.Entry(options_win, textvariable=gotify_token_var, show="*")

    def on_notification_change(*args):
        """Show/hide Gotify fields based on notification selection."""
        if notification_var.get() == "Gotify":
            gotify_url_label.pack(anchor="w", padx=10, pady=(10, 0))
            gotify_url_entry.pack(fill="x", padx=10)
            gotify_token_label.pack(anchor="w", padx=10, pady=(10, 0))
            gotify_token_entry.pack(fill="x", padx=10)
        else:
            gotify_url_label.pack_forget()
            gotify_url_entry.pack_forget()
            gotify_token_label.pack_forget()
            gotify_token_entry.pack_forget()

    # Bind notification change event
    notification_var.trace("w", on_notification_change)
    
    # Initialize visibility based on current selection
    on_notification_change()

    def validate_gotify_url(url):
        """Validate Gotify URL format."""
        if not url:
            return False
        
        # Check if URL starts with http or https
        if not url.startswith(('http://', 'https://')):
            return False
        
        # Check if URL ends with /message
        if not url.endswith('/message'):
            return False
        
        # Basic URI format validation using regex
        # Pattern: http(s)://host(:port)/message
        pattern = r'^https?://[a-zA-Z0-9.-]+(?::\d+)?/message$'
        return bool(re.match(pattern, url))

    btn_frame = tk.Frame(options_win)
    btn_frame.pack(fill="x", pady=15)
    
    def on_ok():
        try:
            new_start = int(start_hour_var.get())
            new_end = int(end_hour_var.get())
            if 0 <= new_start < 24 and 0 < new_end <= 24 and new_start < new_end:
                # Update hour settings
                app.start_hour = new_start
                app.end_hour = new_end
                app.update_cards_after_size_change()
                
                # Update notification settings
                if notification_var.get() == "Gotify":
                    gotify_url = gotify_url_var.get().strip()
                    gotify_token = gotify_token_var.get().strip()
                    
                    # Validate Gotify URL format
                    if gotify_url and not validate_gotify_url(gotify_url):
                        response = messagebox.askyesno(
                            "Invalid Gotify URL",
                            "Gotify URL does not look correct - expected format is http(s)://<ip/name>:<port>/message. Do you want to correct it?",
                            icon="warning"
                        )
                        if response:  # User clicked "Yes"
                            return  # Stay in dialog to allow correction
                        # User clicked "No", proceed with the invalid URL
                    
                    utils.notification.gotify_url = gotify_url
                    utils.notification.gotify_token = gotify_token
                else:
                    utils.notification.gotify_url = ""
                    utils.notification.gotify_token = ""
                
                # Save settings to file
                app.save_settings(immediate=True)
                
                options_win.destroy()
            else:
                messagebox.showerror("Invalid Input", "Start hour must be >=0 and < End hour, End hour must be <=24.")
        except Exception as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def on_cancel():
        options_win.destroy()
    
    tk.Button(btn_frame, text="Ok", command=on_ok).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="right", padx=20)
