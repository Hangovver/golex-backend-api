import math
from typing import Dict, Optional

# Helper: total-goal distribution from scoreDist dict { "a-b": p }
def _totals_from_score(score_dist: Dict[str,float]) -> Dict[int,float]:
    totals = {}
    ssum = sum(score_dist.values()) or 1.0
    for k, p in score_dist.items():
        try:
            a,b = k.split("-"); t = int(a) + int(b)
            totals[t] = totals.get(t, 0.0) + p
        except:
            continue
    # normalize
    s = sum(totals.values()) or 1.0
    for k in list(totals.keys()):
        totals[k] = totals[k]/s
    return totals

def _cdf_from_pmf(pmf: Dict[int,float]):
    # returns cumulative <= x
    keys = sorted(pmf.keys())
    cum = {}; acc = 0.0
    for k in keys:
        acc += pmf[k]
        cum[k] = acc
    return keys, cum

def _prob_over_under(thresh: float, totals: Dict[int,float]) -> (float,float):
    # Over/Under on .5/.0 lines; simple: over = P(total > thresh), under = 1-over
    over = sum(p for t,p in totals.items() if t > thresh)
    under = 1.0 - over
    return max(0,min(1,over)), max(0,min(1,under))

def _prob_team_total(team: str, score_dist: Dict[str,float], thresh: float, over=True) -> float:
    s = 0.0
    for k,p in score_dist.items():
        try:
            a,b = k.split("-"); a=int(a); b=int(b)
            val = a if team=='home' else b
            ok = (val > thresh) if over else (val < thresh) if (thresh%1!=0) else (val <= thresh)  # rough
            # use strict > for .5 thresholds; <= for under equivalent
            if over and val > thresh: s += p
            if not over and val <= thresh: s += p
        except:
            continue
    return max(0.0, min(1.0, s))

def _double_chance(ph, pd, pa):
    return {
        "mkt.double.1X": max(0.0, min(1.0, ph+pd)),
        "mkt.double.12": max(0.0, min(1.0, ph+pa)),
        "mkt.double.X2": max(0.0, min(1.0, pd+pa)),
    }

def _dnb(ph, pa):
    return {"mkt.dnb.H": max(0.0, min(1.0, ph)), "mkt.dnb.A": max(0.0, min(1.0, pa))}

def _btts(score_dist: Dict[str,float]) -> float:
    s = 0.0
    for k,p in score_dist.items():
        try:
            a,b = k.split("-"); a=int(a); b=int(b)
            if a>=1 and b>=1: s += p
        except:
            continue
    return max(0.0, min(1.0, s))

def _cs_topk(score_dist: Dict[str,float], k:int=5):
    pairs = sorted(score_dist.items(), key=lambda x: x[1], reverse=True)[:k]
    return {a: round(b,3) for a,b in pairs}

def derive_all(out: Dict, features: Optional[Dict]=None, include: str="all") -> Dict[str,float|dict]:
    # out: { "1x2": {"H":..,"D":..,"A":..}, "over25": .., "btts": .., "scoreDist": {...} }
    probs = {}
    one = out.get("1x2", {}); ph=float(one.get("H",0)); pd=float(one.get("D",0)); pa=float(one.get("A",0))
    probs["mkt.1x2.H"] = round(ph,3); probs["mkt.1x2.D"] = round(pd,3); probs["mkt.1x2.A"] = round(pa,3)

    sd = out.get("scoreDist", {}) or {"0-0":0.1,"1-0":0.18,"1-1":0.2,"0-1":0.17,"2-1":0.12,"1-2":0.11}
    totals = _totals_from_score(sd)

    # Totals Over/Under common lines
    for line in [0.5,1.5,2.5,3.5,4.5]:
        ov,un = _prob_over_under(line, totals)
        keyO = f"mkt.tg.over.{str(line).replace('.','_')}"
        keyU = f"mkt.tg.under.{str(line).replace('.','_')}"
        probs[keyO] = round(ov,3); probs[keyU] = round(un,3)

    # Team totals
    for team in ["home","away"]:
        for line in [0.5,1.5,2.5]:
            p_over = _prob_team_total(team, sd, line, over=True)
            p_under = 1.0 - p_over
            probs[f"mkt.tt.{team}.over.{str(line).replace('.','_')}"] = round(p_over,3)
            probs[f"mkt.tt.{team}.under.{str(line).replace('.','_')}"] = round(p_under,3)
        # team scores any
        probs[f"mkt.team.{team}.scorers.any"] = round(_prob_team_total(team, sd, 0.5, over=True),3)

    # BTTS
    probs["mkt.btts.yes"] = round(_btts(sd),3)
    probs["mkt.btts.no"]  = round(1.0 - probs["mkt.btts.yes"],3)

    # Double chance & DNB
    probs.update(_double_chance(ph,pd,pa))
    probs.update(_dnb(ph,pa))

    # Correct score Top-K
    probs["mkt.cs.topk"] = _cs_topk(sd, k=5)

    # Asian Handicap rough mapping (using 1X2)
    probs["mkt.ah.home.-0_5"] = round(ph + 0.25*pd, 3)
    probs["mkt.ah.away.+0_5"] = round(pa + 0.25*pd, 3)

    # HT 1X2 approximations
    probs["mkt.ht.1x2.H"] = round(min(0.95, max(0.05, 0.6*ph + 0.2*pd)),3)
    probs["mkt.ht.1x2.D"] = round(min(0.95, max(0.05, 0.6*pd + 0.2*(ph+pa))),3)
    probs["mkt.ht.1x2.A"] = round(min(0.95, max(0.05, 0.6*pa + 0.2*pd)),3)
    probs["mkt.ht.tg.over.0_5"] = round(min(0.95, max(0.05, probs["mkt.tg.over.2_5"] - 0.15)),3)
    probs["mkt.ht.tg.under.0_5"] = round(1.0 - probs["mkt.ht.tg.over.0_5"],3)

    # Corners/Cards heuristics if features provided
    if features:
        elo_h = float(features.get("elo_home",1500)); elo_a=float(features.get("elo_away",1500))
        atk = max(0.0, (elo_h-elo_a)/300.0)
        # Corners total over 9.5 baseline ~0.4 +/- atk
        p_corners_95 = min(0.9, max(0.1, 0.4 + 0.2*abs(atk)))
        probs["mkt.corners.tg.over.9_5"] = round(p_corners_95,3)
        probs["mkt.corners.tg.under.9_5"] = round(1.0 - p_corners_95,3)
        # Cards total over 4.5 baseline ~0.35
        p_cards_45 = min(0.9, max(0.1, 0.35 + 0.1))
        probs["mkt.cards.tg.over.4_5"] = round(p_cards_45,3)
        probs["mkt.cards.tg.under.4_5"] = round(1.0 - p_cards_45,3)

    return probs
