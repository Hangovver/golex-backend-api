
import unicodedata, re
from typing import Dict, Any
from .tz_utils import to_local_time

_TR_OVERRIDES_TEAMS = {
# key: normalized english-ish, value: Turkish display
    "besiktas": "Beşiktaş",
    "galatasaray": "Galatasaray",
    "fenerbahce": "Fenerbahçe",
    "istanbulbasaksehir": "İstanbul Başakşehir",
    "trabzonspor": "Trabzonspor",
    "adana_demirspor": "Adana Demirspor",
    "kasimpasa": "Kasımpaşa",
    "alanyaspor": "Alanyaspor",
    "caykur_rizespor": "Çaykur Rizespor",
    "mke_ankaragucu": "MKE Ankaragücü",
    "fatih_karagumruk": "Fatih Karagümrük",
    "gaziantep_fk": "Gaziantep FK",
    "hatayspor": "Hatayspor",
    "pendikspor": "Pendikspor",
    "kayserispor": "Kayserispor",
    "konyaspor": "Konyaspor",
    "antalyaspor": "Antalyaspor",
    "sivasspor": "Sivasspor",
    "giresunspor": "Giresunspor",
    "umraniyespor": "Ümraniyespor",

    "bayern_munich": "Bayern Münih",
    "bayern_munchen": "Bayern Münih",
    "fc_bayern_munich": "Bayern Münih",
    "fc_bayern_munchen": "Bayern Münih",
    "bayer_leverkusen": "Bayer Leverkusen",
    "borussia_dortmund": "Borussia Dortmund",
    "dortmund": "Borussia Dortmund",
    "rb_leipzig": "Leipzig",
    "leipzig": "Leipzig",
    "borussia_monchengladbach": "Mönchengladbach",
    "borussia_m_gladbach": "Mönchengladbach",
    "monchengladbach": "Mönchengladbach",
    "mgladbach": "Mönchengladbach",
    "eintracht_frankfurt": "Eintracht Frankfurt",
    "frankfurt": "Eintracht Frankfurt",
    "schalke_04": "Schalke 04",
    "fc_schalke_04": "Schalke 04",
    "wolfsburg": "Wolfsburg",
    "hertha_berlin": "Hertha Berlin",
    "hertha_bsc": "Hertha Berlin",
    "hoffenheim": "Hoffenheim",
    "mainz_05": "Mainz 05",
    "freiburg": "Freiburg",
    "1_fc_koln": "Köln",
    "fc_koln": "Köln",
    "koln": "Köln",
    "cologne": "Köln",
    "augsburg": "Augsburg",
    "union_berlin": "Union Berlin",
    "werder_bremen": "Werder Bremen",
    "hamburger_sv": "Hamburg",
    "hamburg": "Hamburg",
    "manchester_united": "Manchester United",
    "man_utd": "Manchester United",
    "manchester_city": "Manchester City",
    "liverpool": "Liverpool",
    "chelsea": "Chelsea",
    "arsenal": "Arsenal",
    "tottenham_hotspur": "Tottenham",
    "tottenham": "Tottenham",
    "newcastle_united": "Newcastle United",
    "everton": "Everton",
    "west_ham_united": "West Ham",
    "west_ham": "West Ham",
    "leicester_city": "Leicester City",
    "aston_villa": "Aston Villa",
    "brighton_hove_albion": "Brighton",
    "brighton": "Brighton",
    "crystal_palace": "Crystal Palace",
    "wolverhampton_wanderers": "Wolverhampton",
    "wolverhampton": "Wolverhampton",
    "nottingham_forest": "Nottingham Forest",
    "real_madrid": "Real Madrid",
    "barcelona": "Barcelona",
    "fc_barcelona": "Barcelona",
    "atletico_madrid": "Atletico Madrid",
    "sevilla": "Sevilla",
    "valencia": "Valencia",
    "villarreal": "Villarreal",
    "real_sociedad": "Real Sociedad",
    "athletic_bilbao": "Athletic Bilbao",
    "real_betis": "Real Betis",
    "celta_vigo": "Celta Vigo",
    "osasuna": "Osasuna",
    "inter_milan": "Inter",
    "internazionale": "Inter",
    "ac_milan": "Milan",
    "milan": "Milan",
    "juventus": "Juventus",
    "napoli": "Napoli",
    "roma": "Roma",
    "lazio": "Lazio",
    "fiorentina": "Fiorentina",
    "atalanta": "Atalanta",
    "paris_saint_germain": "Paris Saint-Germain",
    "psg": "Paris Saint-Germain",
    "olympique_marseille": "Marsilya",
    "marseille": "Marsilya",
    "olympique_lyonnais": "Lyon",
    "lyon": "Lyon",
    "as_monaco": "Monaco",
    "monaco": "Monaco",
    "lille": "Lille",
    "rennes": "Rennes",
    "sporting_cp": "Sporting Lizbon",
    "sporting_lisbon": "Sporting Lizbon",
    "sl_benfica": "Benfica",
    "benfica": "Benfica",
    "fc_porto": "Porto",
    "porto": "Porto",
    "ajax": "Ajax",
    "psv": "PSV",
    "feyenoord": "Feyenoord",
    "celtic": "Celtic",
    "rangers": "Rangers",
}

