"""A dependency-free online baseline for unusual network behaviour.

This is intentionally transparent: it labels volume bursts as possible DDoS and
flags previously unseen source/port combinations after a short warm-up period.
It is a starting point, not a replacement for an intrusion-detection model.
"""
import time
from collections import Counter, deque


class UsageDetector:
    def __init__(self, window_seconds: int = 10, ddos_threshold: int = 250, warmup_events: int = 50):
        self.window_seconds = window_seconds
        self.ddos_threshold = ddos_threshold
        self.warmup_events = warmup_events
        self.timestamps = deque()
        self.seen_pairs = Counter()
        self.events_seen = 0

    def classify(self, event: dict) -> dict:
        now = time.monotonic()
        self.timestamps.append(now)
        while self.timestamps and now - self.timestamps[0] > self.window_seconds:
            self.timestamps.popleft()
        key = (event["src"], event["port"])
        novel = self.events_seen >= self.warmup_events and self.seen_pairs[key] == 0
        self.seen_pairs[key] += 1
        self.events_seen += 1
        burst = len(self.timestamps) >= self.ddos_threshold
        event["label"] = "ddos" if burst else "normal"
        event["anomaly"] = burst or novel
        event["reason"] = "traffic_rate_burst" if burst else ("new_source_port" if novel else None)
        return event


usage_detector = UsageDetector()
