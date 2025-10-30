from fastapi import Request, Response
import hashlib, json
from datetime import datetime, timezone

def make_etag(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(',',':')).encode('utf-8')
    return '"' + hashlib.sha256(raw).hexdigest()[:16] + '"'

def with_http_caching(request: Request, response: Response, payload: dict, last_modified: datetime | None = None):
    # ETag
    etag = make_etag(payload)
    inm = request.headers.get("if-none-match")
    if inm and inm == etag:
        response.status_code = 304
        response.headers["ETag"] = etag
        if last_modified:
            response.headers["Last-Modified"] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return None
    # Last-Modified check (basic)
    if_modified_since = request.headers.get("if-modified-since")
    if last_modified and if_modified_since:
        # naive parse
        try:
            # Always respond 200 with payload for simplicity (demo). Real impl would compare datetimes.
            pass
        except Exception:
            pass
    response.headers["ETag"] = etag
    if last_modified:
        response.headers["Last-Modified"] = last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    return payload
