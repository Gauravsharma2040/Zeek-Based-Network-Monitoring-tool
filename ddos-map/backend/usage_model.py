"""Small, explainable online model for network-usage anomalies.

The model learns a Gaussian baseline incrementally using Welford's algorithm.
It avoids a heavy ML runtime while allowing the receiver to score every Zeek
event immediately.  Model state is deliberately in-memory for this first
integration; persist it only after deciding how profiles should be scoped.
"""
import math
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class RunningStat:
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)

    @property
    def variance(self) -> float:
        return self.m2 / (self.count - 1) if self.count > 1 else 0.0


class OnlineUsageModel:
    """Unsupervised profile that flags events far from learned normal usage."""

    def __init__(self, min_samples: int = 100, anomaly_threshold: float = 3.5):
        self.min_samples = min_samples
        self.anomaly_threshold = anomaly_threshold
        self.samples = 0
        self.stats = [RunningStat() for _ in range(5)]

    @staticmethod
    def _features(event: dict) -> list[float]:
        timestamp = float(event.get("ts") or 0)
        # Legacy binary packets may carry a non-epoch timestamp. Keep scoring
        # robust instead of dropping an entire event batch on conversion.
        hour = datetime.fromtimestamp(timestamp, tz=UTC).hour if 946_684_800 <= timestamp <= 4_102_444_800 else 0
        angle = 2 * math.pi * hour / 24
        protocol = {"tcp": 0.0, "udp": 0.33, "icmp": 0.66}.get(event.get("proto"), 1.0)
        return [
            math.sin(angle),
            math.cos(angle),
            min(max(int(event.get("port") or 0), 0), 65535) / 65535,
            min(math.log1p(max(int(event.get("bytes") or 0), 0)) / math.log1p(1_000_000_000), 1.0),
            protocol,
        ]

    def score(self, event: dict, train: bool = True) -> dict:
        features = self._features(event)
        ready = self.samples >= self.min_samples
        z_scores = []
        if ready:
            for feature, stat in zip(features, self.stats):
                # A small floor prevents an early near-constant feature from
                # producing an unbounded score after one changed event.
                standard_deviation = max(math.sqrt(stat.variance), 0.05)
                z_scores.append((feature - stat.mean) / standard_deviation)
        score = math.sqrt(sum(score * score for score in z_scores) / len(z_scores)) if z_scores else 0.0
        event["ml_ready"] = ready
        event["ml_score"] = round(score, 3)
        event["ml_anomaly"] = ready and score >= self.anomaly_threshold
        event["ml_confidence"] = round(min(self.samples / self.min_samples, 1.0), 2)
        if train:
            for feature, stat in zip(features, self.stats):
                stat.update(feature)
            self.samples += 1
        return event

    def snapshot(self) -> dict:
        return {
            "type": "online_gaussian_baseline",
            "samples": self.samples,
            "min_samples": self.min_samples,
            "ready": self.samples >= self.min_samples,
            "anomaly_threshold": self.anomaly_threshold,
            "features": ["hour_sin", "hour_cos", "destination_port", "log_bytes", "protocol"],
        }


usage_model = OnlineUsageModel()
