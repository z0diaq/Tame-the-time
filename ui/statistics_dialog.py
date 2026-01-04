"""
Statistics dialog for displaying task completion charts and analytics.
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from typing import List, Dict, Tuple
from constants import Colors
from services.task_tracking_service import TaskTrackingService
from utils.logging import log_debug, log_error
from utils.translator import t


class TaskStatisticsDialog:
    """Dialog for displaying task statistics with charts."""
    
    def __init__(self, parent, task_tracking_service: TaskTrackingService):
        """Initialize the statistics dialog."""
        self.parent = parent
        self.task_service = task_tracking_service
        self.dialog = None
        self.task_listbox = None
        self.task_canvas = None
        self.task_scrollbar = None
        self.grouping_var = None
        self.ignore_weekends_var = None
        self.show_known_only_var = None
        self.show_current_schedule_only_var = None
        self.chart_frame = None
        self.figure = None
        self.canvas = None
        self.selected_task_indices = []  # Store selected task indices for persistence
        self.all_task_data = []  # Store all tasks before filtering
        self.filtered_task_data = []  # Store filtered tasks for display
        self.task_colors = {}  # Store color assignments for each task UUID
        self.task_canvas_items = []  # Store canvas item IDs for task list
        self.checkbox_widgets = {}  # Store checkbox widget references for dynamic updates
        
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
        self.dialog.title(t("window.task_statistics"))
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
        
        ok_button = tk.Button(button_frame, text=t("button.ok"), command=self._on_close)
        ok_button.pack(side=tk.RIGHT)
        
    def _create_left_panel(self, parent):
        """Create the left panel with task list."""
        # Title
        title_label = tk.Label(parent, text=t("label.select_tasks"), font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Filter checkbox
        filter_frame = tk.Frame(parent)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Load settings from parent app settings
        show_known_only_default = self.parent.statistics_show_known_only
        show_current_schedule_only_default = getattr(self.parent, 'statistics_show_current_schedule_only', True)
        
        self.show_known_only_var = tk.BooleanVar(value=show_known_only_default)
        show_known_only_cb = tk.Checkbutton(
            filter_frame,
            text=t("label.show_only_known_activity"),
            variable=self.show_known_only_var,
            command=self._on_filter_change
        )
        show_known_only_cb.pack(anchor=tk.W)
        self.checkbox_widgets['show_known_only'] = show_known_only_cb
        
        # Current schedule filter checkbox
        self.show_current_schedule_only_var = tk.BooleanVar(value=show_current_schedule_only_default)
        show_current_schedule_only_cb = tk.Checkbutton(
            filter_frame,
            text=t("label.show_only_current_schedule"),
            variable=self.show_current_schedule_only_var,
            command=self._on_filter_change
        )
        show_current_schedule_only_cb.pack(anchor=tk.W)
        self.checkbox_widgets['show_current_schedule_only'] = show_current_schedule_only_cb
        
        # Task list with scrollbar (using Canvas for color indicators)
        list_frame = tk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.task_scrollbar = tk.Scrollbar(list_frame)
        self.task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.task_canvas = tk.Canvas(
            list_frame,
            yscrollcommand=self.task_scrollbar.set,
            bg="white",
            highlightthickness=0
        )
        self.task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.task_scrollbar.config(command=self.task_canvas.yview)
        
        # Bind click event for task selection
        self.task_canvas.bind('<Button-1>', self._on_task_click)
        self.task_canvas.bind('<Configure>', self._on_canvas_resize)
        
    def _create_right_panel(self, parent):
        """Create the right panel with chart options and display area."""
        # Chart options frame
        options_frame = tk.Frame(parent)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grouping dropdown
        grouping_frame = tk.Frame(options_frame)
        grouping_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(grouping_frame, text=t("label.grouping")).pack(side=tk.LEFT)
        self.grouping_var = tk.StringVar(value=t("combo.day"))
        grouping_combo = ttk.Combobox(
            grouping_frame,
            textvariable=self.grouping_var,
            values=[t("combo.day"), t("combo.week"), t("combo.month"), t("combo.year")],
            state="readonly",
            width=8
        )
        grouping_combo.pack(side=tk.LEFT, padx=(5, 0))
        grouping_combo.bind('<<ComboboxSelected>>', self._on_options_change)
        
        # Ignore weekends checkbox
        self.ignore_weekends_var = tk.BooleanVar(value=False)
        ignore_weekends_cb = tk.Checkbutton(
            options_frame,
            text=t("label.ignore_weekends"),
            variable=self.ignore_weekends_var,
            command=self._on_options_change
        )
        ignore_weekends_cb.pack(side=tk.LEFT, padx=(20, 0))
        self.checkbox_widgets['ignore_weekends'] = ignore_weekends_cb
        
        # Bind checkbox state change events for text updates
        self.show_known_only_var.trace('w', self._on_checkbox_state_change)
        self.show_current_schedule_only_var.trace('w', self._on_checkbox_state_change)
        self.ignore_weekends_var.trace('w', self._on_checkbox_state_change)
        
        # Initialize checkbox texts
        self._update_checkbox_texts()
        
        # Chart display area
        self.chart_frame = tk.Frame(parent, bg=Colors.CHART_FRAME_BG, relief=tk.SUNKEN, bd=1)
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
    def _populate_task_list(self):
        """Populate the task list with all unique tasks."""
        try:
            unique_tasks = self.task_service.get_all_unique_tasks()
            
            # Store all task info for filtering
            self.all_task_data = []
            
            # Get chart colors for assignment
            chart_colors = Colors.get_chart_colors()
            
            for i, task_info in enumerate(unique_tasks):
                task_uuid = task_info['task_uuid']
                activity_id = task_info['activity_id']
                task_name = task_info['task_name']
                
                # Assign color to this task
                self.task_colors[task_uuid] = chart_colors[i % len(chart_colors)]
                
                # Get activity name for display format: "Activity name / task name"
                activity_name = t("activity.unknown_activity")
                if self.parent and activity_id:
                    activity = self.parent.find_activity_by_id(activity_id)
                    if activity:
                        activity_name = activity.get('name', t("activity.unknown_activity"))
                
                # Store the full task info for chart generation
                task_info_with_activity = task_info.copy()
                task_info_with_activity['activity_name'] = activity_name
                self.all_task_data.append(task_info_with_activity)
            
            # Apply filtering and populate the canvas
            self._apply_task_filter()
                
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
        ax.text(0.5, 0.5, t("chart.select_tasks_message"), 
                ha='center', va='center', transform=ax.transAxes, 
                fontsize=12, color='gray')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        self.canvas.draw()
        
    def _apply_task_filter(self):
        """Apply filtering based on the checkbox states and populate the canvas."""
        # Clear canvas
        self.task_canvas.delete('all')
        self.task_canvas_items = []
        self.filtered_task_data = []
        
        show_known_only = self.show_known_only_var.get() if self.show_known_only_var else True
        show_current_schedule_only = self.show_current_schedule_only_var.get() if self.show_current_schedule_only_var else True
        
        log_debug(f"Applying task filter: show_known_only={show_known_only}, show_current_schedule_only={show_current_schedule_only}")
        
        # Build a set of task UUIDs that exist in the current schedule
        current_schedule_task_uuids = set()
        if show_current_schedule_only and hasattr(self.parent, 'schedule') and self.parent.schedule:
            for activity in self.parent.schedule:
                if 'tasks' in activity:
                    for task in activity.get('tasks', []):
                        if isinstance(task, dict) and 'uuid' in task:
                            current_schedule_task_uuids.add(task['uuid'])
                        elif isinstance(task, str):
                            # Legacy string format - skip these in filter
                            log_debug(f"Skipping legacy string task in filter: {task}")
            log_debug(f"Current schedule task UUIDs: {current_schedule_task_uuids}")
        
        y_position = 5
        line_height = 25
        color_box_size = 15
        color_box_margin = 5
        
        for task_info in self.all_task_data:
            activity_name = task_info['activity_name']
            task_name = task_info['task_name']
            activity_id = task_info['activity_id']
            task_uuid = task_info['task_uuid']

            log_debug(f"Processing task: {activity_name} / {task_name} (activity_id={activity_id})")
            
            # Apply known activity filter: if show_known_only is True, skip "Unknown Activity" tasks
            if show_known_only and activity_name == t("activity.unknown_activity"):
                log_debug(f"Filtering out unknown activity task: {task_name}")
                continue
            
            # Apply current schedule filter: if show_current_schedule_only is True, 
            # only show tasks whose UUID exists in the current schedule
            if show_current_schedule_only:
                if not task_uuid or task_uuid not in current_schedule_task_uuids:
                    log_debug(f"Filtering out task not in current schedule: {activity_name} / {task_name} (task_uuid={task_uuid})")
                    continue
            
            log_debug(f"Including task: {activity_name} / {task_name} (activity_id={activity_id})")
            
            # Get color for this task
            task_color = self.task_colors.get(task_uuid, "#cccccc")
            
            # Draw color box
            color_box = self.task_canvas.create_rectangle(
                color_box_margin, y_position,
                color_box_margin + color_box_size, y_position + color_box_size,
                fill=task_color, outline="black", width=1
            )
            
            # Draw task text
            display_text = f"{activity_name} / {task_name}"
            text_x = color_box_margin + color_box_size + 10
            text_item = self.task_canvas.create_text(
                text_x, y_position + color_box_size // 2,
                text=display_text, anchor=tk.W, font=("Arial", 10), tags="tasktext"
            )
            
            # Create invisible click area for selection
            bbox = self.task_canvas.bbox(text_item)
            if bbox:
                click_area = self.task_canvas.create_rectangle(
                    color_box_margin, y_position,
                    bbox[2] + 5, y_position + line_height,
                    fill="", outline="", tags=f"task_{len(self.task_canvas_items)}"
                )
                self.task_canvas.tag_lower(click_area)
            
            # Store item info
            self.task_canvas_items.append({
                'color_box': color_box,
                'text': text_item,
                'y_start': y_position,
                'y_end': y_position + line_height,
                'selected': False
            })
            self.filtered_task_data.append(task_info)
            
            y_position += line_height
        
        # Update scroll region
        self.task_canvas.configure(scrollregion=(0, 0, 480, y_position))
    
    def _on_task_click(self, event):
        """Handle click on task canvas."""
        # Find which task was clicked
        y_click = self.task_canvas.canvasy(event.y)
        clicked_index = None
        
        for i, item in enumerate(self.task_canvas_items):
            if item['y_start'] <= y_click <= item['y_end']:
                clicked_index = i
                break
        
        if clicked_index is None:
            return
        
        # Toggle selection (Ctrl/Shift for multi-select)
        if event.state & 0x0004:  # Ctrl key
            # Toggle this item
            item = self.task_canvas_items[clicked_index]
            item['selected'] = not item['selected']
            if item['selected']:
                if clicked_index not in self.selected_task_indices:
                    self.selected_task_indices.append(clicked_index)
            else:
                if clicked_index in self.selected_task_indices:
                    self.selected_task_indices.remove(clicked_index)
        else:
            # Clear all and select only this one
            for item in self.task_canvas_items:
                item['selected'] = False
            self.task_canvas_items[clicked_index]['selected'] = True
            self.selected_task_indices = [clicked_index]
        
        # Redraw selections
        self._redraw_task_selections()
        
        # Update chart
        self._update_chart()
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize."""
        # Update scroll region width
        if self.task_canvas_items:
            last_y = self.task_canvas_items[-1]['y_end'] if self.task_canvas_items else 100
            self.task_canvas.configure(scrollregion=(0, 0, event.width, last_y))
    
    def _redraw_task_selections(self):
        """Redraw task list to show selections."""
        for i, item in enumerate(self.task_canvas_items):
            if item['selected']:
                # Highlight selected tasks
                self.task_canvas.itemconfig(item['text'], fill="blue", font=("Arial", 10, "bold"))
            else:
                # Normal appearance
                self.task_canvas.itemconfig(item['text'], fill="black", font=("Arial", 10))
    
    def _get_checkbox_text(self, base_key, is_checked):
        """Get checkbox text with optional state indicator."""
        base_text = t(base_key)
        if hasattr(self.parent, 'append_checkbox_state') and self.parent.append_checkbox_state:
            state = t("checkbox_state.on") if is_checked else t("checkbox_state.off")
            return f"{base_text} {state}"
        return base_text
    
    def _update_checkbox_texts(self):
        """Update all checkbox texts based on current state and settings."""
        if 'show_known_only' in self.checkbox_widgets:
            self.checkbox_widgets['show_known_only'].config(
                text=self._get_checkbox_text("label.show_only_known_activity", 
                                            self.show_known_only_var.get())
            )
        if 'show_current_schedule_only' in self.checkbox_widgets:
            self.checkbox_widgets['show_current_schedule_only'].config(
                text=self._get_checkbox_text("label.show_only_current_schedule",
                                            self.show_current_schedule_only_var.get())
            )
        if 'ignore_weekends' in self.checkbox_widgets:
            self.checkbox_widgets['ignore_weekends'].config(
                text=self._get_checkbox_text("label.ignore_weekends",
                                            self.ignore_weekends_var.get())
            )
    
    def _on_checkbox_state_change(self, *args):
        """Handle checkbox state change to update text."""
        self._update_checkbox_texts()
    
    def _on_filter_change(self):
        """Handle filter checkbox change."""
        # Save the settings
        self.parent.statistics_show_known_only = self.show_known_only_var.get()
        self.parent.statistics_show_current_schedule_only = self.show_current_schedule_only_var.get()
        if hasattr(self.parent, 'save_settings'):
            self.parent.save_settings()
        
        # Clear current selection since indices will change
        self.selected_task_indices = []
        
        # Re-apply filtering
        self._apply_task_filter()
        
        # Update chart
        self._update_chart()
    
        
    def _on_options_change(self, event=None):
        """Handle chart options change."""
        # Restore previous selection after grouping change
        self._restore_task_selection()
        self._update_chart()
        
    def _restore_task_selection(self):
        """Restore previously selected tasks after grouping change."""
        if self.selected_task_indices and self.task_canvas_items:
            # Clear current selection
            for item in self.task_canvas_items:
                item['selected'] = False
            
            # Restore previous selection
            for index in self.selected_task_indices:
                if index < len(self.task_canvas_items):
                    self.task_canvas_items[index]['selected'] = True
            
            self._redraw_task_selections()
        
    def _update_chart(self):
        """Update the chart based on current selection and options."""
        try:
            # Get selected tasks from selected_task_indices
            if not self.selected_task_indices:
                self._show_empty_chart()
                return
                
            # Parse selected tasks using filtered task data
            selected_task_uuids = []
            
            for index in self.selected_task_indices:
                if index < len(self.filtered_task_data):
                    task_info = self.filtered_task_data[index]
                    selected_task_uuids.append(task_info['task_uuid'])
            
            if not selected_task_uuids:
                self._show_empty_chart()
                return
                
            # Get chart options - convert display names back to internal values
            grouping_display = self.grouping_var.get()
            grouping_map = {
                t("combo.day"): "Day",
                t("combo.week"): "Week", 
                t("combo.month"): "Month",
                t("combo.year"): "Year"
            }
            grouping = grouping_map.get(grouping_display, "Day")
            ignore_weekends = self.ignore_weekends_var.get()
            
            # Get statistics data using task UUIDs
            stats_data = self.task_service.get_task_statistics(
                selected_task_uuids, grouping, ignore_weekends, limit=10
            )
            
            if not stats_data:
                self._show_empty_chart()
                return
                
            # Create chart
            if grouping == "Day":
                self._create_daily_chart(stats_data)
            elif grouping == "Week":
                self._create_weekly_chart(stats_data)
            elif grouping == "Month":
                self._create_monthly_chart(stats_data)
            else:  # Year
                self._create_yearly_chart(stats_data)
                
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
        
        for i, (task_uuid, task_data) in enumerate(stats_data.items()):
            # Create completion data for each date
            completion_data = []
            for date_str in sorted_dates:
                completed = any(entry['date'] == date_str and entry['completed'] 
                              for entry in task_data)
                completion_data.append(1 if completed else 0)
            
            # Plot bars with assigned color
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = self.task_colors.get(task_uuid, "#cccccc")
            ax.bar(x_offset, completion_data, bar_width, color=color, alpha=0.7)
        
        ax.set_xlabel(t('chart.date'))
        ax.set_ylabel(t('chart.completed_not_completed'))
        ax.set_title(t('chart.daily_completion'))
        ax.set_xticks(x_positions)
        ax.set_xticklabels(date_labels, rotation=45, ha='right')
        ax.set_ylim(0, 1.2)
        
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
                all_weeks.add(entry['date'])
        
        if not all_weeks:
            self._show_empty_chart()
            return
            
        sorted_weeks = sorted(all_weeks, reverse=True)[:10]  # Last 10 weeks
        week_labels = []
        
        # Plot each task
        bar_width = 0.8 / len(stats_data) if stats_data else 0.8
        x_positions = range(len(sorted_weeks))
        
        for i, (task_uuid, task_data) in enumerate(stats_data.items()):
            # Create completion data for each week
            completion_rates = []
            for week_start in sorted_weeks:
                rate = 0
                for entry in task_data:
                    if entry.get('date') == week_start:  
                        rate = entry['completed']  
                        if i == 0:  # Only add label once
                            week_labels.append(entry['display_label'])
                        break
                completion_rates.append(rate)
            
            # Plot bars with assigned color
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = self.task_colors.get(task_uuid, "#cccccc")
            ax.bar(x_offset, completion_rates, bar_width, color=color, alpha=0.7)
        
        log_debug(f"Prepared week labels: {week_labels}")
        ax.set_xlabel(t('chart.week'))
        ax.set_ylabel(t('chart.completion_rate'))
        ax.set_title(t('chart.weekly_completion'))
        ax.set_xticks(x_positions)
        ax.set_xticklabels(week_labels, rotation=45, ha='right')
        ax.set_ylim(0, 1.1)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _create_monthly_chart(self, stats_data: Dict):
        """Create a monthly completion chart."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Prepare data for plotting
        all_months = set()
        for task_data in stats_data.values():
            for entry in task_data:
                all_months.add(entry['date'])
        
        if not all_months:
            self._show_empty_chart()
            return
            
        sorted_months = sorted(all_months, reverse=True)[:10]  # Last 10 months
        month_labels = []
        
        # Plot each task
        bar_width = 0.8 / len(stats_data) if stats_data else 0.8
        x_positions = range(len(sorted_months))
        
        for i, (task_uuid, task_data) in enumerate(stats_data.items()):
            # Create completion data for each month
            completion_rates = []
            for month_date in sorted_months:
                rate = 0
                for entry in task_data:
                    if entry['date'] == month_date:
                        rate = entry['completed']
                        if i == 0:  # Only add label once
                            month_labels.append(entry['display_label'])
                        break
                completion_rates.append(rate)
            
            # Plot bars with assigned color
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = self.task_colors.get(task_uuid, "#cccccc")
            ax.bar(x_offset, completion_rates, bar_width, color=color, alpha=0.7)
        
        ax.set_xlabel(t('chart.month'))
        ax.set_ylabel(t('chart.completion_rate'))
        ax.set_title(t('chart.monthly_completion'))
        ax.set_xticks(x_positions)
        ax.set_xticklabels(month_labels, rotation=45, ha='right')
        ax.set_ylim(0, 1.1)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _create_yearly_chart(self, stats_data: Dict):
        """Create a yearly completion chart."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # Prepare data for plotting
        all_years = set()
        for task_data in stats_data.values():
            for entry in task_data:
                all_years.add(entry['date'])
        
        if not all_years:
            self._show_empty_chart()
            return
            
        sorted_years = sorted(all_years, reverse=True)[:10]  # Last 10 years
        year_labels = []
        
        # Plot each task
        bar_width = 0.8 / len(stats_data) if stats_data else 0.8
        x_positions = range(len(sorted_years))
        
        for i, (task_uuid, task_data) in enumerate(stats_data.items()):
            # Create completion data for each year
            completion_rates = []
            for year_date in sorted_years:
                rate = 0
                for entry in task_data:
                    if entry['date'] == year_date:
                        rate = entry['completed']
                        if i == 0:  # Only add label once
                            year_labels.append(entry['display_label'])
                        break
                completion_rates.append(rate)
            
            # Plot bars with assigned color
            x_offset = [x + (i - len(stats_data)/2 + 0.5) * bar_width for x in x_positions]
            color = self.task_colors.get(task_uuid, "#cccccc")
            ax.bar(x_offset, completion_rates, bar_width, color=color, alpha=0.7)
        
        ax.set_xlabel(t('chart.year'))
        ax.set_ylabel(t('chart.completion_rate'))
        ax.set_title(t('chart.yearly_completion'))
        ax.set_xticks(x_positions)
        ax.set_xticklabels(year_labels, rotation=45, ha='right')
        ax.set_ylim(0, 1.1)
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def _on_close(self):
        """Handle dialog close."""
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


def open_task_statistics_dialog(parent, db_path: str = None):
    """Open the task statistics dialog."""
    try:
        task_service = TaskTrackingService(db_path)
        dialog = TaskStatisticsDialog(parent, task_service)
        dialog.show()
    except Exception as e:
        log_error(f"Failed to open task statistics dialog: {e}")
        messagebox.showerror("Error", f"Failed to open statistics dialog: {e}")
