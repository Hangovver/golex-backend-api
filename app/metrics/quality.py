from collections import defaultdict
from typing import Dict, Any
_quality: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

class Quality:
    @staticmethod
    def record(metric: str, **values: float):
        for k, v in values.items():
            _quality[metric][k] += float(v)

    @staticmethod
    def snapshot():
        return {m: dict(vals) for m, vals in _quality.items()}
