import time
from functools import wraps
from typing import Callable, Any
from ..core.cache import cache_get, cache_set  # assumes redis wrappers in earlier steps

def cached(ttl: int = 30, key_fn: Callable[..., str] | None = None):
    def deco(fn: Callable[..., Any]):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs) if key_fn else f"cache:{fn.__name__}:{hash(str(args)+str(kwargs))}"
            v = await cache_get(key)
            if v is not None:
                return v
            res = await fn(*args, **kwargs)
            await cache_set(key, res, ex=ttl)
            return res
        return wrapper
    return deco
