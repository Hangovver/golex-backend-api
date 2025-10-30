import hashlib
def bucket(device_id: str, salt: str = "golex") -> int:
    if not device_id:
        return 0
    h = hashlib.sha256(f"{salt}:{device_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 100
