from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from time import time

REGISTRY = CollectorRegistry()

REQ_LATENCY = Histogram('golex_request_latency_seconds', 'HTTP request latency', ['path'], registry=REGISTRY, buckets=(0.05,0.1,0.2,0.5,1,2,5))
REQ_COUNT   = Counter('golex_request_total', 'HTTP request count', ['path','code'], registry=REGISTRY)

PRED_LATENCY = Histogram('golex_prediction_latency_seconds', 'Prediction handler latency', registry=REGISTRY, buckets=(0.01,0.05,0.1,0.2,0.5,1,2))
PRED_ECE     = Gauge('golex_prediction_macro_ece', 'Macro ECE from calibration window', registry=REGISTRY)

def track_request(path: str):
    start = time()
    def done(status_code: int):
        dur = time() - start
        try:
            REQ_LATENCY.labels(path).observe(dur)
            REQ_COUNT.labels(path, str(status_code)).inc()
        except Exception:
            pass
    return done

def set_macro_ece(val: float):
    try:
        PRED_ECE.set(val)
    except Exception:
        pass

def metrics_response():
    data = generate_latest(REGISTRY)
    return CONTENT_TYPE_LATEST, data


LIVE_DELAY = Gauge('golex_live_delay_seconds', 'Estimated live update delay seconds', registry=REGISTRY)

def set_live_delay(val: float):
    try:
        LIVE_DELAY.set(val)
    except Exception:
        pass
