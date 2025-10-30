STATUS_MAP = {
    'NS': 'SCHEDULED',
    'TBD': 'SCHEDULED',
    'PST': 'POSTPONED',
    'CANC': 'CANCELLED',
    'SUSP': 'SUSPENDED',
    '1H': 'LIVE',
    'HT': 'HT',
    '2H': 'LIVE',
    'ET': 'LIVE',
    'P': 'LIVE',
    'FT': 'FT',
    'AET': 'FT',
    'PEN': 'FT'
}

def normalize_status(short_code: str | None) -> str:
    if not short_code:
        return 'SCHEDULED'
    return STATUS_MAP.get(short_code.upper(), short_code.upper())
