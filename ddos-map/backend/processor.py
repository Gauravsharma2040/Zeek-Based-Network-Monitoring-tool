import logging

from detector import usage_detector
from geoip import enrich
from metrics import stream_metrics
from parser import parse_batch
from state import ingest_queue
from ui import broadcast
from usage_model import usage_model

logger = logging.getLogger(__name__)


async def processor_loop():
    while True:
        raw = await ingest_queue.get()
        try:
            for event in parse_batch(raw):
                enrich(event)
                usage_detector.classify(event)
                # Do not train the normal-usage baseline with an obvious rate
                # burst; that would normalize the very behavior we want to flag.
                usage_model.score(event, train=event["label"] != "ddos")
                if event["ml_anomaly"]:
                    event["anomaly"] = True
                    reason = "usage_baseline_deviation"
                    event["reason"] = f"{event['reason']}+{reason}" if event["reason"] else reason
                await stream_metrics.update(event)
                await broadcast(event)
        except Exception:
            logger.exception("Unable to process an event batch")
        finally:
            ingest_queue.task_done()
