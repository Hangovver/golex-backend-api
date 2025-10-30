from typing import Dict, List
from statistics import median
from .alerts import SlackProvider
from .metrics import inc, set_gauge

THRESH = {"p95_ms": 500.0, "ece": 0.06, "live_delay_s": 15.0}
DATA = {"latencies_ms": [], "ece": [], "live_delay_s": []}
ALERT_LOG: List[Dict] = []

def ingest(latency_ms: float | None = None, ece: float | None = None, live_delay_s: float | None = None):
    if latency_ms is not None: DATA["latencies_ms"].append(float(latency_ms))
    if ece is not None: DATA["ece"].append(float(ece))
    if live_delay_s is not None: DATA["live_delay_s"].append(float(live_delay_s))
    inc("slo_ingest_total")

def set_thresholds(p95_ms: float | None = None, ece: float | None = None, live_delay_s: float | None = None):
    if p95_ms is not None: THRESH["p95_ms"] = float(p95_ms)
    if ece is not None: THRESH["ece"] = float(ece)
    if live_delay_s is not None: THRESH["live_delay_s"] = float(live_delay_s)
    return THRESH

def report():
    lat = sorted(DATA["latencies_ms"])
    p95 = lat[int(0.95*len(lat))] if lat else None
    last_ece = DATA["ece"][-1] if DATA["ece"] else None
    last_live = DATA["live_delay_s"][-1] if DATA["live_delay_s"] else None
    if p95 is not None: set_gauge("slo_p95_ms", p95)
    if last_ece is not None: set_gauge("slo_ece", last_ece)
    if last_live is not None: set_gauge("slo_live_delay_s", last_live)
    return {"p95_ms": p95, "ece": last_ece, "live_delay_s": last_live, "thresholds": THRESH}

def check_and_alert():
    rep = report()
    breaches = []
    if rep["p95_ms"] is not None and rep["p95_ms"] > THRESH["p95_ms"]:
        breaches.append(f"p95_ms {rep['p95_ms']:.1f}>{THRESH['p95_ms']:.1f}")
    if rep["ece"] is not None and rep["ece"] > THRESH["ece"]:
        breaches.append(f"ECE {rep['ece']:.3f}>{THRESH['ece']:.3f}")
    if rep["live_delay_s"] is not None and rep["live_delay_s"] > THRESH["live_delay_s"]:
        breaches.append(f"live_delay {rep['live_delay_s']:.1f}>{THRESH['live_delay_s']:.1f}")
    if breaches:
        sp = SlackProvider("https://example.webhook")
        msg = "[SLO BREACH] " + ", ".join(breaches)
        sp.send(msg)
        inc("slo_breach_total")
        ALERT_LOG.append({"msg": msg})
    return {"breaches": breaches, "alerted": bool(breaches), "log": ALERT_LOG[-50:]}
