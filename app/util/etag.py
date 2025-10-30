from fastapi import Request, Response, HTTPException
import hashlib, json

def etag_response(request: Request, response: Response, payload_obj, weak_prefix="W/"):
    data = json.dumps(payload_obj, sort_keys=True, default=str).encode("utf-8")
    tag = weak_prefix + '"' + hashlib.md5(data).hexdigest() + '"'
    inm = request.headers.get('If-None-Match')
    if inm and inm == tag:
        raise HTTPException(status_code=304, detail="Not Modified")
    response.headers['ETag'] = tag
    response.headers['Cache-Control'] = 'public, max-age=15'
    return payload_obj