_TR_OVERRIDES_LEAGUES = {
"super_lig": "Süper Lig",
    "turkiye_kupasi": "Türkiye Kupası",

    "super_lig": "Süper Lig",
    "turkiye_kupasi": "Türkiye Kupası",
    "premier_league": "Premier League",
    "la_liga": "La Liga",
    "bundesliga": "Bundesliga",
    "serie_a": "Serie A",
    "ligue_1": "Ligue 1",
    "eredivisie": "Eredivisie",
    "primeira_liga": "Primeira Liga",
    "uefa_champions_league": "Şampiyonlar Ligi",
    "champions_league": "Şampiyonlar Ligi",
    "ucl": "Şampiyonlar Ligi",
    "uefa_europa_league": "UEFA Avrupa Ligi",
    "europa_league": "UEFA Avrupa Ligi",
    "uefa_europa_conference_league": "Konferans Ligi",
    "conference_league": "Konferans Ligi",
    "dfb_pokal": "Almanya Kupası",
    "fa_cup": "FA Cup",
    "copa_del_rey": "Kral Kupası",
    "coppa_italia": "İtalya Kupası",
    "coupe_de_france": "Fransa Kupası",
    "tff_super_kupasi": "TFF Süper Kupa",
}

def _slug(s: str) -> str:
    if not s: return ""
    # normalize: remove diacritics, keep alnum/underscore
    ns = unicodedata.normalize("NFKD", s)
    ns = "".join(ch for ch in ns if not unicodedata.combining(ch))
    ns = re.sub(r"[^A-Za-z0-9]+", "_", ns).strip("_").lower()
    return ns

def tr_display_name(name: str, entity: str = "team") -> str:
    if not name: return name
    key = _slug(name)
    if entity == "league":
        return _TR_OVERRIDES_LEAGUES.get(key, name)
    return _TR_OVERRIDES_TEAMS.get(key, name)

def localize_payload(payload: Any, lang: str = "tr", tz: str = "Europe/Istanbul") -> Any:
    # Recursively walk dict/list; add display fields and local kickoff when applicable
    try:
        if lang.lower().startswith("tr"):
            if isinstance(payload, dict):
                out = {}
                for k,v in payload.items():
                    out[k] = localize_payload(v, lang, tz)
                # team name hints
                if "teamName" in out and "teamDisplayName" not in out:
                    out["teamDisplayName"] = tr_display_name(out.get("teamName",""), "team")
                if "name" in out and ("teamId" in out or out.get("type")=="team") and "displayName" not in out:
                    out["displayName"] = tr_display_name(out.get("name",""), "team")
                # league
                if ("leagueId" in out or out.get("type")=="league") and "name" in out and "displayName" not in out:
                    out["displayName"] = tr_display_name(out.get("name",""), "league")
                if "leagueName" in out and "leagueDisplayName" not in out:
                    out["leagueDisplayName"] = tr_display_name(out.get("leagueName",""), "league")
                # fixtures: home/away + kickoff
                if ("home" in out and "away" in out) and ("homeDisplayName" not in out or "awayDisplayName" not in out):
                    out["homeDisplayName"] = tr_display_name(out.get("home",""), "team")
                    out["awayDisplayName"] = tr_display_name(out.get("away",""), "team")
                # kickoff → kickoffLocal
                for dk in ("kickoff","kickoffUtc","date","datetime","eventTimeUtc"):
                    if dk in out and "kickoffLocal" not in out:
                        local = to_local_time(out.get(dk), tz)
                        if local: out["kickoffLocal"] = local
                return out
            elif isinstance(payload, list):
                return [localize_payload(x, lang, tz) for x in payload]
        return payload
    except Exception:
        return payload
