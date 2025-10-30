
import math, re, os

def poisson_pmf(k, lam):
    return math.exp(-lam) * (lam**k) / math.factorial(k)

def score_matrix(mu_home: float, mu_away: float, max_goals: int = 10):
    P = []
    for a in range(max_goals+1):
        row = []
        for b in range(max_goals+1):
            row.append(poisson_pmf(a, mu_home)*poisson_pmf(b, mu_away))
        P.append(row)
    # normalize (safety)
    s = sum(sum(r) for r in P)
    if s>0:
        P = [[x/s for x in r] for r in P]
    return P

# Helpers
def total_prob(P, cond):
    m=len(P); n=len(P[0])
    s=0.0
    for a in range(m):
        for b in range(n):
            if cond(a,b): s += P[a][b]
    return s

def half_score_mats(mu_home: float, mu_away: float, max_goals: int = 8):
    # Assume first/second half Poisson with half rate
    lam_h = mu_home/2.0
    lam_a = mu_away/2.0
    Ph = score_matrix(lam_h, lam_a, max_goals)
    # For second half we assume same distribution
    Ps = score_matrix(lam_h, lam_a, max_goals)
    return Ph, Ps

def prob_btts(P):  # KG
    return total_prob(P, lambda a,b: a>=1 and b>=1)

def prob_nkg(P):
    return 1.0 - prob_btts(P)

def prob_over_n5(P, n):
    thr = int(n)+1
    return total_prob(P, lambda a,b: a+b >= thr)

def prob_under_n5(P, n):
    thr = int(n)
    return total_prob(P, lambda a,b: a+b <= thr)

def prob_1x2(P):
    p1 = total_prob(P, lambda a,b: a>b)
    px = total_prob(P, lambda a,b: a==b)
    p2 = 1.0 - p1 - px
    return p1, px, p2

def prob_team_over_n5(P, team: str, n: float):
    thr = int(n)+1
    if team.upper().startswith("H"):
        return total_prob(P, lambda a,b: a>=thr)
    return total_prob(P, lambda a,b: b>=thr)

def prob_team_under_n5(P, team: str, n: float):
    thr = int(n)
    if team.upper().startswith("H"):
        return total_prob(P, lambda a,b: a<=thr)
    return total_prob(P, lambda a,b: b<=thr)

def prob_correct_score(P, a:int, b:int):
    if a < len(P) and b < len(P[0]):
        return P[a][b]
    return 0.0

def prob_total_band(P, lo:int, hi:int):
    return total_prob(P, lambda a,b: lo <= (a+b) <= hi)

def prob_total_exact(P, k:int):
    return total_prob(P, lambda a,b: (a+b)==k)

def prob_total_parity(P, odd=True):
    return total_prob(P, lambda a,b: ((a+b)%2==1) if odd else ((a+b)%2==0))

def prob_margin(P, side:str, by:int, at_least:bool=False):
    if side=="H":
        return total_prob(P, lambda a,b: (a-b >= by) if at_least else (a-b==by))
    else:
        return total_prob(P, lambda a,b: (b-a >= by) if at_least else (b-a==by))

def prob_clean_sheet(P, side:str):
    if side=="H":
        return total_prob(P, lambda a,b: b==0)
    else:
        return total_prob(P, lambda a,b: a==0)

def prob_dnb(P, side:str):
    # Success probability only: push (draw) excluded
    if side=="1":
        return total_prob(P, lambda a,b: a>b)
    else:
        return total_prob(P, lambda a,b: b>a)

def prob_eh_3way(P, side:str, hcap:int, outcome:str):
    # European handicap: adjust scores then 1X2 on adjusted
    def cond(a,b):
        ha=a; hb=b
        if side=="1":
            ha = a + hcap
        else:
            hb = b + hcap
        if outcome=="1": return ha>hb
        if outcome=="X": return ha==hb
        return ha<hb
    return total_prob(P, cond)

