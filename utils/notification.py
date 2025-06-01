from typing import Dict

GOTIFY_TOKEN = "AFugh.ZkSxFka_y"

def format_gotify_message(activity: Dict) -> str:
    """Format a message for Gotify notification."""
    return "\n".join(f"{i}. {point}" for i, point in enumerate(activity['description'], 1))
