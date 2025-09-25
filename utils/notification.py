from typing import Dict
import requests
from utils.logging import log_info, log_error, log_debug

gotify_token = None  # Replace with your Gotify token
gotify_url = None  # Replace with your Gotify server URL

def format_gotify_message(activity: Dict) -> str:
    """Format a message for Gotify notification."""
    return "\n".join(f"{i}. {point}" for i, point in enumerate(activity['description'], 1))

def send_gotify_notification(activity: Dict, is_delayed: bool = False) -> None:
    """Send a notification to Gotify."""

    if not gotify_url:
        log_error("Can't send Gotify notification - URL is not known.")
        return

    message = format_gotify_message(activity)
    payload = {
        "title": f"{'Starting: ' if not is_delayed else ''}{activity['name']}",
        "message": message or "No description provided"
    }
    
    headers = {
        "X-Gotify-Key": gotify_token,
        "Content-Type": "application/json"
    }

    log_debug(f"Sending notification: {payload} to {gotify_url}")
    response = requests.post(gotify_url, json=payload, headers=headers)

    if response.status_code != 200:
        log_error(f"Failed to send notification: {response.status_code} - {response.text}")
    else:
        log_info("Notification sent successfully.")
