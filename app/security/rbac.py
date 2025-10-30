from fastapi import Depends, HTTPException, Request

def require_role(role: str):
    def checker(request: Request):
        r = request.headers.get('X-Role', 'viewer').lower()
        if role == 'viewer' and r in ('viewer','operator','admin'): return True
        if role == 'operator' and r in ('operator','admin'): return True
        if role == 'admin' and r == 'admin': return True
        raise HTTPException(403, detail='forbidden')
    return checker
