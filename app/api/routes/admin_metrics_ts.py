# Timeseries metrics for model monitoring (ECE/accuracy) grouped daily
from fastapi import APIRouter, HTTPException, Query
from ..deps import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/admin/metrics/ts", tags=["admin.metrics.ts"])

def _floor_day(dt):
    return datetime(dt.year, dt.month, dt.day, tzinfo=timezone.utc)

@router.get("/ece")
async def ece_timeseries(key: str = Query(..., description="calibration key e.g., 1x2.H, over2_5"),
                         days: int = 30, bins: int = 10):
    """Returns daily ECE for given calibration key using prediction_logs payload and fixtures final result if applicable."""
    db = SessionLocal()
    try:
        since = datetime.now(timezone.utc) - timedelta(days=int(days))
        rows = db.execute(text("""
            SELECT pl.created_at, pl.payload, f.status, f.goals_home, f.goals_away
            FROM prediction_logs pl
            LEFT JOIN fixtures f ON f.id = pl.fixture_id
            WHERE pl.created_at >= :since
        """), {"since": since}).fetchall()

        def map_to_mkt_keys(cal_key: str):
            if cal_key.startswith("1x2."):
                side = cal_key.split(".")[1]
                return [f"mkt.1x2.{side}"]
            if cal_key.startswith("over") or cal_key.startswith("under"):
                return [f"mkt.tg.{cal_key.replace('.', '_')}"]
            if cal_key.startswith("tt."):
                _, team, rest = cal_key.split(".", 2)
                typ = "over" if "over" in rest else "under"
                num = rest.replace("over","").replace("under","").replace(".", "_")
                return [f"mkt.tt.{team}.{typ}.{num}"]
            if cal_key.startswith("ah."):
                _, side, num = cal_key.split(".", 2)
                num = num.replace(".", "_")
                return [f"mkt.ah.{side}.{num}"]
            if cal_key.startswith("btts"):
                return ["mkt.btts.yes"] if cal_key == "btts" else ["mkt.btts.no"]
            if cal_key.startswith("corners.") or cal_key.startswith("cards."):
                cat, rest = cal_key.split(".", 1)
                typ = "over" if "over" in rest else "under"
                num = rest.replace("over","").replace("under","")
                if num.startswith("."): num = num[1:]
                return [f"mkt.{cat}.tg.{typ}.{num}"]
            return []

        mkt_keys = map_to_mkt_keys(key)
        if not mkt_keys:
            return {"series": []}

        daily = {}

        def outcome_ok(frow):
            if frow is None:
                return None
            gh, ga = frow
            if gh is None or ga is None:
                return None
            if key.startswith("1x2."):
                side = key.split(".")[1]
                if side == "H": return 1 if gh > ga else 0
                if side == "D": return 1 if gh == ga else 0
                if side == "A": return 1 if gh < ga else 0
            if key == "btts":
                return 1 if (gh>=1 and ga>=1) else 0
            if key == "btts.no":
                return 1 if not (gh>=1 and ga>=1) else 0
            if key.startswith("over") or key.startswith("under"):
                tot = gh + ga
                try:
                    thr = float(key.split("over")[1].replace("_",".")) if key.startswith("over") else float(key.split("under")[1].replace("_","."))
                except Exception:
                    thr = 2.5
                if key.startswith("over"): return 1 if tot > thr else 0
                else: return 1 if tot < thr else 0
            if key.startswith("tt."):
                parts = key.split(".")
                team = parts[1]; rest = parts[2]
                over = rest.startswith("over")
                thr = float(rest.replace("over","").replace("under","").replace("_","."))
                val = gh if team=="home" else ga
                return 1 if (val > thr if over else val < thr) else 0
            return None

        for created_at, payload, f_status, gh, ga in rows:
            if not isinstance(payload, dict):
                continue
            probs = (payload or {}).get("probabilities", {})
            p = None
            for mk in mkt_keys:
                if mk in probs and not isinstance(probs[mk], dict):
                    p = float(probs[mk]); break
            if p is None:
                continue
            y = outcome_ok((gh, ga))
            if y is None:
                continue
            day = _floor_day(created_at)
            daily.setdefault(day, []).append((p, y))

        def ece(items, bins):
            if not items: return None
            bs = [0.0]*bins; cs = [0.0]*bins; ns = [0]*bins
            for p,y in items:
                b = min(bins-1, max(0, int(p * bins)))
                ns[b] += 1; cs[b] += y; bs[b] += p
            tot = sum(ns) or 1
            err = 0.0
            for i in range(bins):
                if ns[i]==0: continue
                avg_p = bs[i]/ns[i]; freq = cs[i]/ns[i]
                err += (ns[i]/tot) * abs(freq-avg_p)
            return round(float(err), 4)

        series = []
        for day, items in sorted(daily.items(), key=lambda x: x[0]):
            v = ece(items, bins)
            if v is not None:
                series.append({"t": day.isoformat(), "ece": v, "n": len(items)})
        return {"key": key, "bins": bins, "series": series}
    finally:
        db.close()

@router.get("/accuracy")
async def accuracy_timeseries(market: str = Query("1x2"),
                              days: int = 30):
    """Accuracy for 1x2 by top-prediction vs actual result, daily."""
    if market != "1x2":
        raise HTTPException(status_code=400, detail="Only 1x2 supported for accuracy in MVP")
    db = SessionLocal()
    try:
        since = datetime.now(timezone.utc) - timedelta(days=int(days))
        rows = db.execute(text("""
            SELECT pl.created_at, pl.payload, f.goals_home, f.goals_away
            FROM prediction_logs pl
            LEFT JOIN fixtures f ON f.id = pl.fixture_id
            WHERE pl.created_at >= :since
        """), {"since": since}).fetchall()

        daily = {}
        for created_at, payload, gh, ga in rows:
            if not isinstance(payload, dict):
                continue
            probs = (payload or {}).get("probabilities", {})
            h = float(probs.get("mkt.1x2.H", 0))
            d = float(probs.get("mkt.1x2.D", 0))
            a = float(probs.get("mkt.1x2.A", 0))
            if gh is None or ga is None:
                continue
            actual = "H" if gh>ga else "D" if gh==ga else "A"
            top = "H"
            if d>=h and d>=a: top="D"
            elif a>=h and a>=d: top="A"
            acc = 1 if top==actual else 0
            day = _floor_day(created_at)
            daily.setdefault(day, []).append(acc)
        series = []
        for day, items in sorted(daily.items(), key=lambda x: x[0]):
            if items:
                series.append({"t": day.isoformat(), "acc": round(sum(items)/len(items), 4), "n": len(items)})
        return {"market": market, "series": series}
    finally:
        db.close()