def prob_ah(P, side:str, line:float):
    # Asian handicap: probability of win/push/lose under handicap
    # Convention: side "1" means home + (-line) applied to home score comparison
    # Evaluate based on score difference d = home - away
    # For side 1 with line L: bet wins if d > L, push if d == L (when L is integer), loses if d < L
    # For quarter lines (.25/.75), push probability is split half from neighboring half-line; we report approximated push=0 and compute split under standard rules:
    wins=0.0; push=0.0; lose=0.0
    m=len(P); n=len(P[0])
    for a in range(m):
        for b in range(n):
            d = (a-b) if side=="1" else (b-a)
            prob = P[a][b]
            if abs(line - round(line))<1e-9: # integer
                if d > line: wins += prob
                elif d == line: push += prob
                else: lose += prob
            else:
                # quarter/half lines: treat strictly
                if d - line > 0: wins += prob
                elif abs(d - line) < 1e-9: push += prob
                else: lose += prob
    return wins, push, lose

def half_total_prob(mu_home, mu_away, over_under:str, n:float):
    Ph, Ps = half_score_mats(mu_home, mu_away)
    P = Ph  # either half identical by assumption
    if over_under=="O":
        return prob_over_n5(P, n)
    else:
        return prob_under_n5(P, n)

def half_btts(mu_home, mu_away):
    Ph, _ = half_score_mats(mu_home, mu_away)
    return prob_btts(Ph), 1.0 - prob_btts(Ph)

def half_1x2(mu_home, mu_away):
    Ph, _ = half_score_mats(mu_home, mu_away)
    return prob_1x2(Ph)

def prob_htft(mu_home, mu_away, ht:str, ft:str, max_goals:int=6):
    # joint over halves: H1,A1 ~ Pois(mu/2), H2,A2 ~ Pois(mu/2) independent
    Ph, Ps = half_score_mats(mu_home, mu_away, max_goals)
    def res(a,b):
        if a>b: return "1"
        if a==b: return "X"
        return "2"
    s=0.0
    # iterate over half-time and second half increments
    for h1 in range(len(Ph)):
        for a1 in range(len(Ph[0])):
            p1 = Ph[h1][a1]
            r1 = res(h1,a1)
            if r1 != ht: continue
            for h2 in range(len(Ps)):
                for a2 in range(len(Ps[0])):
                    p2 = Ps[h2][a2]
                    rft = res(h1+h2, a1+a2)
                    if rft == ft:
                        s += p1*p2
    return s

def fts(mu_home, mu_away):
    # first team to score: for independent Poisson races, P(H first) = lam_h/(lam_h+lam_a) * (1 - P(no goal))
    lam_h = mu_home; lam_a = mu_away
    p_no_goal = math.exp(-(lam_h+lam_a))
    if lam_h+lam_a <= 0: 
        return 0.0, 0.0, 1.0
    p_first_h = (lam_h/(lam_h+lam_a)) * (1.0 - p_no_goal)
    p_first_a = (lam_a/(lam_h+lam_a)) * (1.0 - p_no_goal)
    return p_first_h, p_first_a, p_no_goal

# ---- Corners / Cards totals using simple Poisson ----
def poisson_tail_over(lam: float, n: float, kmax:int=30):
    # P(X >= thr) for X ~ Pois(lam), with thr = floor(n)+1
    thr = int(n)+1
    s = 0.0
    for k in range(thr, kmax+1):
        s += poisson_pmf(k, lam)
    return s

def poisson_tail_under(lam: float, n: float, kmax:int=30):
    thr = int(n)  # <= floor(n)
    s = 0.0
    for k in range(0, thr+1):
        s += poisson_pmf(k, lam)
    return s

def env_mu(name:str, default:float):
    try:
        v = float(os.getenv(name, ""))
        if v>0: return v
    except Exception:
        pass
    return default

def market_corners(prob_kind:str, n: float, fx:dict):
    lam = fx.get("cornersMu", None)
    if lam is None:
        lam = env_mu("CORNERS_MU_DEFAULT", 10.0)
    return poisson_tail_over(lam, n) if prob_kind=="O" else poisson_tail_under(lam, n)

def market_yc(prob_kind:str, n: float, fx:dict):
    lam = fx.get("ycMu", None)
    if lam is None:
        lam = env_mu("YC_MU_DEFAULT", 4.0)
    return poisson_tail_over(lam, n) if prob_kind=="O" else poisson_tail_under(lam, n)

