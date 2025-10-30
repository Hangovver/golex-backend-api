import time

class CircuitOpen(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_time: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.state = "closed"  # "open" or "half"
        self.opened_at = 0.0

    def before_call(self):
        if self.state == "open":
            if (time.monotonic() - self.opened_at) > self.recovery_time:
                self.state = "half"
            else:
                raise CircuitOpen("API circuit open")
        # closed or half allowed

    def success(self):
        self.failures = 0
        self.state = "closed"

    def failure(self, error: Exception):
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"
            self.opened_at = time.monotonic()
