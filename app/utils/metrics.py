import math
from typing import List, Dict

def brier_score(probs: List[float], labels: List[int]) -> float:
    n = max(1, len(probs))
    return sum([(p - y)**2 for p,y in zip(probs, labels)]) / n

def log_loss(probs: List[float], labels: List[int], eps: float = 1e-12) -> float:
    n = max(1, len(probs))
    s = 0.0
    for p,y in zip(probs, labels):
        p = min(1.0, max(0.0, p))
        if y == 1:
            s += -math.log(max(p, eps))
        else:
            s += -math.log(max(1.0 - p, eps))
    return s / n

def ece(probs: List[float], labels: List[int], bins: int = 10) -> Dict:
    if not probs:
        return {"ece": 0.0, "bins": []}
    step = 1.0 / bins
    edges = [i*step for i in range(bins+1)]
    table = []
    ece_sum = 0.0
    n = len(probs)
    for i in range(bins):
        lo, hi = edges[i], edges[i+1]
        idx = [j for j,p in enumerate(probs) if (p >= lo and (p < hi if i < bins-1 else p <= hi))]
        if not idx:
            table.append({"bin":[lo,hi], "n":0, "conf":None, "acc":None, "gap":None})
            continue
        conf = sum([probs[j] for j in idx]) / len(idx)
        acc = sum([labels[j] for j in idx]) / len(idx)
        gap = abs(acc - conf)
        w = len(idx) / n
        ece_sum += w * gap
        table.append({"bin":[lo,hi], "n":len(idx), "conf":round(conf,3), "acc":round(acc,3), "gap":round(gap,3)})
    return {"ece": round(ece_sum,4), "bins": table}