def market_rc(prob_kind:str, n: float, fx:dict):
    lam = fx.get("rcMu", None)
    if lam is None:
        lam = env_mu("RC_MU_DEFAULT", 0.3)
    return poisson_tail_over(lam, n) if prob_kind=="O" else poisson_tail_under(lam, n)

# ---- Generic predicate parser ----
def _normalize_token(token: str) -> str:
    token = token.replace("Ü","U").replace("Ö","O")
    token = token.replace("UST","O").replace("ALT","U")
    token = token.replace("GG","KG")
    return token.strip().upper()

def _make_predicate(token: str, mu_home: float, mu_away: float, fx: dict):
    # Player tokens
    mt = re.match(r'PL_(SC_ANY|SC_FIRST|SOG_O([0-9]+(?:\.[05])?)|YC|RC):([0-9]+)', token.upper())
    if mt:
        kind = mt.group(1)
        pid = mt.group(3)
        if kind == 'SC_ANY':
            return ('PL','SC_ANY', pid)
        if kind == 'SC_FIRST':
            return ('PL','SC_FIRST', pid)
        if kind.startswith('SOG_O'):
            n = float(mt.group(2))
            return ('PL','SOG_O', pid, n)
        if kind == 'YC':
            return ('PL','YC', pid)
        if kind == 'RC':
            return ('PL','RC', pid)
    
    t = _normalize_token(token)

    # Simple aliases
    if t in ("KG","NKG","1","X","2","1X","12","X2","X1","1-2","2X"):
        if t in ("KG",): return lambda a,b: (a>=1 and b>=1)
        if t in ("NKG",): return lambda a,b: (a==0 or b==0)
        if t in ("1",): return lambda a,b: a>b
        if t in ("X",): return lambda a,b: a==b
        if t in ("2",): return lambda a,b: a<b
        if t in ("1X","X1"): return lambda a,b: a>=b
        if t in ("12","1-2"): return lambda a,b: a!=b
        if t in ("X2","2X"): return lambda a,b: a<=b

    # O/U totals
    m = re.match(r'([OU])([0-9]+(?:\.[05])?)', t)
    if m:
        kind = m.group(1); n = float(m.group(2))
        thr_over = int(n)+1
        thr_under = int(n)
        if kind=="O":
            return lambda a,b: (a+b) >= thr_over
        else:
            return lambda a,b: (a+b) <= thr_under

    # Team totals
    m = re.match(r'(H|A)_([OU])([0-9]+(?:\.[05])?)', t)
    if m:
        side = m.group(1); kind = m.group(2); n = float(m.group(3))
        thr_over = int(n)+1
        thr_under = int(n)
        if side=="H":
            return (lambda a,b: a>=thr_over) if kind=="O" else (lambda a,b: a<=thr_under)
        else:
            return (lambda a,b: b>=thr_over) if kind=="O" else (lambda a,b: b<=thr_under)

    # Correct score
    m = re.match(r'CS([0-9]+)-([0-9]+)', t)
    if m:
        aa = int(m.group(1)); bb=int(m.group(2))
        return lambda a,b: (a==aa and b==bb)

    # Total band TGm-n
    m = re.match(r'TG([0-9]+)-([0-9]+)', t)
    if m:
        lo=int(m.group(1)); hi=int(m.group(2))
        return lambda a,b: (lo <= a+b <= hi)

    # Total exact TOT=k
    m = re.match(r'TOT=([0-9]+)', t)
    if m:
        k=int(m.group(1)); return lambda a,b: (a+b)==k

    # Total parity
    if t=="TOT_ODD": return lambda a,b: ((a+b)%2==1)
    if t=="TOT_EVEN": return lambda a,b: ((a+b)%2==0)

    # Margin
    m = re.match(r'(H|A)_WIN_BY([0-9]+)\+', t)
    if m:
        side=m.group(1); by=int(m.group(2))
        return (lambda a,b: (a-b)>=by) if side=="H" else (lambda a,b: (b-a)>=by)
    m = re.match(r'(H|A)_WIN_BY([0-9]+)', t)
    if m:
        side=m.group(1); by=int(m.group(2))
        return (lambda a,b: (a-b)==by) if side=="H" else (lambda a,b: (b-a)==by)

    # Clean sheet
    if t=="H_CS": return lambda a,b: b==0
    if t=="A_CS": return lambda a,b: a==0

    # DNB (success-only)
    if t=="DNB1": return lambda a,b: a>b
    if t=="DNB2": return lambda a,b: b>a

    # European Handicap: EH1-1:1 / EH2+1:X
    m = re.match(r'EH(1|2)([+-]?[0-9]+):([12X])', t)
    if m:
        side=m.group(1); hcap=int(m.group(2)); out=m.group(3)
        def cond(a,b):
            ha=a; hb=b
            if side=="1": ha = a + hcap
            else: hb = b + hcap
            if out=="1": return ha>hb
            if out=="X": return ha==hb
            return ha<hb
        return cond

    # Half markets
    m = re.match(r'(1H|2H)_([OU])([0-9]+(?:\.[05])?)', t)
    if m:
        half=m.group(1); kind=m.group(2); n=float(m.group(3))
        # We evaluate on half distribution built from mu/2
        # Here we return a lambda to evaluate on full P but we need special eval outside;
        return ("HALF_TOTAL", half, kind, n)

    if t in ("1H_1","1H_X","1H_2","2H_1","2H_X","2H_2","1H_KG","1H_NKG"):
        return ("HALF_MISC", t)

    # HTFT
    m = re.match(r'HTFT([12X])-([12X])', t)
    if m:
        return ("HTFT", m.group(1), m.group(2))

    # First to score
    if t in ("FTS_H","FTS_A","FTS_NONE"):
        return ("FTS", t)

    # Corners & Cards totals
    m = re.match(r'(C|YC|RC)_([OU])([0-9]+(?:\.[05])?)', t)
    if m:
        kind=m.group(1); ou=m.group(2); n=float(m.group(3))
        return ("SIDE_TOT", kind, ou, n)

    # default false
    return lambda a,b: False


