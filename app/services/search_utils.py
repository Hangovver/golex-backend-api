
def _lev(a: str, b: str) -> int:
    a = a.lower(); b = b.lower()
    if a == b: return 0
    la, lb = len(a), len(b)
    if la == 0: return lb
    if lb == 0: return la
    dp = list(range(lb+1))
    for i in range(1, la+1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, lb+1):
            cur = dp[j]
            cost = 0 if a[i-1]==b[j-1] else 1
            dp[j] = min(dp[j]+1, dp[j-1]+1, prev+cost)
            prev = cur
    return dp[lb]

def score(q: str, s: str) -> float:
    if not s: return 0.0
    ql = q.lower().strip()
    sl = s.lower().strip()
    if ql in sl:
        return 1.0 - (len(sl) - len(ql)) * 0.001
    d = _lev(ql, sl)
    m = max(len(ql), len(sl), 1)
    return max(0.0, 1.0 - d / m)

def filter_rank(q: str, items: list[dict], key: str, min_score: float = 0.55) -> list[dict]:
    scored = []
    for it in items:
        s = str(it.get(key,""))
        sc = score(q, s)
        if sc >= min_score:
            it2 = dict(it); it2["_score"] = round(sc, 4)
            scored.append(it2)
    scored.sort(key=lambda x: x["_score"], reverse=True)
    return scored
