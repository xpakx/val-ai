from datetime import datetime


def current_time() -> str:
    """
    current time
    """
    now = datetime.now()
    return now.strftime("%B %d, %Y, %I:%M %p")
