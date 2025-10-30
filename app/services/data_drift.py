from typing import Dict, List, Tuple
from statistics import mean, pstdev
from .metrics import inc, set_gauge
from .alerts import SlackProvider

# In-memory baseline & logs (demo)
BASELINE: Dict[str, List[float]] = {}   # feature -> values (baseline window)
CURRENT: Dict[str, List[float]] = {}    # feature -> values (current window)
THRESHOLDS = {"mean_delta_pct": 0.25, "std_delta_pct": 0.35}  # demo thresholds
ALERTS: List[Dict] = []

def log_sample(vec: Dict[str, float], to_current: bool = True):
    target = CURRENT if to_current else BASELINE
    for k, v in vec.items():
        target.setdefault(k, []).append(float(v))
    inc("data_drift_samples_total")

def set_baseline(vec: Dict[str, float]):
    for k, v in vec.items():
        BASELINE.setdefault(k, []).append(float(v))
    inc("data_drift_baseline_updates_total")

def summary():
    out = []
    for feat, cur_vals in CURRENT.items():
        base_vals = BASELINE.get(feat, [])
        if not cur_vals or not base_vals:
            continue
        m0 = mean(base_vals); s0 = pstdev(base_vals) if len(base_vals)>1 else 0.0
        m1 = mean(cur_vals);  s1 = pstdev(cur_vals) if len(cur_vals)>1 else 0.0
        mean_delta = (m1 - m0)
        std_delta = (s1 - s0)
        mean_pct = abs(mean_delta) / (abs(m0)+1e-9)
        std_pct  = abs(std_delta)  / (abs(s0)+1e-9) if s0>0 else (1.0 if s1>0 else 0.0)
        drifted = (mean_pct > THRESHOLDS["mean_delta_pct"]) or (std_pct > THRESHOLDS["std_delta_pct"])
        set_gauge("data_drift_mean_pct", mean_pct, {"feature": feat})
        set_gauge("data_drift_std_pct", std_pct, {"feature": feat})
        out.append({"feature": feat, "m0": m0, "m1": m1, "mean_pct": round(mean_pct,4),
                    "s0": s0, "s1": s1, "std_pct": round(std_pct,4), "drift": drifted})
    return {"features": out, "thresholds": THRESHOLDS}

def check_and_alert():
    sm = summary()
    alerts = []
    for r in sm["features"]:
        if r["drift"]:
            msg = f"[DRIFT] {r['feature']} meanΔ%={r['mean_pct']} stdΔ%={r['std_pct']}"
            alerts.append(msg)
    if alerts:
        sp = SlackProvider("https://example.webhook")
        for a in alerts:
            sp.send(a)
            ALERTS.append({"msg": a})
        inc("data_drift_alerts_total", {"count": str(len(alerts))}, value=len(alerts))
    return {"alerts": ALERTS[-50:], "latest": alerts}
