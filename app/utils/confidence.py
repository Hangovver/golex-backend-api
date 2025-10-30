from typing import Dict, Tuple

def _label(x: float) -> str:
    if x >= 0.7: return "high"
    if x >= 0.5: return "medium"
    return "low"

def compute(probabilities: Dict[str, float], calibrated_keys: set[str]) -> Tuple[float, str]:
    # Core from 1x2 distribution if present
    h = probabilities.get("mkt.1x2.H")
    d = probabilities.get("mkt.1x2.D")
    a = probabilities.get("mkt.1x2.A")
    core_conf = 0.5
    if h is not None and d is not None and a is not None:
        arr = sorted([float(h), float(d), float(a)], reverse=True)
        top, second = arr[0], arr[1]
        margin = max(0.0, top - second)  # 0..1
        core_conf = max(0.3, min(0.95, 0.5*top + 0.5*margin))

    # Calibration boost/penalty
    cal_ratio = 0.0
    if probabilities:
        cal_ratio = len(calibrated_keys) / max(1, len([k for k,v in probabilities.items() if not isinstance(v, dict)]))
    # Slightly boost if most keys calibrated, slight penalty if few
    factor = 1.0
    if cal_ratio >= 0.7: factor = 1.05
    elif cal_ratio < 0.2: factor = 0.95

    conf = max(0.3, min(0.95, core_conf * factor))
    return round(conf, 2), _label(conf)
