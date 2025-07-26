"""
Time management model for handling time-related operations.
Encapsulates time simulation and provider functionality.
"""

from datetime import datetime, timedelta
from typing import Callable, Optional
from constants import AppConstants, ValidationConstants


class TimeManager:
    """Manages time operations including simulation and time providers."""
    
    def __init__(self, 
                 timelapse_speed: float = AppConstants.DEFAULT_TIMELAPSE_SPEED,
                 start_time: Optional[datetime] = None):
        """
        Initialize TimeManager.
        
        Args:
            timelapse_speed: Speed multiplier for time simulation
            start_time: Starting time for simulation (defaults to current time)
        """
        self._validate_timelapse_speed(timelapse_speed)
        
        self.timelapse_speed = timelapse_speed
        self.start_real_time: Optional[datetime] = None
        self.start_sim_time: Optional[datetime] = None
        
        # Initialize with current time or provided time
        now = start_time or datetime.now()
        self.start_real_time = now
        self.start_sim_time = now
    
    @staticmethod
    def _validate_timelapse_speed(speed: float) -> None:
        """Validate timelapse speed is within acceptable range."""
        if not (ValidationConstants.MIN_TIMELAPSE_SPEED < speed <= ValidationConstants.MAX_TIMELAPSE_SPEED):
            raise ValueError(
                f"Timelapse speed must be in range "
                f"({ValidationConstants.MIN_TIMELAPSE_SPEED}, {ValidationConstants.MAX_TIMELAPSE_SPEED}], "
                f"got {speed}"
            )
    
    def set_timelapse_speed(self, speed: float) -> None:
        """Set new timelapse speed with validation."""
        self._validate_timelapse_speed(speed)
        self.timelapse_speed = speed
    
    def set_simulation_start_time(self, start_time: datetime) -> None:
        """Set the simulation start time."""
        self.start_sim_time = start_time
        # Reset real time reference
        self.start_real_time = datetime.now()
    
    def get_current_time(self) -> datetime:
        """
        Get current simulated time based on timelapse speed.
        
        Returns:
            Current simulated datetime
        """
        if self.start_real_time is None or self.start_sim_time is None:
            return datetime.now()
        
        elapsed_real = (datetime.now() - self.start_real_time).total_seconds()
        elapsed_sim = elapsed_real * self.timelapse_speed
        return self.start_sim_time + timedelta(seconds=elapsed_sim)
    
    def get_time_provider(self) -> Callable[[], datetime]:
        """
        Get a callable that returns current simulated time.
        
        Returns:
            Function that returns current datetime
        """
        return self.get_current_time
    
    def reset_to_real_time(self) -> None:
        """Reset time simulation to use real time."""
        now = datetime.now()
        self.start_real_time = now
        self.start_sim_time = now
        self.timelapse_speed = AppConstants.DEFAULT_TIMELAPSE_SPEED
    
    def is_simulation_active(self) -> bool:
        """Check if time simulation is active (speed != 1.0)."""
        return self.timelapse_speed != AppConstants.DEFAULT_TIMELAPSE_SPEED
    
    def get_simulation_info(self) -> dict:
        """Get information about current simulation state."""
        return {
            "timelapse_speed": self.timelapse_speed,
            "start_real_time": self.start_real_time,
            "start_sim_time": self.start_sim_time,
            "current_sim_time": self.get_current_time(),
            "is_simulation_active": self.is_simulation_active()
        }
