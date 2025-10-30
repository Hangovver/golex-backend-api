
#!/usr/bin/env python3
# i18n QA: ensure keys match between TR/EN and flag long labels prone to truncation
import re, sys, os, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
strings = ROOT / "mobile-android" / "app" / "src" / "main" / "java" / "com" / "golex" / "app" / "i18n" / "Strings.kt"
s = strings.read_text(encoding="utf-8")

def extract(lang):
    m = re.search(rf'private val {lang}\s*=\s*mapOf\((.*?)\)', s, re.S)
    if not m: return {}
    body = m.group(1)
    pairs = re.findall(r'"([^"]+)"\s*to\s*"([^"]*)"', body)
    return dict(pairs)

tr = extract("tr"); en = extract("en")
missing_in_tr = [k for k in en.keys() if k not in tr]
missing_in_en = [k for k in tr.keys() if k not in en]

# Heuristic: labels > 28 chars potentially truncate in small devices
long_tr = {k:v for k,v in tr.items() if len(v) > 28}
long_en = {k:v for k,v in en.items() if len(v) > 28}

res = {
    "missing_in_tr": missing_in_tr,
    "missing_in_en": missing_in_en,
    "long_tr": long_tr,
    "long_en": long_en,
}
print(json.dumps(res, ensure_ascii=False, indent=2))

# Fail CI if missing keys
if missing_in_tr or missing_in_en:
    sys.exit(1)
