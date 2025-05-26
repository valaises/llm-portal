import threading
from dataclasses import dataclass


@dataclass
class Worker:
    """Structure to hold worker thread and its stop event"""
    name: str
    thread: threading.Thread
    stop_event: threading.Event
