"""A container's page."""
from shipments import latest


def summary(container: str) -> str:
    event = latest(container)
    if event and event["status"] == "held":
        return f"held since {event['at']:%Y-%m-%d %H:%M}"
    return "not held"