def _pl_get_baseline(fx:dict, pid:str):
    b = (fx.get("playerBaselines") or {}).get(pid)
    if not b:
        # default baseline if not provided by route
        b = {"playerId": pid, "side":"?", "startProb":0.6, "minutesExp":65.0, "goal90":0.25, "sog90":0.7, "yc90":0.12, "rc90":0.01}
    return b

def _pois_tail_ge(lam: float, n: float, kmax:int=10):
    thr = int(n)+1
    s=0.0
    for k in range(thr, kmax+1):
        s += poisson_pmf(k, lam)
    return s

def _pl_prob_goal_any(mu_home, mu_away, fx, pid:str):
    b = _pl_get_baseline(fx, pid)
    lam = max(0.0001, b.get("goal90",0.2) * (b.get("minutesExp",70.0)/90.0) * b.get("startProb",0.6))
    return 1.0 - math.exp(-lam)

def _pl_prob_goal_first(mu_home, mu_away, fx, pid:str):
    b = _pl_get_baseline(fx, pid)
    side = b.get("side","?")
    team_lam = mu_home if side=="H" else (mu_away if side=="A" else (mu_home+mu_away)/2.0)
    if team_lam <= 0.0: return 0.0
    # player's share in team scoring intensity
    lam_p = max(0.0001, b.get("goal90",0.2) * (b.get("minutesExp",70.0)/90.0) * b.get("startProb",0.6))
    share = min(0.9, lam_p / max(1e-6, team_lam))
    p_team_scores = 1.0 - math.exp(-team_lam)
    return share * p_team_scores

def _pl_prob_sog_over(mu_home, mu_away, fx, pid:str, n: float):
    b = _pl_get_baseline(fx, pid)
    lam = max(0.0001, b.get("sog90",0.7) * (b.get("minutesExp",70.0)/90.0) * b.get("startProb",0.6))
    return _pois_tail_ge(lam, n, kmax=12)

def _pl_prob_yc(mu_home, mu_away, fx, pid:str):
    b = _pl_get_baseline(fx, pid)
    lam = max(0.0001, b.get("yc90",0.12) * (b.get("minutesExp",70.0)/90.0) * b.get("startProb",0.6))
    return 1.0 - math.exp(-lam)

def _pl_prob_rc(mu_home, mu_away, fx, pid:str):
    b = _pl_get_baseline(fx, pid)
    lam = max(0.00001, b.get("rc90",0.01) * (b.get("minutesExp",70.0)/90.0) * b.get("startProb",0.6))
    return 1.0 - math.exp(-lam)

