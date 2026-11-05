"""The list of held containers."""
from shipments import EVENTS, latest


def held():
    containers = {e["container"] for e in EVENTS}
    return sorted(c for c in containers if latest(c)["status"] == "held")
