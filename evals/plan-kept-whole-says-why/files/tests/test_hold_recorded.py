"""Requirement: Hold recorded. Fed a broker message recorded in tests/messages/."""
import json
from pathlib import Path

import shipments
from broker.updates import handle
from holds.list import held
from page import summary

MESSAGES = Path(__file__).parent / "messages"


def setup_function():
    shipments.EVENTS.clear()


def test_hold_reported():
    handle(json.loads((MESSAGES / "hold.json").read_text()))
    assert held() == ["MSCU1234567"]
    assert summary("MSCU1234567") == "held since 2027-02-12 09:12"
