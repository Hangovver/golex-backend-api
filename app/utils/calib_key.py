import re
def map_calibration_key(mkt_key: str) -> str | None:
    # 1X2
    m = re.match(r"mkt\.1x2\.(H|D|A)$", mkt_key)
    if m: return f"1x2.{m.group(1)}"
    # totals
    m = re.match(r"mkt\.tg\.(over|under)\.(\d_\d)$", mkt_key)
    if m: return f"{m.group(1)}{m.group(2)}"
    # team totals
    m = re.match(r"mkt\.tt\.(home|away)\.(over|under)\.(\d_\d)$", mkt_key)
    if m: return f"tt.{m.group(1)}.{m.group(2)}{m.group(3)}"
    # btts
    if mkt_key == "mkt.btts.yes": return "btts"
    if mkt_key == "mkt.btts.no": return "btts.no"
    # asian handicap
    m = re.match(r"mkt\.ah\.(home|away)\.([\-\+]\d_\d)$", mkt_key)
    if m: return f"ah.{m.group(1)}.{m.group(2)}"
    # corners/cards
    m = re.match(r"mkt\.(corners|cards)\.tg\.(over|under)\.(\d_\d)$", mkt_key)
    if m: return f"{m.group(1)}.{m.group(2)}{m.group(3)}"
    return None
