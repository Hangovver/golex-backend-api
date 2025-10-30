import hashlib, json, os
from fastapi import Request
from fastapi.responses import JSONResponse, Response
from typing import Any, Tuple

def compute_etag(payload: Any) -> str:
    try:
        body = json.dumps(payload, sort_keys=True, separators=(",",":")).encode("utf-8")
    except Exception:
        body = str(payload).encode("utf-8")
    return hashlib.sha1(body).hexdigest()

def respond_with_etag(request: Request, payload: Any, max_age: int = 30) -> Response:
    etag = compute_etag(payload)
    inm = request.headers.get("if-none-match") or request.headers.get("If-None-Match")
    headers = {
        "ETag": etag,
        "Cache-Control": f"public, max-age={max_age}",
    }
    if inm and inm.strip('"') == etag:
        return Response(status_code=304, headers=headers)
    return JSONResponse(content=payload, headers=headers)
