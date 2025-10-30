# Simple in-memory model registry (demo)
from typing import Dict
STATE: Dict[str, object] = {
    "version": "1.0.0",
    "force": False,
    "url": "/models/model-1.0.0.bin"
}
def get_version():
    return {"version": STATE["version"], "forceRefresh": STATE["force"], "url": STATE["url"]}
def set_version(v: str, url: str|None=None):
    STATE["version"] = v
    if url: STATE["url"] = url
def set_force(flag: bool):
    STATE["force"] = flag
