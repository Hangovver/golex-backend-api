import time
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_time=30):
        self.fail = 0
        self.open_until = 0
        self.th = failure_threshold
        self.rec = recovery_time
    def on_success(self):
        self.fail = 0
    def on_failure(self):
        self.fail += 1
        if self.fail >= self.th:
            self.open_until = time.time() + self.rec
    def can_pass(self):
        return time.time() >= self.open_until
