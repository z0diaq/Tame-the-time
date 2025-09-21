import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk
import utils.notification
import re
from utils.translator import t, get_available_languages, set_language

def open_global_options(app):
    """Open a dialog to edit global options."""
    options_win = tk.Toplevel(app)
    options_win.title(t("window.global_options"))
    options_win.geometry("400x510")
    options_win.transient(app)
    options_win.grab_set()

    # Store references to UI elements for dynamic updates
    ui_elements = {}

    # Day start setting
    ui_elements['day_start_label'] = tk.Label(options_win, text=t("label.day_start"))
    ui_elements['day_start_label'].pack(anchor="w", padx=10, pady=(15, 0))
    day_start_var = tk.IntVar(value=getattr(app, 'day_start', 0))
    day_start_entry = tk.Entry(options_win, textvariable=day_start_var)
    day_start_entry.pack(fill="x", padx=10)
    
    # Help text for day start
    ui_elements['day_start_help'] = tk.Label(options_win, text=t("label.day_start_help"), 
                                           font=("Arial", 8), fg="gray")
    ui_elements['day_start_help'].pack(anchor="w", padx=10, pady=(2, 0))

    # Notification settings
    ui_elements['notification_label'] = tk.Label(options_win, text=t("label.notification"))
    ui_elements['notification_label'].pack(anchor="w", padx=10, pady=(15, 0))
    notification_var = tk.StringVar()
    notification_combo = ttk.Combobox(options_win, textvariable=notification_var, 
                                     values=[t("combo.disabled"), t("combo.gotify")], state="readonly")
    notification_combo.pack(fill="x", padx=10)
    ui_elements['notification_combo'] = notification_combo
    
    # Set current notification type based on whether Gotify is configured
    current_gotify_url = utils.notification.gotify_url or ""
    current_gotify_token = utils.notification.gotify_token or ""
    if current_gotify_url and current_gotify_token:
        notification_var.set(t("combo.gotify"))
    else:
        notification_var.set(t("combo.disabled"))

    # Gotify URL field
    ui_elements['gotify_url_label'] = tk.Label(options_win, text=t("label.gotify_url"))
    gotify_url_var = tk.StringVar(value=current_gotify_url)
    gotify_url_entry = tk.Entry(options_win, textvariable=gotify_url_var)

    # Gotify Token field
    ui_elements['gotify_token_label'] = tk.Label(options_win, text=t("label.gotify_token"))
    gotify_token_var = tk.StringVar(value=current_gotify_token)
    gotify_token_entry = tk.Entry(options_win, textvariable=gotify_token_var, show="*")

    def on_notification_change(*args):
        """Show/hide Gotify fields based on notification selection."""
        if notification_var.get() == t("combo.gotify"):
            ui_elements['gotify_url_label'].pack(anchor="w", padx=10, pady=(10, 0))
            gotify_url_entry.pack(fill="x", padx=10)
            ui_elements['gotify_token_label'].pack(anchor="w", padx=10, pady=(10, 0))
            gotify_token_entry.pack(fill="x", padx=10)
        else:
            ui_elements['gotify_url_label'].pack_forget()
            gotify_url_entry.pack_forget()
            ui_elements['gotify_token_label'].pack_forget()
            gotify_token_entry.pack_forget()

    # Bind notification change event
    notification_var.trace("w", on_notification_change)
    
    # Initialize visibility based on current selection
    on_notification_change()

    # Language selection
    ui_elements['language_label'] = tk.Label(options_win, text=t("label.language"))
    ui_elements['language_label'].pack(anchor="w", padx=10, pady=(15, 0))
    language_var = tk.StringVar()
    available_languages = get_available_languages()
    language_values = list(available_languages.values())
    language_combo = ttk.Combobox(options_win, textvariable=language_var, 
                                 values=language_values, state="readonly")
    language_combo.pack(fill="x", padx=10)
    ui_elements['language_combo'] = language_combo
    
    # Set current language
    current_lang = getattr(app, 'current_language', 'en')
    if current_lang in available_languages:
        language_var.set(available_languages[current_lang])
    else:
        language_var.set(available_languages.get('en', 'English'))
    
    def on_language_change(*args):
        """Handle language change and update UI immediately."""
        selected_language_display = language_var.get()
        selected_language_code = None
        for code, display in available_languages.items():
            if display == selected_language_display:
                selected_language_code = code
                break
        
        if selected_language_code and selected_language_code != getattr(app, 'current_language', 'en'):
            if set_language(selected_language_code):
                app.current_language = selected_language_code
                # Update dialog UI elements
                refresh_dialog_ui()
                # Update main window
                app.refresh_ui_after_language_change()
    
    def refresh_dialog_ui():
        """Refresh all translatable UI elements in the dialog."""
        # Update window title
        options_win.title(t("window.global_options"))
        
        # Update labels
        ui_elements['day_start_label'].config(text=t("label.day_start"))
        ui_elements['day_start_help'].config(text=t("label.day_start_help"))
        ui_elements['notification_label'].config(text=t("label.notification"))
        ui_elements['gotify_url_label'].config(text=t("label.gotify_url"))
        ui_elements['gotify_token_label'].config(text=t("label.gotify_token"))
        ui_elements['language_label'].config(text=t("label.language"))
        ui_elements['advance_settings_label'].config(text=t("label.advance_notification_settings"))
        ui_elements['advance_checkbox'].config(text=t("label.enable_advance_notifications"))
        ui_elements['seconds_label'].config(text=t("label.seconds_before_activity"))
        
        # Update notification combo box values
        current_notification = notification_var.get()
        new_values = [t("combo.disabled"), t("combo.gotify")]
        ui_elements['notification_combo']['values'] = new_values
        
        # Preserve selection by mapping old to new values
        if current_notification in ["Disabled", "Désactivé", "Deshabilitado"]:
            notification_var.set(t("combo.disabled"))
        elif current_notification in ["Gotify"]:
            notification_var.set(t("combo.gotify"))
        
        # Update language combo box values and selection
        current_lang_code = getattr(app, 'current_language', 'en')
        new_available_languages = get_available_languages()
        new_language_values = list(new_available_languages.values())
        ui_elements['language_combo']['values'] = new_language_values
        
        # Update the selected language display name to match new language
        if current_lang_code in new_available_languages:
            language_var.set(new_available_languages[current_lang_code])
        
        # Update buttons
        ui_elements['ok_button'].config(text=t("button.ok"))
        ui_elements['cancel_button'].config(text=t("button.cancel"))
    
    # Bind language change event
    language_var.trace("w", on_language_change)
    
    # Advance notification settings
    ui_elements['advance_settings_label'] = tk.Label(options_win, text=t("label.advance_notification_settings"))
    ui_elements['advance_settings_label'].pack(anchor="w", padx=10, pady=(15, 0))
    
    # Advance notification enabled checkbox
    advance_notification_enabled_var = tk.BooleanVar()
    advance_notification_enabled_var.set(getattr(app, 'advance_notification_enabled', True))
    ui_elements['advance_checkbox'] = tk.Checkbutton(
        options_win, 
        text=t("label.enable_advance_notifications"), 
        variable=advance_notification_enabled_var
    )
    ui_elements['advance_checkbox'].pack(anchor="w", padx=10, pady=(5, 0))
    
    # Advance notification seconds setting
    advance_seconds_frame = tk.Frame(options_win)
    advance_seconds_frame.pack(fill="x", padx=10, pady=(5, 0))
    
    ui_elements['seconds_label'] = tk.Label(advance_seconds_frame, text=t("label.seconds_before_activity"))
    ui_elements['seconds_label'].pack(side="left")
    advance_notification_seconds_var = tk.IntVar()
    advance_notification_seconds_var.set(getattr(app, 'advance_notification_seconds', 30))
    advance_notification_seconds_entry = tk.Entry(
        advance_seconds_frame, 
        textvariable=advance_notification_seconds_var,
        width=10
    )
    advance_notification_seconds_entry.pack(side="right")

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
            new_day_start = int(day_start_var.get())
            if 0 <= new_day_start < 24:
                # Update day start setting
                app.day_start = new_day_start
                # Update derived values for backward compatibility
                app.start_hour = new_day_start
                app.end_hour = (new_day_start + 24) % 24 if new_day_start != 0 else 24
                app.update_cards_after_size_change()
                
                # Update notification settings
                if notification_var.get() == t("combo.gotify"):
                    gotify_url = gotify_url_var.get().strip()
                    gotify_token = gotify_token_var.get().strip()
                    
                    # Validate Gotify URL format
                    if gotify_url and not validate_gotify_url(gotify_url):
                        response = messagebox.askyesno(
                            t("dialog.invalid_gotify_url"),
                            t("message.gotify_url_format"),
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
                
                # Update advance notification settings
                new_advance_enabled = advance_notification_enabled_var.get()
                new_advance_seconds = advance_notification_seconds_var.get()
                
                # Validate advance notification seconds
                if new_advance_seconds < 0 or new_advance_seconds > 3600:  # Max 1 hour
                    messagebox.showerror(t("dialog.invalid_input"), t("message.invalid_advance_seconds"))
                    return
                
                # Language is already updated by the on_language_change callback
                
                # Update app settings
                app.advance_notification_enabled = new_advance_enabled
                app.advance_notification_seconds = new_advance_seconds
                
                # Update notification service with new settings
                app.notification_service.set_advance_notification_settings(
                    new_advance_enabled, 
                    new_advance_seconds
                )
                
                # Save settings to file
                app.save_settings(immediate=True)
                
                options_win.destroy()
            else:
                messagebox.showerror(t("dialog.invalid_input"), t("message.invalid_day_start"))
        except Exception as e:
            messagebox.showerror(t("dialog.invalid_input"), str(e))
    
    def on_cancel():
        options_win.destroy()
    
    ui_elements['ok_button'] = tk.Button(btn_frame, text=t("button.ok"), command=on_ok)
    ui_elements['ok_button'].pack(side="left", padx=20)
    ui_elements['cancel_button'] = tk.Button(btn_frame, text=t("button.cancel"), command=on_cancel)
    ui_elements['cancel_button'].pack(side="right", padx=20)
