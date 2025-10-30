# Baseline Poisson / Dixon-Coles inspired placeholder (NOT full impl)
def predict(features: dict) -> dict:
    # Use a couple of features to produce deterministic probabilities
    h = features.get("elo_home", 1500) - 1500
    a = features.get("elo_away", 1500) - 1500
    adv = (h - a) / 100.0
    import math
    def _softmax3(x,y,z):
        m=max(x,y,z); ex=[math.exp(x-m),math.exp(y-m),math.exp(z-m)]; s=sum(ex); return [e/s for e in ex]
    ph, pd, pa = _softmax3(0.6+adv, 0.2, 0.6-adv)
    over25 = min(0.95, 0.45 + abs(adv)*0.2 + 0.15)
    btts = min(0.95, 0.4 + (1-abs(adv))*0.2)
    return {
        "1x2": {"H": round(ph,3), "D": round(pd,3), "A": round(pa,3)},
        "over25": round(over25,3),
        "btts": round(btts,3),
        "scoreDist": {"0-0":0.1,"1-0":0.18,"1-1":0.2,"0-1":0.17,"2-1":0.12,"1-2":0.11}  # toy
    }
