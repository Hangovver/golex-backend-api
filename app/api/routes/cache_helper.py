import os, time, threading
try:
    import redis
except Exception:
    redis = None

class Cache:
    def __init__(self):
        self.client = None
        url = os.getenv('REDIS_URL')
        if redis and url:
            try:
                self.client = redis.Redis.from_url(url)
            except Exception:
                self.client = None
        self.mem = {}
        self.lock = threading.Lock()
    def get(self, k):
        if self.client:
            v = self.client.get(k)
            return v.decode('utf-8') if isinstance(v, bytes) else v
        with self.lock:
            item = self.mem.get(k)
            if not item: return None
            v, exp = item
            if exp and exp < time.time():
                del self.mem[k]; return None
            return v
    def set(self, k, v, ttl=60):
        if self.client:
            self.client.setex(k, ttl, v)
            return
        with self.lock:
            self.mem[k] = (v, time.time()+ttl if ttl else None)

cache = Cache()
