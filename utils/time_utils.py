from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any, Tuple
from constants import ValidationConstants


class TimeUtils:
    """Consolidated time utilities for parsing, validation, and formatting."""
    
    @staticmethod
    def parse_time_with_validation(time_str: str) -> time:
        """
        Parse and validate time string with comprehensive error handling.
        
        Args:
            time_str: Time string in format 'HH:MM' or 'HH:MM:SS'
            
        Returns:
            time object
            
        Raises:
            ValueError: If time string is invalid or out of range
        """
        if not isinstance(time_str, str):
            raise ValueError(f"Time must be a string, got {type(time_str)}")
        
        time_str = time_str.strip()
        if not time_str:
            raise ValueError("Time string cannot be empty")
        
        parts = time_str.split(":")
        
        try:
            if len(parts) == 2:
                hour, minute = int(parts[0]), int(parts[1])
                second = 0
            elif len(parts) == 3:
                hour, minute, second = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                raise ValueError(f"Invalid time format: {time_str}. Expected 'HH:MM' or 'HH:MM:SS'")
            
            # Validate ranges
            if not (ValidationConstants.MIN_HOUR <= hour <= ValidationConstants.MAX_HOUR):
                raise ValueError(f"Hour {hour} out of range ({ValidationConstants.MIN_HOUR}-{ValidationConstants.MAX_HOUR})")
            if not (ValidationConstants.MIN_MINUTE <= minute <= ValidationConstants.MAX_MINUTE):
                raise ValueError(f"Minute {minute} out of range ({ValidationConstants.MIN_MINUTE}-{ValidationConstants.MAX_MINUTE})")
            if not (0 <= second <= 59):
                raise ValueError(f"Second {second} out of range (0-59)")
            
            return time(hour, minute, second)
            
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid time format: {time_str}. All parts must be numbers")
            raise
    
    @staticmethod
    def format_time_display(t: time) -> str:
        """Format a time object to HH:MM string for display."""
        return t.strftime("%H:%M")
    
    @staticmethod
    def format_time_with_seconds(t: time) -> str:
        """Format a time object to HH:MM:SS string."""
        return t.strftime("%H:%M:%S")
    
    @staticmethod
    def calculate_duration_minutes(start_time_str: str, end_time_str: str) -> int:
        """
        Calculate duration between two time strings in minutes.
        
        Args:
            start_time_str: Start time in 'HH:MM' format
            end_time_str: End time in 'HH:MM' format
            
        Returns:
            Duration in minutes
        """
        start_time = TimeUtils.parse_time_with_validation(start_time_str)
        end_time = TimeUtils.parse_time_with_validation(end_time_str)
        
        # Convert to minutes since midnight
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        
        # Handle case where end time is next day (e.g., 23:00 to 01:00)
        if end_minutes < start_minutes:
            end_minutes += 24 * 60
        
        return end_minutes - start_minutes
    
    @staticmethod
    def round_to_nearest_5_minutes(minutes: int) -> int:
        """Round minutes to the nearest 5 minutes."""
        return ValidationConstants.TIME_ROUNDING_MINUTES * round(minutes / ValidationConstants.TIME_ROUNDING_MINUTES)
    
    @staticmethod
    def normalize_time_format(timepoint: datetime) -> str:
        """
        Ensure time string has valid values and 5min granularity.
        
        Args:
            timepoint: datetime object to normalize
            
        Returns:
            Normalized time string in HH:MM format
        """
        hour = timepoint.hour
        minutes = TimeUtils.round_to_nearest_5_minutes(timepoint.minute)
        
        if minutes == 60:
            hour += 1
            minutes = 0
        if hour >= 24:
            hour = 0
            
        return f"{hour:02d}:{minutes:02d}"
    
    @staticmethod
    def is_time_in_range(current_time: time, start_time_str: str, end_time_str: str) -> bool:
        """
        Check if current time falls within the given time range.
        
        Args:
            current_time: Current time object
            start_time_str: Start time string
            end_time_str: End time string
            
        Returns:
            True if current time is within range
        """
        start_time = TimeUtils.parse_time_with_validation(start_time_str)
        end_time = TimeUtils.parse_time_with_validation(end_time_str)
        
        return start_time <= current_time < end_time


# Backward compatibility functions - these delegate to TimeUtils methods

def get_current_activity(schedule: List[Dict[str, Any]], current_time: datetime) -> Optional[Dict[str, Any]]:
    """Determine the current activity based on the current time."""
    
    ''' Weekend handling
    if current_time.weekday() >= 5:
        return None
    '''
    
    time_now = current_time.time()
    for activity in schedule:
        # Use TimeUtils for consistent time parsing
        if TimeUtils.is_time_in_range(time_now, activity["start_time"], activity["end_time"]):
            return activity.copy()
    
    return None

def round_to_nearest_5_minutes(minutes: int) -> int:
    """Round minutes to the nearest 5 minutes."""
    return TimeUtils.round_to_nearest_5_minutes(minutes)


def parse_time_str(tstr: str) -> time:
    """Parse time string and return time object. Delegates to TimeUtils for consistency."""
    return TimeUtils.parse_time_with_validation(tstr)
