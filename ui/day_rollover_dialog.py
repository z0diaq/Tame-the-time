import tkinter as tk
from tkinter import ttk
from utils.translator import t


class DayRolloverDialog:
    """
    Modal dialog shown during day rollover when a new day schedule file is found.
    
    Prompts user to choose between loading the new schedule or keeping the current one.
    This dialog is modal and blocks timeline updates until user makes a choice.
    """
    
    def __init__(self, parent, weekday: str, schedule_path: str):
        """
        Initialize the day rollover confirmation dialog.
        
        Args:
            parent: Parent window (main app)
            weekday: Name of the weekday for the new schedule
            schedule_path: Path to the new schedule file
        """
        self.result = None  # Will be True (load new) or False (keep current)
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(t("window.day_rollover_prompt"))
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()  # Make it modal
        
        # Center on parent window
        self.dialog.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create UI elements
        self._create_ui(weekday, schedule_path)
        
        # Disable window close button to force user to make a choice
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_keep_current)
        
        # Wait for dialog to close (modal behavior)
        self.dialog.wait_window()
    
    def _create_ui(self, weekday: str, schedule_path: str):
        """Create the dialog UI elements."""
        # Main frame with padding
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Message label
        message = t("message.day_rollover_schedule_found").format(
            weekday=weekday,
            schedule_path=schedule_path
        )
        message_label = tk.Label(
            main_frame,
            text=message,
            wraplength=450,
            justify="left",
            font=("Arial", 10)
        )
        message_label.pack(pady=(0, 20))
        
        # Separator
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill="x", pady=(0, 20))
        
        # Button frame
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        # Load new schedule button (primary action)
        load_button = tk.Button(
            button_frame,
            text=t("button.load_new_schedule"),
            command=self._on_load_new,
            width=25,
            bg="#4CAF50",  # Green background
            fg="white",
            font=("Arial", 10, "bold"),
            relief="raised",
            bd=2
        )
        load_button.pack(pady=5)
        
        # Load hint
        load_hint_label = tk.Label(
            button_frame,
            text=t("message.load_new_schedule_confirm"),
            font=("Arial", 8),
            fg="gray"
        )
        load_hint_label.pack(pady=(0, 15))
        
        # Keep current schedule button (secondary action)
        keep_button = tk.Button(
            button_frame,
            text=t("button.keep_current_schedule"),
            command=self._on_keep_current,
            width=25,
            font=("Arial", 10),
            relief="raised",
            bd=2
        )
        keep_button.pack(pady=5)
        
        # Keep hint
        keep_hint_label = tk.Label(
            button_frame,
            text=t("message.keep_current_schedule_confirm"),
            font=("Arial", 8),
            fg="gray"
        )
        keep_hint_label.pack(pady=(0, 5))
        
        # Set focus to load button (primary action)
        load_button.focus_set()
    
    def _on_load_new(self):
        """Handle 'Load New Schedule' button click."""
        self.result = True
        self.dialog.destroy()
    
    def _on_keep_current(self):
        """Handle 'Keep Current Schedule' button click."""
        self.result = False
        self.dialog.destroy()
    
    def get_result(self) -> bool:
        """
        Get the user's choice.
        
        Returns:
            True if user wants to load new schedule, False to keep current
        """
        return self.result if self.result is not None else False


def show_day_rollover_dialog(parent, weekday: str, schedule_path: str) -> bool:
    """
    Show day rollover confirmation dialog and return user choice.
    
    Args:
        parent: Parent window (main app)
        weekday: Name of the weekday for the new schedule
        schedule_path: Path to the new schedule file
        
    Returns:
        True if user wants to load new schedule, False to keep current
    """
    dialog = DayRolloverDialog(parent, weekday, schedule_path)
    return dialog.get_result()
