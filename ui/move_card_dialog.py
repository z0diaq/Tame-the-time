import tkinter as tk
import tkinter.messagebox as messagebox
from datetime import datetime, time, timedelta
from utils.translator import t
from utils.time_utils import TimeUtils
from utils.logging import log_debug, log_error


class MoveCardDialog:
    """Dialog for moving a card to a new time position."""
    
    def __init__(self, parent, card_obj, app):
        """
        Initialize the move card dialog.
        
        Args:
            parent: Parent window
            card_obj: TaskCard object to move
            app: Main application instance
        """
        self.card_obj = card_obj
        self.app = app
        self.result = None  # Will store the new start time if user confirms
        self._updating_fields = False  # Flag to prevent infinite update loops
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(t("window.move_card"))
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make dialog modal
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Center dialog on parent
        self.dialog.geometry("500x250")
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        dialog_width = 500
        dialog_height = 250
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        self._create_widgets()
        
        # Bind keyboard shortcuts
        self.dialog.bind('<Return>', lambda e: self._on_ok())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        
        # Set focus to the dialog and the first entry field
        self.dialog.focus_set()
        self.new_time_entry.focus_set()
        self.new_time_entry.select_range(0, tk.END)  # Select all text for easy replacement
        self.new_time_entry.icursor(tk.END)  # Move cursor to end
        
    def _create_widgets(self):
        """Create dialog widgets."""
        # Main frame
        main_frame = tk.Frame(self.dialog, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current time label
        current_time = f"{self.card_obj.start_hour:02d}:{self.card_obj.start_minute:02d}"
        tk.Label(
            main_frame, 
            text=t("label.current_time", time=current_time),
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Option 1: Set new time
        tk.Label(
            main_frame,
            text=t("label.move_option_new_time")
        ).pack(anchor=tk.W, pady=(5, 5))
        
        time_frame = tk.Frame(main_frame)
        time_frame.pack(anchor=tk.W, pady=(0, 15))
        
        self.new_time_entry = tk.Entry(time_frame, width=10)
        self.new_time_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.new_time_entry.insert(0, current_time)
        
        tk.Label(time_frame, text=t("label.time_format_hint")).pack(side=tk.LEFT)
        
        # Option 2: Shift by amount
        tk.Label(
            main_frame,
            text=t("label.move_option_shift")
        ).pack(anchor=tk.W, pady=(5, 5))
        
        shift_frame = tk.Frame(main_frame)
        shift_frame.pack(anchor=tk.W, pady=(0, 15))
        
        self.shift_entry = tk.Entry(shift_frame, width=10)
        self.shift_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.shift_entry.insert(0, "00:00")
        
        tk.Label(shift_frame, text=t("label.shift_format_hint")).pack(side=tk.LEFT)
        
        # Bind entries to sync with each other
        self.new_time_entry.bind('<KeyRelease>', self._on_new_time_changed)
        self.new_time_entry.bind('<FocusOut>', self._on_new_time_changed)
        self.shift_entry.bind('<KeyRelease>', self._on_shift_changed)
        self.shift_entry.bind('<FocusOut>', self._on_shift_changed)
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        
        tk.Button(
            button_frame,
            text=t("button.ok"),
            command=self._on_ok,
            width=10
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        tk.Button(
            button_frame,
            text=t("button.cancel"),
            command=self._on_cancel,
            width=10
        ).pack(side=tk.RIGHT)
        
    def _parse_shift_time(self, shift_str):
        """
        Parse shift time string in format HH:MM or -HH:MM.
        
        Args:
            shift_str: String like "01:30" or "-01:30"
            
        Returns:
            Tuple of (hours, minutes, is_negative)
        """
        shift_str = shift_str.strip()
        is_negative = shift_str.startswith('-')
        
        if is_negative:
            shift_str = shift_str[1:]
        
        try:
            time_obj = TimeUtils.parse_time_with_validation(shift_str)
            return time_obj.hour, time_obj.minute, is_negative
        except ValueError as e:
            raise ValueError(f"{t('message.invalid_shift_format')}: {str(e)}")
    
    def _on_new_time_changed(self, event=None):
        """
        Handle changes to new_time_entry and update shift_entry accordingly.
        
        Args:
            event: Tkinter event (unused)
        """
        if self._updating_fields:
            return
        
        new_time_str = self.new_time_entry.get().strip()
        if not new_time_str:
            return
        
        try:
            # Parse the new time
            time_obj = TimeUtils.parse_time_with_validation(new_time_str)
            new_hour = time_obj.hour
            new_minute = time_obj.minute
            
            # Calculate shift from current time
            current_minutes = self.card_obj.start_hour * 60 + self.card_obj.start_minute
            new_minutes = new_hour * 60 + new_minute
            shift_minutes = new_minutes - current_minutes
            
            # Determine sign and format
            is_negative = shift_minutes < 0
            abs_shift = abs(shift_minutes)
            shift_hours = abs_shift // 60
            shift_mins = abs_shift % 60
            
            # Update shift_entry
            self._updating_fields = True
            try:
                sign = "-" if is_negative else ""
                self.shift_entry.delete(0, tk.END)
                self.shift_entry.insert(0, f"{sign}{shift_hours:02d}:{shift_mins:02d}")
            finally:
                self._updating_fields = False
                
        except ValueError:
            # Invalid time format, don't update shift
            pass
    
    def _on_shift_changed(self, event=None):
        """
        Handle changes to shift_entry and update new_time_entry accordingly.
        
        Args:
            event: Tkinter event (unused)
        """
        if self._updating_fields:
            return
        
        shift_str = self.shift_entry.get().strip()
        if not shift_str:
            return
        
        try:
            # Parse the shift
            shift_hours, shift_minutes, is_negative = self._parse_shift_time(shift_str)
            
            # Calculate new time
            current_minutes = self.card_obj.start_hour * 60 + self.card_obj.start_minute
            shift_total_minutes = shift_hours * 60 + shift_minutes
            
            if is_negative:
                new_minutes = current_minutes - shift_total_minutes
            else:
                new_minutes = current_minutes + shift_total_minutes
            
            # Handle wrap around (keep within 24 hour period)
            new_minutes = new_minutes % (24 * 60)
            if new_minutes < 0:
                new_minutes += 24 * 60
            
            new_hour = new_minutes // 60
            new_minute = new_minutes % 60
            
            # Update new_time_entry
            self._updating_fields = True
            try:
                self.new_time_entry.delete(0, tk.END)
                self.new_time_entry.insert(0, f"{new_hour:02d}:{new_minute:02d}")
            finally:
                self._updating_fields = False
                
        except ValueError:
            # Invalid shift format, don't update new time
            pass
    
    def _calculate_new_time(self):
        """
        Calculate new time based on user input.
        
        Returns:
            Tuple of (new_hour, new_minute) or None if invalid
        """
        # Check if shift is provided (non-zero)
        shift_str = self.shift_entry.get().strip()
        new_time_str = self.new_time_entry.get().strip()
        
        # Determine which input method to use
        use_shift = shift_str and shift_str != "00:00" and shift_str != "0:00" and shift_str != "0:0"
        
        if use_shift:
            # Use shift method
            try:
                shift_hours, shift_minutes, is_negative = self._parse_shift_time(shift_str)
                
                # Calculate new time
                current_minutes = self.card_obj.start_hour * 60 + self.card_obj.start_minute
                shift_total_minutes = shift_hours * 60 + shift_minutes
                
                if is_negative:
                    new_minutes = current_minutes - shift_total_minutes
                else:
                    new_minutes = current_minutes + shift_total_minutes
                
                # Handle wrap around (keep within 24 hour period)
                new_minutes = new_minutes % (24 * 60)
                if new_minutes < 0:
                    new_minutes += 24 * 60
                
                new_hour = new_minutes // 60
                new_minute = new_minutes % 60
                
                return new_hour, new_minute
                
            except ValueError as e:
                messagebox.showerror(t("dialog.error"), str(e))
                return None
        else:
            # Use absolute time method
            try:
                time_obj = TimeUtils.parse_time_with_validation(new_time_str)
                return time_obj.hour, time_obj.minute
            except ValueError as e:
                messagebox.showerror(
                    t("dialog.error"),
                    f"{t('message.invalid_time_format')}: {str(e)}"
                )
                return None
    
    def _check_day_boundary(self, new_hour, new_minute):
        """
        Check if new time crosses the day_start boundary.
        
        Args:
            new_hour: New hour (0-23)
            new_minute: New minute (0-59)
            
        Returns:
            True if valid, False if crosses boundary
        """
        day_start = getattr(self.app, 'day_start', 0)
        
        # Calculate card duration
        duration_hours = self.card_obj.end_hour - self.card_obj.start_hour
        duration_minutes = self.card_obj.end_minute - self.card_obj.start_minute
        
        if duration_minutes < 0:
            duration_hours -= 1
            duration_minutes += 60
        
        if duration_hours < 0:
            duration_hours += 24
        
        # Calculate new end time
        end_minutes = new_minute + duration_minutes
        end_hour = new_hour + duration_hours
        
        if end_minutes >= 60:
            end_hour += 1
            end_minutes -= 60
        
        end_hour = end_hour % 24
        
        # Check if card would cross the day_start boundary
        # This is complex because we need to consider the 24-hour wrap
        
        # Convert times to minutes since day_start
        def minutes_from_day_start(hour, minute):
            if hour < day_start:
                hour += 24
            return (hour - day_start) * 60 + minute
        
        start_minutes = minutes_from_day_start(new_hour, new_minute)
        end_minutes_total = minutes_from_day_start(end_hour, end_minutes)
        
        # Card should be entirely within one day period (0 to 24*60 minutes from day_start)
        if start_minutes < 0 or start_minutes >= 24 * 60:
            return False
        
        if end_minutes_total < 0 or end_minutes_total > 24 * 60:
            return False
        
        # Also check that end time is after start time
        if end_minutes_total <= start_minutes:
            return False
        
        return True
    
    def _check_conflicts(self, new_hour, new_minute):
        """
        Check if new position conflicts with other cards.
        
        Args:
            new_hour: New hour (0-23)
            new_minute: New minute (0-59)
            
        Returns:
            List of conflicting cards, empty if no conflicts
        """
        # Calculate new end time
        duration_hours = self.card_obj.end_hour - self.card_obj.start_hour
        duration_minutes = self.card_obj.end_minute - self.card_obj.start_minute
        
        if duration_minutes < 0:
            duration_hours -= 1
            duration_minutes += 60
        
        if duration_hours < 0:
            duration_hours += 24
        
        end_minutes = new_minute + duration_minutes
        end_hour = new_hour + duration_hours
        
        if end_minutes >= 60:
            end_hour += 1
            end_minutes -= 60
        
        end_hour = end_hour % 24
        
        # Convert to minutes for easier comparison
        new_start_mins = new_hour * 60 + new_minute
        new_end_mins = end_hour * 60 + end_minutes
        
        # Handle wrap around midnight
        if new_end_mins <= new_start_mins:
            new_end_mins += 24 * 60
        
        conflicts = []
        
        for card in self.app.cards:
            # Skip the card being moved
            if card == self.card_obj:
                continue
            
            # Check for time overlap
            card_start_mins = card.start_hour * 60 + card.start_minute
            card_end_mins = card.end_hour * 60 + card.end_minute
            
            # Handle wrap around midnight for existing card
            if card_end_mins <= card_start_mins:
                card_end_mins += 24 * 60
            
            # Adjust for day_start if needed
            day_start = getattr(self.app, 'day_start', 0)
            day_start_mins = day_start * 60
            
            # Normalize both ranges to be relative to day_start
            def normalize_to_day_start(start, end, day_start_mins):
                if start < day_start_mins:
                    start += 24 * 60
                if end < day_start_mins:
                    end += 24 * 60
                if end <= start:
                    end += 24 * 60
                return start, end
            
            new_start_norm, new_end_norm = normalize_to_day_start(new_start_mins, new_end_mins, day_start_mins)
            card_start_norm, card_end_norm = normalize_to_day_start(card_start_mins, card_end_mins, day_start_mins)
            
            # Check for overlap: ranges overlap if start1 < end2 AND start2 < end1
            if new_start_norm < card_end_norm and card_start_norm < new_end_norm:
                conflicts.append(card)
        
        return conflicts
    
    def _on_ok(self):
        """Handle OK button click."""
        # Calculate new time
        new_time = self._calculate_new_time()
        if new_time is None:
            return
        
        new_hour, new_minute = new_time
        
        # Validate day boundary
        if not self._check_day_boundary(new_hour, new_minute):
            day_start = getattr(self.app, 'day_start', 0)
            messagebox.showerror(
                t("dialog.error"),
                t("message.move_crosses_day_boundary", day_start=day_start)
            )
            return
        
        # Check for conflicts
        conflicts = self._check_conflicts(new_hour, new_minute)
        if conflicts:
            conflict_names = [card.activity.get('name', 'Unknown') for card in conflicts]
            conflict_list = "\n".join([f"- {name}" for name in conflict_names])
            
            if not messagebox.askyesno(
                t("dialog.warning"),
                t("message.move_conflict_warning", conflict_list=conflict_list)
            ):
                return
        
        # Store result and close
        self.result = (new_hour, new_minute)
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show dialog and wait for user input."""
        self.dialog.wait_window()
        return self.result


def open_move_card_dialog(parent, card_obj, app):
    """
    Open dialog to move a card to new position.
    
    Args:
        parent: Parent window
        card_obj: TaskCard object to move
        app: Main application instance
        
    Returns:
        Tuple of (new_hour, new_minute) or None if cancelled
    """
    dialog = MoveCardDialog(parent, card_obj, app)
    return dialog.show()
