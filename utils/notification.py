from typing import Dict
import requests

gotify_token = None  # Replace with your Gotify token
gotify_url = None  # Replace with your Gotify server URL

def format_gotify_message(activity: Dict) -> str:
    """Format a message for Gotify notification."""
    return "\n".join(f"{i}. {point}" for i, point in enumerate(activity['description'], 1))

def send_gotify_notification(activity: Dict) -> None:
    """Send a notification to Gotify."""

    message = format_gotify_message(activity)
    payload = {
        "title": f"Starting: {activity['name']}",
        "message": message
    }
    
    headers = {
        "X-Gotify-Key": gotify_token,
        "Content-Type": "application/json"
    }

    response = requests.post(gotify_url, json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Failed to send notification: {response.status_code} - {response.text}")
    else:
        print("Notification sent successfully.")
