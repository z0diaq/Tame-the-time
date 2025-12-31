# ADR-008: Matplotlib for Statistics Visualization

**Title:** Matplotlib for Statistics Visualization  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The task tracking system needed to display statistical charts showing:

- Daily task completion trends over time
- Weekly aggregated completion rates
- Multi-task comparison in single charts
- Interactive filtering (ignore weekends, grouping options)
- Professional-quality visualizations for progress analysis

Requirements:
- Integration with Tkinter GUI
- Support for bar charts with multiple data series
- Customizable time groupings (Day/Week)
- Data filtering capabilities
- Export potential for future features

## Decision

We implemented Matplotlib with Tkinter backend for statistics visualization:

```python
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class TaskStatisticsDialog:
    def _setup_chart_area(self):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
```

**Chart Types Implemented:**
- Daily completion charts (binary completion status)
- Weekly completion rate charts (percentage-based)
- Multi-task comparison with color coding
- Time-series visualization with proper date formatting

**Features:**
- Interactive task selection (multi-select listbox)
- Dynamic chart updates based on selection
- Grouping options (Day/Week) with different visualizations
- Weekend filtering for work-focused analysis
- Professional styling with legends and proper labeling

## Consequences

**Positive:**
- Professional-quality charts with extensive customization
- Excellent Tkinter integration through backend
- Rich visualization capabilities (colors, legends, annotations)
- Familiar charting library with extensive documentation
- Export capabilities for future features (PNG, PDF, etc.)
- Handles complex multi-series data elegantly

**Negative:**
- Additional dependency (matplotlib) increases application size
- Slower startup time due to matplotlib import overhead
- Memory usage higher than simple custom charts
- Platform-specific font rendering differences

## Evolution and Enhancements

### August 2025 Enhancements

**Extended Time Period Support:**
- Added Monthly and Yearly statistics alongside existing Daily and Weekly views
- Monthly stats calculate completion rates as: completed days / total tracked days in month
- Yearly stats calculate completion rates as: completed days / total tracked days in year
- Enhanced service layer with `_get_monthly_statistics()` and `_get_yearly_statistics()` methods

**Improved Task Identification:**
- Changed task display format from UUIDs to "Activity name / task name" format
- Enhanced user experience by providing clear context for each task
- Updated all chart legends to use human-readable task identification
- Integrated with app instance for activity name resolution

**User Experience Improvements:**
- Implemented task selection persistence across grouping changes
- Users can now switch between Day/Week/Month/Year views while maintaining selected tasks
- Eliminates need to reselect tasks when exploring different time periods
- Improved workflow continuity for statistical analysis

**Task Filtering Enhancements:**
- Added "Show only tasks with known activity" checkbox to filter out "Unknown Activity" tasks
- Added "Only show tasks for current schedule" checkbox to filter tasks by current loaded schedule
- Both filters are persistent across app sessions via settings storage
- Filters work independently and can be combined for precise task selection
- Default behavior shows only tasks from current schedule with known activities

**Week Label Format Enhancement (December 2025):**
- Updated weekly statistics labels to show complete Monday-Sunday date range
- New format: `month.day-month.day (Xd)` where X is the number of tracked days
- First date always represents Monday (ISO week start)
- Second date always represents Sunday (ISO week end)
- Tracked days count shows actual days with data (e.g., "2d" if only Monday and Tuesday were tracked)
- Example: `12.23-12.29 (5d)` means week from December 23 (Monday) to December 29 (Sunday) with 5 days of tracked data
- Provides clearer context about week boundaries and data completeness

**Technical Implementation:**
```python
# Extended grouping support
def get_task_statistics(self, task_list: List[str], 
                      grouping: str = "Day", ignore_weekends: bool = False,
                      limit: int = 10) -> Dict[str, List[Dict]]:
    # Now supports: "Day", "Week", "Month", "Year"

# Task selection persistence
class TaskStatisticsDialog:
    def __init__(self, parent, task_tracking_service, app=None):
        self.selected_task_indices = []  # Store selection state
        self.show_known_only_var = None  # Filter for known activities
        self.show_current_schedule_only_var = None  # Filter for current schedule
    
    def _on_options_change(self, event=None):
        self._restore_task_selection()  # Preserve selection
        self._update_chart()
    
    def _apply_task_filter(self):
        # Apply both known activity and current schedule filters
        current_schedule_activity_ids = set()
        if self.parent.schedule:
            for activity in self.parent.schedule:
                if activity.get('id'):
                    current_schedule_activity_ids.add(activity['id'])
        
        for task_info in self.all_task_data:
            # Filter by known activity
            if show_known_only and activity_name == "Unknown Activity":
                continue
            # Filter by current schedule
            if show_current_schedule_only and activity_id not in current_schedule_activity_ids:
                continue
```

**Chart Types Now Available:**
- Daily completion charts (binary 0/1 completion status)
- Weekly completion rate charts (percentage-based aggregation)
- Monthly completion rate charts (monthly aggregation with completion rates)
- Yearly completion rate charts (yearly aggregation with completion rates)
- All charts support multi-task comparison with "Activity / Task" labeling

## Alternatives

1. **Custom Tkinter Charts**: Lightweight but limited visualization capabilities
2. **Plotly**: Modern and interactive but requires web browser integration
3. **PyQt Charts**: Excellent but would require changing entire UI framework
4. **ASCII Charts**: Simple but unprofessional appearance for desktop application
