"""
Statistics dialog for displaying task completion charts and analytics.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import List, Dict, Tuple
from services.task_tracking_service import TaskTrackingService
from utils.logging import log_debug, log_error


class TaskStatisticsDialog:
    """Dialog for displaying task statistics with charts."""
    
    def __init__(self, parent, task_tracking_service: TaskTrackingService):
        """Initialize the statistics dialog."""
        self.parent = parent
        self.task_service = task_tracking_service
        self.dialog = None
        self.task_listbox = None
        self.grouping_var = None
        self.ignore_weekends_var = None
        self.chart_frame = None
        self.figure = None
        self.canvas = None
        
    def show(self):
        """Show the statistics dialog."""
        if self.dialog is not None:
            self.dialog.lift()
            return
            
        self._create_dialog()
        self._populate_task_list()
        self._setup_chart_area()
        
    def _create_dialog(self):
        """Create the main dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Task Statistics")
        self.dialog.geometry("1000x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Handle dialog close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Create main container with horizontal split
        main_frame = tk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel for task selection (50% width)
        left_frame = tk.Frame(main_frame, width=480)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 5))
        left_frame.pack_propagate(False)
        
        # Right panel for charts (50% width)
        right_frame = tk.Frame(main_frame, width=480)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self._create_left_panel(left_frame)
        self._create_right_panel(right_frame)
        
        # Bottom button frame
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ok_button = tk.Button(button_frame, text="Ok", command=self._on_close)
        ok_button.pack(side=tk.RIGHT)
        
    def _create_left_panel(self, parent):
        """Create the left panel with task list."""
        # Title
        title_label = tk.Label(parent, text="Select Tasks:", font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Task list with scrollbar
        list_frame = tk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.task_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.EXTENDED,  # Allow multiple selection
            yscrollcommand=scrollbar.set,
            font=("Arial", 10)
        )
        self.task_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.task_listbox.yview)
        
        # Bind selection change event
        self.task_listbox.bind('<<ListboxSelect>>', self._on_task_selection_change)
        
    def _create_right_panel(self, parent):
        """Create the right panel with chart options and display area."""
        # Chart options frame
        options_frame = tk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grouping dropdown
        grouping_frame = tk.Frame(options_frame)
        grouping_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(grouping_frame, text="Grouping:").pack(side=tk.LEFT)
        self.grouping_var = tk.StringVar(value="Day")
        grouping_combo = ttk.Combobox(
            grouping_frame,
            textvariable=self.grouping_var,
            values=["Day", "Week"],
            state="readonly",
            width=8
        )
        grouping_combo.pack(side=tk.LEFT, padx=(5, 0))
        grouping_combo.bind('<<ComboboxSelected>>', self._on_options_change)
        
        # Ignore weekends checkbox
        self.ignore_weekends_var = tk.BooleanVar(value=False)
        ignore_weekends_cb = tk.Checkbutton(
            options_frame,
            text="Ignore weekends",
            variable=self.ignore_weekends_var,
            command=self._on_options_change
        )
        ignore_weekends_cb.pack(side=tk.LEFT, padx=(20, 0))
        
        # Chart display area
        self.chart_frame = tk.Frame(parent, bg="white", relief=tk.SUNKEN, bd=1)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
    def _populate_task_list(self):
        """Populate the task list with all unique tasks."""
        try:
            unique_tasks = self.task_service.get_all_unique_tasks()
            
            self.task_listbox.delete(0, tk.END)
            
            for activity_name, task_name in unique_tasks:
                display_text = f"{activity_name} - {task_name}"
                self.task_listbox.insert(tk.END, display_text)
                
            log_debug(f"Populated task list with {len(unique_tasks)} tasks")
            
        except Exception as e:
            log_error(f"Failed to populate task list: {e}")
            
    def _setup_chart_area(self):
        """Setup the matplotlib chart area."""
        try:
            # Create matplotlib figure
            self.figure = Figure(figsize=(6, 4), dpi=100)
            self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Show initial empty chart
            self._show_empty_chart()
            
        except Exception as e:
            log_error(f"Failed to setup chart area: {e}")
            
    def _show_empty_chart(self):
        """Show an empty chart with instructions."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, "Select tasks from the list to view statistics", 
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
        
    def _on_task_selection_change(self, event=None):
        """Handle task selection change."""
        self._update_chart()
        
    def _on_options_change(self, event=None):
        """Handle chart options change."""
        self._update_chart()
        
    def _update_chart(self):
        """Update the chart based on current selection and options."""
        try:
            # Get selected tasks
            selected_indices = self.task_listbox.curselection()
            if not selected_indices:
                self._show_empty_chart()
                return
                
            # Parse selected tasks
            selected_tasks = []
            unique_tasks = self.task_service.get_all_unique_tasks()
            
            for index in selected_indices:
                if index < len(unique_tasks):
                    selected_tasks.append(unique_tasks[index])
            
            if not selected_tasks:
                self._show_empty_chart()
                return
                
            # Get chart options
            grouping = self.grouping_var.get()
            ignore_weekends = self.ignore_weekends_var.get()
            
            # Get statistics data
            stats_data = self.task_service.get_task_statistics(
                selected_tasks, grouping, ignore_weekends, limit=10
            )
            
            if not stats_data:
                self._show_empty_chart()
                return
                
            # Create chart
            if grouping == "Day":
                self._create_daily_chart(stats_data)
            else:
                self._create_weekly_chart(stats_data)
                
        except Exception as e:
            log_error(f"Failed to update chart: {e}")
            self._show_empty_chart()
            
    def _create_daily_chart(self, stats_data: Dict):
        """Create a daily completion chart."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Prepare data for plotting
        all_dates = set()
        for task_data in stats_data.values():
            for entry in task_data:
                all_dates.add(entry['date'])
        
        if not all_dates:
            self._show_empty_chart()
            return
            
        sorted_dates = sorted(all_dates, reverse=True)[:10]  # Last 10 days
        date_labels = [entry.split('-')[1] + '-' + entry.split('-')[2] for entry in sorted_dates]
        
        # Plot each task
        bar_width = 0.8 / len(stats_data) if stats_data else 0.8
        x_positions = range(len(sorted_dates))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, (task_name, task_data) in enumerate(stats_data.items()):
            # Create completion data for each date
            completion_data = []
            for date_str in sorted_dates:
                completed = any(entry['date'] == date_str and entry['completed'] 
                              for entry in task_data)
                completion_data.append(1 if completed else 0)
            
            # Plot bars
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = colors[i % len(colors)]
            ax.bar(x_offset, completion_data, bar_width, label=task_name, 
                  color=color, alpha=0.7)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Completed (1) / Not Completed (0)')
        ax.set_title('Daily Task Completion')
        ax.set_xticks(x_positions)
        ax.set_xticklabels(date_labels, rotation=45)
        ax.set_ylim(0, 1.2)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _create_weekly_chart(self, stats_data: Dict):
        """Create a weekly completion chart."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Prepare data for plotting
        all_weeks = set()
        for task_data in stats_data.values():
            for entry in task_data:
                all_weeks.add(entry['week_start'])
        
        if not all_weeks:
            self._show_empty_chart()
            return
            
        sorted_weeks = sorted(all_weeks, reverse=True)[:10]  # Last 10 weeks
        week_labels = []
        
        # Plot each task
        bar_width = 0.8 / len(stats_data) if stats_data else 0.8
        x_positions = range(len(sorted_weeks))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                 '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        
        for i, (task_name, task_data) in enumerate(stats_data.items()):
            # Create completion rate data for each week
            completion_rates = []
            for week_start in sorted_weeks:
                rate = 0
                for entry in task_data:
                    if entry['week_start'] == week_start:
                        rate = entry['completion_rate']
                        if i == 0:  # Only add label once
                            week_labels.append(entry['display_label'])
                        break
                completion_rates.append(rate)
            
            # Plot bars
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = colors[i % len(colors)]
            ax.bar(x_offset, completion_rates, bar_width, label=task_name, 
                  color=color, alpha=0.7)
        
        ax.set_xlabel('Week')
        ax.set_ylabel('Completion Rate')
        ax.set_title('Weekly Task Completion Rate')
        ax.set_xticks(x_positions)
        ax.set_xticklabels(week_labels, rotation=45)
        ax.set_ylim(0, 1.1)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _on_close(self):
        """Handle dialog close."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


def open_task_statistics_dialog(parent):
    """Open the task statistics dialog."""
    try:
        task_service = TaskTrackingService()
        dialog = TaskStatisticsDialog(parent, task_service)
        dialog.show()
    except Exception as e:
        log_error(f"Failed to open task statistics dialog: {e}")
        tk.messagebox.showerror("Error", f"Failed to open statistics dialog: {e}")
