import re, hashlib
from typing import Dict

def normalize_trace(trace: str) -> str:
    # Remove memory addresses/line numbers and collapse whitespace
    t = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', trace)
    t = re.sub(r':\d+', ':LINE', t)  # line numbers
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def fingerprint(trace: str) -> str:
    norm = normalize_trace(trace)
    # Keep package/method names; drop line numbers; hash to short id
    h = hashlib.sha1(norm.encode('utf-8')).hexdigest()[:12]
    return f"fp:{h}"

def group_label(trace: str) -> Dict[str,str]:
    norm = normalize_trace(trace)
    return {"fingerprint": fingerprint(trace), "normalized": norm}
