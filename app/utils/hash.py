import hashlib, json
def sha256_json(obj) -> str:
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()
