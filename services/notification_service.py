"""
Notification service for handling notification-related business operations.
Separates notification logic from UI and other concerns.
"""

from datetime import datetime
from typing import Dict, Optional, Callable
from models.schedule import ScheduledActivity
from utils.logging import log_debug, log_info
import utils.notification
import utils.config
from constants import NotificationConstants


class NotificationService:
    """Service for managing notifications and alerts."""
    
    def __init__(self, now_provider: Optional[Callable[[], datetime]] = None, on_activity_change: Optional[Callable] = None):
        """
        Initialize NotificationService.
        
        Args:
            now_provider: Function that returns current datetime
            on_activity_change: Callback function to call when activity changes
        """
        self.now_provider = now_provider or datetime.now
        self._notified_tasks: Dict[str, bool] = {}
        self._last_activity: Optional[ScheduledActivity] = None
        self.on_activity_change = on_activity_change
    
    def check_and_send_notifications(self, 
                                   current_activity: Optional[ScheduledActivity],
                                   next_activity: Optional[ScheduledActivity],
                                   next_activity_start: Optional[datetime]) -> None:
        """
        Check for and send appropriate notifications.
        
        Args:
            current_activity: Currently active activity
            next_activity: Next scheduled activity
            next_activity_start: Start time of next activity
        """
        if not utils.config.allow_notification:
            return
        
        now = self.now_provider()
        
        # Send advance notification for next task
        self._check_advance_notification(next_activity, next_activity_start, now)
        
        # Send notification for activity changes
        self._check_activity_change_notification(current_activity)
    
    def _check_advance_notification(self, 
                                  next_activity: Optional[ScheduledActivity],
                                  next_activity_start: Optional[datetime],
                                  now: datetime) -> None:
        """Check and send advance notification for upcoming task."""
        if not next_activity or not next_activity_start:
            # Clear any existing notification state
            if hasattr(self, '_notified_next_task'):
                delattr(self, '_notified_next_task')
            return
        
        time_until_start = (next_activity_start - now).total_seconds()
        
        # Send notification if within advance warning time
        if 0 <= time_until_start <= NotificationConstants.ADVANCE_WARNING_SECONDS:
            if not hasattr(self, '_notified_next_task') or self._notified_next_task != next_activity.name:
                self._send_advance_notification(next_activity)
                self._notified_next_task = next_activity.name
        
        # Clear notification state if outside warning window
        elif (hasattr(self, '_notified_next_task') and 
              (time_until_start > NotificationConstants.ADVANCE_WARNING_SECONDS or time_until_start < 0)):
            delattr(self, '_notified_next_task')
    
    def _check_activity_change_notification(self, current_activity: Optional[ScheduledActivity]) -> None:
        """Check and send notification for activity changes."""
        # Send notification if activity changed
        if current_activity and (
            self._last_activity is None or 
            self._last_activity.name != current_activity.name
        ):
            if self.on_activity_change:
                self.on_activity_change()
            self._send_activity_start_notification(current_activity)
            log_debug(f"Notification sent for activity: {current_activity.name}")
        
        self._last_activity = current_activity
    
    def _send_advance_notification(self, activity: ScheduledActivity) -> None:
        """Send advance notification for upcoming activity."""
        notification_data = {
            'name': f"{NotificationConstants.ADVANCE_WARNING_SECONDS} seconds to start {activity.name}",
            'description': [f"{activity.name} starts at {activity.start_time}"]
        }
        utils.notification.send_gotify_notification(notification_data, is_delayed=True)
        log_info(f"Sent advance notification for: {activity.name}")
    
    def _send_activity_start_notification(self, activity: ScheduledActivity) -> None:
        """Send notification for activity start."""
        notification_data = activity.to_dict()
        utils.notification.send_gotify_notification(notification_data)
        log_info(f"Sent start notification for: {activity.name}")
    
    def send_custom_notification(self, title: str, message: str, is_delayed: bool = False) -> None:
        """
        Send a custom notification.
        
        Args:
            title: Notification title
            message: Notification message
            is_delayed: Whether this is a delayed notification
        """
        if not utils.config.allow_notification:
            return
        
        notification_data = {
            'name': title,
            'description': [message]
        }
        utils.notification.send_gotify_notification(notification_data, is_delayed=is_delayed)
        log_info(f"Sent custom notification: {title}")
    
    def reset_notification_state(self) -> None:
        """Reset all notification state."""
        self._notified_tasks.clear()
        self._last_activity = None
        if hasattr(self, '_notified_next_task'):
            delattr(self, '_notified_next_task')
        log_debug("Reset notification state")
    
    def is_notifications_enabled(self) -> bool:
        """Check if notifications are currently enabled."""
        return utils.config.allow_notification
    
    def set_notifications_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications."""
        utils.config.allow_notification = enabled
        if not enabled:
            self.reset_notification_state()
        log_info(f"Notifications {'enabled' if enabled else 'disabled'}")
