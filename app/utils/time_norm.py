from datetime import datetime, timezone
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("UTC")
SEASON_CUTOFF_MONTH = 7
SEASON_OVERRIDES = {}

def parse_to_utc(dt_str: str, tz_hint: str | None = None) -> datetime:
    '''ISO/HTTP tarih stringini UTC'ye çevirir. tz_hint verilirse öncelikle onu kullanır.'''
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    if dt.tzinfo is None:
        tz = ZoneInfo(tz_hint) if tz_hint else APP_TZ
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(APP_TZ)

def season_year_for_date(dt: datetime, league_key: str | None = None) -> int:
    '''2024-08-15 → 2024 (yani 2024/25 sezonu) — varsayılan Temmuz kesimi.'''
    cutoff = SEASON_OVERRIDES.get(league_key, SEASON_CUTOFF_MONTH)
    year = dt.year
    if dt.month < cutoff:
        return year - 1
    return year

def season_name(year_start: int) -> str:
    return f"{year_start}/{str((year_start + 1) % 100).zfill(2)}"
