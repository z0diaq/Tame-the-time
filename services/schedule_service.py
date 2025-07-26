"""
Schedule service for handling schedule-related business operations.
Separates schedule management logic from UI concerns.
"""

from datetime import datetime, time
from typing import Dict, List, Optional, Tuple, Any, Callable
import yaml
import os
from pathlib import Path

from models.schedule import Schedule, ScheduledActivity
from utils.logging import log_info, log_error, log_debug
from constants import FileConstants


class ScheduleService:
    """Service for managing schedule operations and persistence."""
    
    def __init__(self, now_provider: Optional[Callable[[], datetime]] = None):
        """
        Initialize ScheduleService.
        
        Args:
            now_provider: Function that returns current datetime
        """
        self.now_provider = now_provider or datetime.now
        self._schedule: Optional[Schedule] = None
        self._config_path: Optional[str] = None
        self._is_changed = False
    
    @property
    def schedule(self) -> Optional[Schedule]:
        """Get current schedule."""
        return self._schedule
    
    @property
    def config_path(self) -> Optional[str]:
        """Get current configuration file path."""
        return self._config_path
    
    @property
    def is_changed(self) -> bool:
        """Check if schedule has unsaved changes."""
        return self._is_changed
    
    def mark_changed(self) -> None:
        """Mark schedule as having unsaved changes."""
        self._is_changed = True
    
    def mark_saved(self) -> None:
        """Mark schedule as saved (no unsaved changes)."""
        self._is_changed = False
    
    def load_schedule(self, config_path: Optional[str] = None) -> Tuple[Schedule, str]:
        """
        Load schedule from configuration file.
        
        Args:
            config_path: Path to configuration file (optional)
            
        Returns:
            Tuple of (Schedule, actual_config_path_used)
        """
        from config.config_loader import load_schedule as load_schedule_legacy
        
        # Use legacy loader for now, then convert to new model
        schedule_data, actual_path = load_schedule_legacy(config_path, self.now_provider)
        
        self._schedule = Schedule(schedule_data)
        self._config_path = actual_path
        self._is_changed = False
        
        log_info(f"Loaded schedule with {len(self._schedule)} activities from {actual_path}")
        return self._schedule, actual_path
    
    def save_schedule(self, file_path: Optional[str] = None, ask_confirmation: bool = True) -> bool:
        """
        Save current schedule to file.
        
        Args:
            file_path: Path to save to (uses current config_path if None)
            ask_confirmation: Whether to ask for user confirmation
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self._schedule:
            log_error("No schedule to save")
            return False
        
        target_path = file_path or self._config_path
        if not target_path:
            log_error("No file path specified for saving")
            return False
        
        try:
            schedule_data = self._schedule.to_dicts()
            with open(target_path, 'w') as f:
                yaml.dump(schedule_data, f, default_flow_style=False)
            
            self._config_path = target_path
            self._is_changed = False
            log_info(f"Saved schedule to {target_path}")
            return True
            
        except Exception as e:
            log_error(f"Failed to save schedule: {e}")
            return False
    
    def create_new_schedule(self) -> Schedule:
        """Create a new empty schedule."""
        self._schedule = Schedule()
        self._config_path = None
        self._is_changed = False
        return self._schedule
    
    def add_activity(self, activity_data: Dict[str, Any]) -> bool:
        """
        Add new activity to schedule.
        
        Args:
            activity_data: Dictionary containing activity information
            
        Returns:
            True if added successfully, False otherwise
        """
        if not self._schedule:
            return False
        
        try:
            activity = ScheduledActivity.from_dict(activity_data)
            self._schedule.add_activity(activity)
            self._is_changed = True
            log_debug(f"Added activity: {activity.name}")
            return True
        except Exception as e:
            log_error(f"Failed to add activity: {e}")
            return False
    
    def remove_activity(self, activity_index: int) -> bool:
        """
        Remove activity by index.
        
        Args:
            activity_index: Index of activity to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if not self._schedule or activity_index < 0 or activity_index >= len(self._schedule):
            return False
        
        try:
            activity = self._schedule[activity_index]
            if self._schedule.remove_activity(activity):
                self._is_changed = True
                log_debug(f"Removed activity: {activity.name}")
                return True
        except Exception as e:
            log_error(f"Failed to remove activity: {e}")
        
        return False
    
    def clear_schedule(self) -> None:
        """Clear all activities from schedule."""
        if self._schedule:
            self._schedule.clear()
            self._is_changed = True
            log_debug("Cleared all activities from schedule")
    
    def get_current_activity(self) -> Optional[ScheduledActivity]:
        """Get currently active activity."""
        if not self._schedule:
            return None
        
        current_time = self.now_provider().time()
        return self._schedule.get_current_activity(current_time)
    
    def get_next_activity(self) -> Optional[Tuple[ScheduledActivity, datetime]]:
        """
        Get next scheduled activity and its start time.
        
        Returns:
            Tuple of (activity, start_datetime) or None if no next activity
        """
        if not self._schedule:
            return None
        
        now = self.now_provider()
        current_time = now.time()
        today = now.date()
        
        next_activity = self._schedule.get_next_activity(current_time)
        if next_activity:
            next_start = datetime.combine(today, next_activity.start_time_obj)
            return next_activity, next_start
        
        # If no activity today, check first activity of next day
        if len(self._schedule) > 0:
            first_activity = self._schedule[0]
            tomorrow = today.replace(day=today.day + 1)
            next_start = datetime.combine(tomorrow, first_activity.start_time_obj)
            return first_activity, next_start
        
        return None
    
    def get_activities_for_display(self) -> List[Dict[str, Any]]:
        """
        Get activities formatted for UI display.
        
        Returns:
            List of activity dictionaries for UI consumption
        """
        if not self._schedule:
            return []
        
        return self._schedule.to_dicts()
    
    def validate_activity_data(self, activity_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate activity data before adding to schedule.
        
        Args:
            activity_data: Activity data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Try to create activity to validate
            ScheduledActivity.from_dict(activity_data)
            return True, ""
        except Exception as e:
            return False, str(e)
