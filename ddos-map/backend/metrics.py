import time
from collections import deque

class StreamMetrics:
    def __init__(self, window_seconds=10):
        self.total_events = 0
        self.ddos_events = 0
        self.normal_events = 0
        self.window_seconds = window_seconds
        self.timestamps = deque()

    def update(self, event):
        now = time.time()

        self.total_events += 1
        self.timestamps.append(now)

        if event["label"] == "ddos":
            self.ddos_events += 1
        else:
            self.normal_events += 1

        # Remove old timestamps
        while self.timestamps and now - self.timestamps[0] > self.window_seconds:
            self.timestamps.popleft()

    def events_per_second(self):
        if not self.timestamps:
            return 0.0
        return len(self.timestamps) / self.window_seconds

    def snapshot(self):
        return {
            "total_events": self.total_events,
            "ddos_events": self.ddos_events,
            "normal_events": self.normal_events,
            "events_per_second": round(self.events_per_second(), 2),
        }
