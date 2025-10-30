from typing import Dict, Tuple
from collections import defaultdict

_counters: Dict[Tuple[str, Tuple[Tuple[str,str],...]], int] = defaultdict(int)
_gauges: Dict[Tuple[str, Tuple[Tuple[str,str],...]], float] = defaultdict(float)

def inc(name: str, labels: Dict[str,str] | None = None, value: int = 1):
    key = (name, tuple(sorted((labels or {}).items())))
    _counters[key] += value

def set_gauge(name: str, value: float, labels: Dict[str,str] | None = None):
    key = (name, tuple(sorted((labels or {}).items())))
    _gauges[key] = value

def render_prom() -> str:
    def fmt_labels(lbls):
        if not lbls: return ""
        return "{" + ",".join([f"{k}=\"{v}\"" for k,v in lbls]) + "}"
    lines = []
    for (name, lbls), v in sorted(_counters.items()):
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name}{fmt_labels(lbls)} {v}")
    for (name, lbls), v in sorted(_gauges.items()):
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name}{fmt_labels(lbls)} {v}")
    return "\n".join(lines) + "\n"
