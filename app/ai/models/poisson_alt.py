# Alternate Poisson-inspired baseline (slightly different weighting)
def predict(features: dict) -> dict:
    h = features.get("elo_home", 1500) - 1500
    a = features.get("elo_away", 1500) - 1500
    adv = (h - a) / 90.0  # more sensitive
    import math
    def _softmax3(x,y,z):
        m=max(x,y,z); ex=[math.exp(x-m),math.exp(y-m),math.exp(z-m)]; s=sum(ex); return [e/s for e in ex]
    ph, pd, pa = _softmax3(0.65+adv, 0.18, 0.65-adv)
    over25 = min(0.97, 0.44 + abs(adv)*0.25 + 0.12)
    btts = min(0.97, 0.38 + (1-abs(adv))*0.25)
    return {
        "1x2": {"H": round(ph,3), "D": round(pd,3), "A": round(pa,3)},
        "over25": round(over25,3),
        "btts": round(btts,3),
        "scoreDist": {"0-0":0.09,"1-0":0.17,"1-1":0.21,"0-1":0.16,"2-1":0.13,"1-2":0.12}
    }
