"""Shipment status events (ADR 0003)."""
from datetime import datetime

# Every status a container can have. "cleared" is a container customs has released.
STATUSES = ("held", "cleared")

EVENTS = []


def record_status(container: str, status: str, at: datetime) -> None:
    """Record a status change as an event; the only way a status changes.

    A status that would change nothing is not recorded: a repeated hold, or clearing a container
    that is not held.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown status: {status}")
    current = latest(container)
    if status == (current["status"] if current else "cleared"):
        return
    EVENTS.append({"container": container, "status": status, "at": at})


def latest(container: str):
    found = [e for e in EVENTS if e["container"] == container]
    return found[-1] if found else None
