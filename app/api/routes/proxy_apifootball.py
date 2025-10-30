from fastapi import APIRouter, HTTPException
from .util_rate_limit import TokenBucket
from .util_circuit_breaker import CircuitBreaker

router = APIRouter(tags=['proxy'], prefix='/proxy/api-football')

bucket = TokenBucket(rate=10, capacity=60)  # 10 tokens/sec, burst 60
cb = CircuitBreaker(failure_threshold=5, recovery_time=15)

@router.get('/health')
def health():
    return {'allow': bucket.allow(0), 'cb_open': (not cb.can_pass())}
