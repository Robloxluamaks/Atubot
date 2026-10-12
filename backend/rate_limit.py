import time
from collections import deque

from fastapi import Depends, HTTPException, Request

from workspace_auth import owner

WINDOW = 60
_buckets: dict[tuple, deque] = {}


def client_ip(request: Request):
    forwarded = request.headers.get('x-forwarded-for', '')
    return forwarded.split(',')[0].strip() or (request.client.host if request.client else 'unknown')


def _sweep(now):
    if len(_buckets) < 5000:
        return
    for key in [k for k, v in _buckets.items() if not v or now - v[-1] > WINDOW]:
        _buckets.pop(key, None)


def _hit(key, limit, now):
    bucket = _buckets.setdefault(key, deque())
    while bucket and now - bucket[0] > WINDOW:
        bucket.popleft()
    if len(bucket) >= limit:
        retry = max(1, int(WINDOW - (now - bucket[0])) + 1)
        raise HTTPException(429, f'Zbyt wiele prób. Spróbuj ponownie za {retry} s.', headers={'Retry-After': str(retry)})
    bucket.append(now)


def throttle(limit: int):
    async def guard(request: Request, session=Depends(owner)):
        now = time.monotonic()
        _sweep(now)
        _hit((request.url.path, 'ip', client_ip(request)), limit * 3, now)
        _hit((request.url.path, 'session', session['id']), limit, now)
        return session
    return guard
