"""Handle update messages from the customs broker.

The broker sends two types of message, "hold" and "released", each with the container's number
and the time, such as {"type": "released", "container": "MSCU1234567", "time": "2027-02-13T14:30"}.
"""
from datetime import datetime

from shipments import record_status


def handle(message: dict) -> None:
    at = datetime.fromisoformat(message["time"])
    if message["type"] == "hold":
        record_status(message["container"], "held", at)
    # "released" messages are ignored for now.
