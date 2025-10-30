import re
_MAP = {
    "premier league": "Premier League",
    "super lig": "Süper Lig",
    "super league": "Super League",
    "la liga": "La Liga",
}
def normalize_league_name(name: str, lang: str = "tr") -> str:
    key = re.sub(r"\s+", " ", name or "").strip().lower()
    v = _MAP.get(key, None)
    if v: return v
    # title-case fallback; Turkish dotted-i special cases could be applied later
    return " ".join(w.capitalize() for w in key.split(" "))
