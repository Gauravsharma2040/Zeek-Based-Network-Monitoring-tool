import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from usage_model import OnlineUsageModel


class OnlineUsageModelTests(unittest.TestCase):
    def test_model_warms_up_before_flagging(self):
        model = OnlineUsageModel(min_samples=3, anomaly_threshold=2.0)
        normal = {"ts": 1_700_000_000, "proto": "tcp", "port": 443, "bytes": 512}
        for _ in range(3):
            result = model.score(normal.copy())
            self.assertFalse(result["ml_anomaly"])
        self.assertTrue(model.snapshot()["ready"])

    def test_model_flags_a_large_deviation_after_warmup(self):
        model = OnlineUsageModel(min_samples=3, anomaly_threshold=2.0)
        normal = {"ts": 1_700_000_000, "proto": "tcp", "port": 443, "bytes": 512}
        for _ in range(3):
            model.score(normal.copy())
        result = model.score({"ts": 1_700_043_200, "proto": "icmp", "port": 1, "bytes": 100_000_000}, train=False)
        self.assertTrue(result["ml_anomaly"])
        self.assertGreaterEqual(result["ml_score"], 2.0)


if __name__ == "__main__":
    unittest.main()