def prob_combo(P, expr: str, mu_home: float, mu_away: float, fx:dict):
    if not expr: return {"prob":0.0}
    parts = [p for p in re.split(r'[+&]', expr) if p.strip()]
    preds = [_make_predicate(p, mu_home, mu_away, fx) for p in parts]

    # Special evaluators
    # If any part returns tuple markers, we compute separately and multiply (independence approx between special and full-time?). 
    # Safer: compute directly for each special:
    specials = []
    normal_preds = []
    for pr in preds:
        if callable(pr):
            normal_preds.append(pr)
        else:
            specials.append(pr)

    # Evaluate normal joint prob on full-time matrix
    prob_norm = 1.0
    if normal_preds:
        prob_norm = total_prob(P, lambda a,b: all(pr(a,b) for pr in normal_preds))

    # Evaluate specials and multiply (approx). Some specials directly return prob.
    prob_spec = 1.0
    details = {}
    for sp in specials:
        kind = sp[0]
        if kind=="HALF_TOTAL":
            _, half, ou, n = sp
            ph = half_total_prob(mu_home, mu_away, ou, n)
            prob_spec *= ph
            details.setdefault("half",[]).append({"half":half,"type":f"{ou}{n}","prob":round(ph,4)})
        elif kind=="HALF_MISC":
            t = sp[1]
            if t.endswith("_KG") or t.endswith("_NKG"):
                pkg, pnkg = half_btts(mu_home, mu_away)
                ph = pkg if t.endswith("_KG") else pnkg
                prob_spec *= ph
                details.setdefault("half",[]).append({"half":t[:2],"type":t[3:], "prob":round(ph,4)})
            else:
                ph1, px1, p21 = half_1x2(mu_home, mu_away)
                mp = {"1H_1":ph1,"1H_X":px1,"1H_2":p21,"2H_1":ph1,"2H_X":px1,"2H_2":p21}[t]
                prob_spec *= mp
                details.setdefault("half",[]).append({"half":t[:2],"type":t[3:], "prob":round(mp,4)})
        elif kind=="HTFT":
            _, ht, ft = sp
            p = prob_htft(mu_home, mu_away, ht, ft)
            prob_spec *= p
            details["htft"]= {"ht":ht,"ft":ft,"prob":round(p,4)}
        elif kind=="FTS":
            _, which = sp
            ph, pa, pn = fts(mu_home, mu_away)
            mp = {"FTS_H":ph, "FTS_A":pa, "FTS_NONE":pn}[which]
            prob_spec *= mp
            details["fts"] = {"FTS_H":round(ph,4),"FTS_A":round(pa,4),"FTS_NONE":round(pn,4)}
        elif kind=="SIDE_TOT":
            _, what, ou, n = sp
            if what=="C":
                p = market_corners(ou, n, fx)
            elif what=="YC":
                p = market_yc(ou, n, fx)
            else:
                p = market_rc(ou, n, fx)
            prob_spec *= p
            details.setdefault("side_tot",[]).append({"type":f"{what}_{ou}{n}", "prob":round(p,4)})
        elif kind=='PL':
            _, sub, pid, *rest = sp
            if sub=='SC_ANY': p = _pl_prob_goal_any(mu_home, mu_away, fx, pid)
            elif sub=='SC_FIRST': p = _pl_prob_goal_first(mu_home, mu_away, fx, pid)
            elif sub=='SOG_O': p = _pl_prob_sog_over(mu_home, mu_away, fx, pid, rest[0])
            elif sub=='YC': p = _pl_prob_yc(mu_home, mu_away, fx, pid)
            elif sub=='RC': p = _pl_prob_rc(mu_home, mu_away, fx, pid)
            else: p = 1.0
            prob_spec *= p
            details.setdefault('players',[]).append({'token':f'{sub}:{pid}','prob':round(p,4)})
        else:
            # unknown special, neutral multiplier
            pass

    # Asian handicap tokens should be sent alone ideally; if present in combo, we multiply by other parts (approx)
    # We detect AH tokens in outer handler (route) to attach push probability.
    return {"prob": prob_norm * prob_spec, "details": details}
