
from collections import deque
import threading, time, statistics, os

class MetricRing:
    def __init__(self, maxlen=1000):
        self.buf = deque(maxlen=maxlen)
        self.lock = threading.Lock()
    def add(self, v: float):
        with self.lock:
            self.buf.append((time.time(), float(v)))
    def values(self):
        with self.lock:
            return [v for ts,v in list(self.buf)]

class SloStore:
    def __init__(self):
        self.http_p95 = MetricRing(2000)
        self.ece = MetricRing(500)
        self.live_delay = MetricRing(1000)
        self.thresholds = {
            "http_p95_ms": float(os.getenv("SLO_P95_MS","500")),
            "ece": float(os.getenv("SLO_ECE","0.06")),
            "live_delay_sec": float(os.getenv("SLO_LIVE_DELAY","15")),
        }
    def ingest(self, metric: str, value: float):
        m = metric.lower()
        if m in ("p95","http_p95","http_p95_ms"): self.http_p95.add(value)
        elif m in ("ece","ece_error","calibration"): self.ece.add(value)
        elif m in ("live_delay","live_delay_sec"): self.live_delay.add(value)
    def check(self):
        def p95(vals):
            if not vals: return 0.0
            xs = sorted(vals)
            k = int(0.95*(len(xs)-1))
            return xs[k]
        s = {
            "http_p95_ms": p95(self.http_p95.values()),
            "ece": (self.ece.values()[-1] if self.ece.values() else 0.0),
            "live_delay_sec": (self.live_delay.values()[-1] if self.live_delay.values() else 0.0),
            "thresholds": self.thresholds,
        }
        s["ok"] = (s["http_p95_ms"] <= self.thresholds["http_p95_ms"]) and (s["ece"] <= self.thresholds["ece"]) and (s["live_delay_sec"] <= self.thresholds["live_delay_sec"])
        return s

STORE = SloStore()
