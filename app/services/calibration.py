from typing import List, Dict, Tuple
import math
from .metrics import set_gauge

LOG: List[Dict] = []  # items: { "p": float, "y": int, "modelVersion": str }

def log(p: float, y: int, modelVersion: str):
    LOG.append({"p": float(p), "y": int(y), "modelVersion": modelVersion})

def summary(bins: int = 10, modelVersion: str | None = None):
    data = [r for r in LOG if (modelVersion is None or r["modelVersion"] == modelVersion)]
    if not data: return {"bins":[], "ece": None, "n": 0}
    buckets = [ {"lo":i/bins, "hi":(i+1)/bins, "n":0, "p_avg":0.0, "acc":0.0} for i in range(bins) ]
    for r in data:
        idx = min(int(r["p"] * bins), bins-1)
        b = buckets[idx]; b["n"] += 1; b["p_avg"] += r["p"]; b["acc"] += r["y"]
    ece = 0.0; N = len(data)
    for b in buckets:
        if b["n"]>0:
            b["p_avg"] /= b["n"]
            b["acc"] /= b["n"]
            ece += (b["n"]/N) * abs(b["acc"] - b["p_avg"])
    set_gauge("prediction_ece", ece, {"modelVersion": modelVersion or "ALL"})
    return {"bins": buckets, "ece": round(ece, 4), "n": N}
