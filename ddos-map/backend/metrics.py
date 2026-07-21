import time
from asyncio import Lock
from collections import Counter, deque


class StreamMetrics:
    def __init__(self, window_seconds: int = 10):
        self.lock = Lock()
        self.total_events = self.ddos_events = self.normal_events = self.anomaly_events = self.ml_anomaly_events = 0
        self.window_seconds = window_seconds
        self.timestamps = deque()
        self.protocols = Counter()

    async def update(self, event: dict):
        async with self.lock:
            now = time.monotonic()
            self.total_events += 1
            self.timestamps.append(now)
            self.protocols[event.get("proto", "unknown")] += 1
            if event.get("label") == "ddos":
                self.ddos_events += 1
            else:
                self.normal_events += 1
            self.anomaly_events += int(bool(event.get("anomaly")))
            self.ml_anomaly_events += int(bool(event.get("ml_anomaly")))
            while self.timestamps and now - self.timestamps[0] > self.window_seconds:
                self.timestamps.popleft()

    async def snapshot(self):
        async with self.lock:
            return {
                "total_events": self.total_events,
                "ddos_events": self.ddos_events,
                "normal_events": self.normal_events,
                "anomaly_events": self.anomaly_events,
                "ml_anomaly_events": self.ml_anomaly_events,
                "events_per_second": round(len(self.timestamps) / self.window_seconds, 2),
                "protocols": dict(self.protocols),
            }


stream_metrics = StreamMetrics()
