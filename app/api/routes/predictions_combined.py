
from fastapi import APIRouter, Query, Request
from typing import List, Dict
from ...services import apifootball_adapter as AF
from ...services import prediction_utils as PU
from ...services import cache_utils as CU
import re

router = APIRouter(prefix="/predictions", tags=["predictions-combined"])

@router.get("/combined")
async def combined(
    fixtureId: str = Query(...),
    markets: str = Query("KG+O2.5,1X+O1.5+KG,X2+O1.5+KG,12+O2.5,1X+U2.5,1&NKG,TG2-4,TOT=3,TOT_ODD,H_WIN_BY1,H_WIN_BY2+,H_CS,DNB1,EH1-1:1,AH1-0.25,1H_O0.5,1H_1,1H_KG,HTFT1-1,FTS_H,C_O8.5,YC_O3.5,RC_U0.5"),
    request: Request = None
):
    fx = AF.get_fixture(fixtureId)
    # prefetch player baselines if any PL_ tokens
    pids = set()
    for t in markets.split(','):
        t=t.strip()
        mt = re.findall(r'PL_[A-Z_]+:([0-9]+)', t.upper())
        for pid in mt:
            pids.add(pid)
    if pids:
        fx['playerBaselines'] = {pid: AF.get_player_baseline(fixtureId, pid) for pid in pids}
    mu = fx.get("mu", {"home":1.4,"away":1.1})
    P = PU.score_matrix(mu.get("home",1.4), mu.get("away",1.1))
    out: List[Dict] = []
    for m in markets.split(","):
        m = m.strip()
        if not m: continue
        # Asian handicap special handling
        ah = re.match(r'AH(1|2)([+-]?[0-9]+(?:\.[05])?)', m.upper())
        if ah:
            side = ah.group(1); line = float(ah.group(2))
            w,p,l = PU.prob_ah(P, side, line)
            out.append({"market": m, "prob": round(w,4), "push": round(p,4)})
            continue

        r = PU.prob_combo(P, m, mu.get("home",1.4), mu.get("away",1.1), fx)
        item = {"market": m, "prob": round(r.get("prob",0.0),4)}
        if r.get("details"):
            item["details"] = r["details"]
        out.append(item)
    return CU.respond_with_etag(request, {"fixtureId": fixtureId, "markets": out})
