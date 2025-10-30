import time, threading

class RateLimiter:
    """Simple token bucket limiter for dev.
    rate tokens per 'per' seconds.
    """
    def __init__(self, rate: int, per: float):
        self.capacity = rate
        self.tokens = rate
        self.per = per
        self.updated = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1):
        with self.lock:
            now = time.monotonic()
            delta = now - self.updated
            refill = delta * (self.capacity / self.per)
            self.tokens = min(self.capacity, self.tokens + refill)
            self.updated = now
            if self.tokens >= tokens:
                self.tokens -= tokens
                return
            sleep_for = (tokens - self.tokens) / (self.capacity / self.per)
        time.sleep(sleep_for)
        self.consume(tokens)
