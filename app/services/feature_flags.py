from typing import Dict, Any
from .metrics import inc

STATE: Dict[str, Any] = {
    "prefetchPolicy": "gentle",   # gentle | aggressive
    "enableExplainChips": True,
    "enableRealtimeWS": False,
    "highContrastDefault": False
}

def get_all() -> Dict[str, Any]:
    inc("feature_flags_gets_total")
    return STATE

def update(patch: Dict[str, Any]) -> Dict[str, Any]:
    STATE.update(patch or {})
    inc("feature_flags_updates_total")
    return STATE
