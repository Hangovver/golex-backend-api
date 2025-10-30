from time import time
from collections import defaultdict

WINDOW=60; LIMIT=300
hits = defaultdict(list)

def allow(ip: str) -> bool:
    now = time()
    lst = hits[ip]
    while lst and now - lst[0] > WINDOW:
        lst.pop(0)
    if len(lst) >= LIMIT: return False
    lst.append(now); return True
