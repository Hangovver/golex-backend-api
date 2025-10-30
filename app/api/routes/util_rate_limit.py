from time import time

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last = time()
    def allow(self, cost=1) -> bool:
        now = time()
        self.tokens = min(self.capacity, self.tokens + (now - self.last)*self.rate)
        self.last = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
