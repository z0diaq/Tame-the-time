"""
Compact view window for displaying minimal task information.
Shows current time, active task details, and next task preview.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Dict, Any
from utils.translator import t
from utils.locale_utils import get_weekday_name


class CompactView:
    """
    Compact window displaying minimal task information.
    
    Shows:
    - Current time with day of week
    - Current activity (name, description, tasks)
    - Task completion percentage
    - Next task name and time until it starts
    """
    
    def __init__(self, parent, now_provider):
        """
        Initialize the compact view window.
        
        Args:
            parent: Parent window (main app)
            now_provider: Function that returns current datetime
        """
        self.parent = parent
        self.now_provider = now_provider
        self.window: Optional[tk.Toplevel] = None
        self.is_visible = False
        
        # UI element references for updates
        self.time_label: Optional[tk.Label] = None
        self.activity_name_label: Optional[tk.Label] = None
        self.activity_desc_label: Optional[tk.Label] = None
        self.tasks_label: Optional[tk.Label] = None
        self.progress_label: Optional[tk.Label] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.next_task_label: Optional[tk.Label] = None
        
        # Track last window geometry for restoration
        self.last_geometry: Optional[str] = None
    
    def show(self):
        """Show the compact view window."""
        if self.window is None or not self.window.winfo_exists():
            self._create_window()
        else:
            self.window.deiconify()
        
        self.is_visible = True
        self.update()
    
    def hide(self):
        """Hide the compact view window."""
        if self.window and self.window.winfo_exists():
            # Save geometry before hiding
            self.last_geometry = self.window.geometry()
            self.window.withdraw()
        
        self.is_visible = False
    
    def toggle(self):
        """Toggle compact view visibility."""
        if self.is_visible:
            self.hide()
        else:
            self.show()
    
    def destroy(self):
        """Destroy the compact view window."""
        if self.window and self.window.winfo_exists():
            self.last_geometry = self.window.geometry()
            self.window.destroy()
        
        self.window = None
        self.is_visible = False
    
    def _create_window(self):
        """Create the compact view window UI."""
        self.window = tk.Toplevel(self.parent)
        self.window.title(t("window.compact_view"))
        
        # Set window properties
        self.window.attributes("-topmost", True)  # Always on top by default
        self.window.resizable(True, True)
        
        # Restore last geometry or use default
        if self.last_geometry:
            self.window.geometry(self.last_geometry)
        else:
            self.window.geometry("320x280")
        
        # Main frame with padding
        main_frame = tk.Frame(self.window, padx=10, pady=10, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True)
        
        # === Current Time Section ===
        time_frame = tk.Frame(main_frame, bg="#2c3e50", relief="raised", bd=2)
        time_frame.pack(fill="x", pady=(0, 8))
        
        self.time_label = tk.Label(
            time_frame,
            text="--:--:--",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50",
            pady=8
        )
        self.time_label.pack()
        
        # === Current Activity Section ===
        activity_frame = tk.Frame(main_frame, bg="white", relief="solid", bd=1)
        activity_frame.pack(fill="both", expand=True, pady=(0, 8))
        
        # Activity header
        activity_header = tk.Label(
            activity_frame,
            text=t("compact.current_activity"),
            font=("Arial", 9, "bold"),
            bg="#3498db",
            fg="white",
            anchor="w",
            padx=5,
            pady=3
        )
        activity_header.pack(fill="x")
        
        # Activity content frame
        activity_content = tk.Frame(activity_frame, bg="white", padx=8, pady=6)
        activity_content.pack(fill="both", expand=True)
        
        # Activity name
        self.activity_name_label = tk.Label(
            activity_content,
            text="No active task",
            font=("Arial", 11, "bold"),
            bg="white",
            anchor="w",
            justify="left",
            wraplength=280
        )
        self.activity_name_label.pack(fill="x", pady=(0, 4))
        
        # Activity description
        self.activity_desc_label = tk.Label(
            activity_content,
            text="",
            font=("Arial", 9),
            bg="white",
            anchor="w",
            justify="left",
            wraplength=280,
            fg="#555555"
        )
        self.activity_desc_label.pack(fill="x", pady=(0, 6))
        
        # Tasks info
        self.tasks_label = tk.Label(
            activity_content,
            text="",
            font=("Arial", 9),
            bg="white",
            anchor="w",
            justify="left"
        )
        self.tasks_label.pack(fill="x", pady=(0, 4))
        
        # Progress section
        progress_frame = tk.Frame(activity_content, bg="white")
        progress_frame.pack(fill="x", pady=(4, 0))
        
        self.progress_label = tk.Label(
            progress_frame,
            text=t("compact.completion") + ": 0%",
            font=("Arial", 9),
            bg="white",
            anchor="w"
        )
        self.progress_label.pack(fill="x")
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            maximum=100
        )
        self.progress_bar.pack(fill="x", pady=(2, 0))
        
        # === Next Task Section ===
        next_frame = tk.Frame(main_frame, bg="#ecf0f1", relief="solid", bd=1)
        next_frame.pack(fill="x")
        
        next_header = tk.Label(
            next_frame,
            text=t("compact.next_task"),
            font=("Arial", 9, "bold"),
            bg="#95a5a6",
            fg="white",
            anchor="w",
            padx=5,
            pady=3
        )
        next_header.pack(fill="x")
        
        next_content = tk.Frame(next_frame, bg="#ecf0f1", padx=8, pady=6)
        next_content.pack(fill="x")
        
        self.next_task_label = tk.Label(
            next_content,
            text=t("compact.no_next_task"),
            font=("Arial", 9),
            bg="#ecf0f1",
            anchor="w",
            justify="left",
            wraplength=280
        )
        self.next_task_label.pack(fill="x")
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.hide)
    
    def update(self):
        """Update compact view with current information."""
        if not self.is_visible or not self.window or not self.window.winfo_exists():
            return
        
        # Update current time
        self._update_time()
        
        # Update current activity
        self._update_current_activity()
        
        # Update next task
        self._update_next_task()
    
    def _update_time(self):
        """Update current time display with day of week."""
        now = self.now_provider()
        weekday_name = get_weekday_name(now.weekday())
        time_str = now.strftime("%H:%M:%S")
        
        self.time_label.config(text=f"{weekday_name} {time_str}")
    
    def _update_current_activity(self):
        """Update current activity information."""
        # Get current activity from schedule service
        from services.schedule_service import ScheduleService
        
        schedule_service = ScheduleService(self.now_provider)
        schedule_service._schedule = getattr(self.parent, '_schedule_model', None)
        
        if not schedule_service._schedule:
            # Fallback: create schedule from parent's schedule data
            from models.schedule import Schedule
            schedule_service._schedule = Schedule(self.parent.schedule)
        
        current_activity = schedule_service.get_current_activity()
        
        if current_activity:
            # Update activity name
            self.activity_name_label.config(text=current_activity.name)
            
            # Update description
            desc_text = "\n".join(current_activity.description) if current_activity.description else ""
            self.activity_desc_label.config(text=desc_text)
            
            # Update tasks info
            tasks = current_activity.tasks
            if tasks:
                # Get task completion status from parent app's cards
                task_done_count = 0
                total_tasks = len(tasks)
                
                # Find the card for this activity to get task completion status
                activity_id = current_activity.id
                for card in self.parent.cards:
                    if card.activity.get("id") == activity_id:
                        tasks_done = getattr(card, '_tasks_done', [False] * total_tasks)
                        task_done_count = sum(tasks_done)
                        break
                
                # Update tasks label
                self.tasks_label.config(
                    text=t("compact.tasks_info").format(
                        done=task_done_count,
                        total=total_tasks
                    )
                )
                
                # Update progress
                percentage = int((task_done_count / total_tasks) * 100) if total_tasks > 0 else 0
                self.progress_label.config(
                    text=t("compact.completion") + f": {percentage}%"
                )
                self.progress_bar["value"] = percentage
            else:
                self.tasks_label.config(text=t("compact.no_tasks"))
                self.progress_label.config(text=t("compact.completion") + ": --")
                self.progress_bar["value"] = 0
        else:
            # No current activity
            self.activity_name_label.config(text=t("compact.no_activity"))
            self.activity_desc_label.config(text="")
            self.tasks_label.config(text="")
            self.progress_label.config(text=t("compact.completion") + ": --")
            self.progress_bar["value"] = 0
    
    def _update_next_task(self):
        """Update next task information."""
        from services.schedule_service import ScheduleService
        
        schedule_service = ScheduleService(self.now_provider)
        schedule_service._schedule = getattr(self.parent, '_schedule_model', None)
        
        if not schedule_service._schedule:
            from models.schedule import Schedule
            schedule_service._schedule = Schedule(self.parent.schedule)
        
        next_result = schedule_service.get_next_activity()
        
        if next_result:
            next_activity, next_start = next_result
            
            # Calculate time until start
            now = self.now_provider()
            time_diff = next_start - now
            
            # Format time difference
            total_seconds = int(time_diff.total_seconds())
            if total_seconds < 0:
                time_str = t("compact.starting_soon")
            elif total_seconds < 60:
                time_str = t("compact.seconds_until").format(seconds=total_seconds)
            elif total_seconds < 3600:
                minutes = total_seconds // 60
                time_str = t("compact.minutes_until").format(minutes=minutes)
            else:
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                time_str = t("compact.hours_minutes_until").format(hours=hours, minutes=minutes)
            
            # Update next task label
            next_text = f"▶ {next_activity.name}\n{time_str}"
            self.next_task_label.config(text=next_text)
        else:
            self.next_task_label.config(text=t("compact.no_next_task"))
    
    def refresh_ui_after_language_change(self):
        """Refresh UI elements after language change."""
        if not self.window or not self.window.winfo_exists():
            return
        
        # Update window title
        self.window.title(t("window.compact_view"))
        
        # Recreate the window to update all labels
        # Save geometry
        geometry = self.window.geometry()
        
        # Destroy and recreate
        self.window.destroy()
        self._create_window()
        self.window.geometry(geometry)
        
        # Update content
        self.update()


def create_compact_view(parent, now_provider):
    """
    Factory function to create a compact view instance.
    
    Args:
        parent: Parent window (main app)
        now_provider: Function that returns current datetime
        
    Returns:
        CompactView instance
    """
    return CompactView(parent, now_provider)
