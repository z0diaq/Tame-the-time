"""
Schedule and Task models for business logic separation.
Contains data structures and operations for managing tasks and schedules.
"""

from datetime import datetime, time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from utils.time_utils import TimeUtils


@dataclass
class Task:
    """Represents a single task within a scheduled activity."""
    name: str
    description: str = ""
    completed: bool = False
    
    def mark_completed(self) -> None:
        """Mark this task as completed."""
        self.completed = True
    
    def mark_incomplete(self) -> None:
        """Mark this task as incomplete."""
        self.completed = False


@dataclass
class ScheduledActivity:
    """Represents a scheduled activity with time bounds and associated tasks."""
    name: str
    start_time: str  # Format: "HH:MM"
    end_time: str    # Format: "HH:MM"
    description: List[str] = field(default_factory=list)
    tasks: List[str] = field(default_factory=list)
    
    def __post_init__(self) -> None:
        """Validate time formats after initialization using TimeUtils."""
        try:
            TimeUtils.parse_time_with_validation(self.start_time)
            TimeUtils.parse_time_with_validation(self.end_time)
        except ValueError as e:
            raise ValueError(f"Invalid time format in ScheduledActivity: {e}") from e
    
    @property
    def start_time_obj(self) -> time:
        """Get start time as a time object."""
        return TimeUtils.parse_time_with_validation(self.start_time)
    
    @property
    def end_time_obj(self) -> time:
        """Get end time as a time object."""
        return TimeUtils.parse_time_with_validation(self.end_time)
    
    @property
    def duration_minutes(self) -> int:
        """Get duration in minutes."""
        return TimeUtils.calculate_duration_minutes(self.start_time, self.end_time)
    
    def is_active_at(self, current_time: time) -> bool:
        """Check if this activity is active at the given time."""
        # Handle activities that span past midnight (e.g., 23:30 to 01:30)
        if self.end_time_obj < self.start_time_obj:  # Activity crosses midnight
            return current_time >= self.start_time_obj or current_time < self.end_time_obj
        else:
            return self.start_time_obj <= current_time < self.end_time_obj
    
    def is_finished_at(self, current_time: time) -> bool:
        """Check if this activity is finished at the given time."""
        # Handle activities that span past midnight
        if self.end_time_obj < self.start_time_obj:  # Activity crosses midnight
            # Finished if current_time is >= end_time AND < start_time
            # (i.e., in the gap between end and start of next occurrence)
            return current_time >= self.end_time_obj and current_time < self.start_time_obj
        else:
            return self.end_time_obj <= current_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for serialization."""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "description": self.description,
            "tasks": self.tasks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledActivity':
        """Create ScheduledActivity from dictionary data."""
        return cls(
            name=data["name"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            description=data.get("description", []),
            tasks=data.get("tasks", [])
        )


class Schedule:
    """Manages a collection of scheduled activities."""
    
    def __init__(self, activities: Optional[List[Dict[str, Any]]] = None):
        """Initialize schedule with optional list of activity dictionaries."""
        self._activities: List[ScheduledActivity] = []
        if activities:
            self.load_from_dicts(activities)
    
    def load_from_dicts(self, activities: List[Dict[str, Any]]) -> None:
        """Load activities from list of dictionaries."""
        self._activities = [ScheduledActivity.from_dict(activity) for activity in activities]
        self._sort_activities()
    
    def _sort_activities(self) -> None:
        """Sort activities by start time."""
        self._activities.sort(key=lambda a: a.start_time_obj)
    
    @property
    def activities(self) -> List[ScheduledActivity]:
        """Get list of all activities."""
        return self._activities.copy()
    
    def add_activity(self, activity: ScheduledActivity) -> None:
        """Add a new activity to the schedule."""
        self._activities.append(activity)
        self._sort_activities()
    
    def remove_activity(self, activity: ScheduledActivity) -> bool:
        """Remove an activity from the schedule. Returns True if removed."""
        try:
            self._activities.remove(activity)
            return True
        except ValueError:
            return False
    
    def get_current_activity(self, current_time: time) -> Optional[ScheduledActivity]:
        """Get the currently active activity at the given time."""
        for activity in self._activities:
            if activity.is_active_at(current_time):
                return activity
        return None
    
    def get_next_activity(self, current_time: time) -> Optional[ScheduledActivity]:
        """Get the next scheduled activity after the given time."""
        for activity in self._activities:
            if activity.start_time_obj > current_time:
                return activity
        return None
    
    def get_activities_in_range(self, start_time: time, end_time: time) -> List[ScheduledActivity]:
        """Get all activities that overlap with the given time range."""
        result = []
        for activity in self._activities:
            # Check if activity overlaps with the range
            if (activity.start_time_obj < end_time and activity.end_time_obj > start_time):
                result.append(activity)
        return result
    
    def clear(self) -> None:
        """Remove all activities from the schedule."""
        self._activities.clear()
    
    def to_dicts(self) -> List[Dict[str, Any]]:
        """Convert schedule to list of dictionaries for serialization."""
        return [activity.to_dict() for activity in self._activities]
    
    def __len__(self) -> int:
        """Get number of activities in schedule."""
        return len(self._activities)
    
    def __iter__(self):
        """Make schedule iterable."""
        return iter(self._activities)
    
    def __getitem__(self, index: int) -> ScheduledActivity:
        """Allow indexing into schedule."""
        return self._activities[index]
