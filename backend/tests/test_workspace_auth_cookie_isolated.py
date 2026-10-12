import asyncio
from types import SimpleNamespace

import workspace_auth
from fastapi import Response


# Isolated workspace_auth establish route test with mocked session lookup/DB insert
def test_establish_sets_strict_direct_app_cookie_attributes(monkeypatch):
    class _Sessions:
        def __init__(self):
            self.inserted = None

        async def insert_one(self, payload):
            self.inserted = payload

    sessions = _Sessions()

    async def fake_lookup_session(_request):
        return None

    monkeypatch.setenv('SESSION_TTL_SECONDS', '2592000')
    monkeypatch.setenv('SESSION_HASH_KEY', '11' * 32)
    monkeypatch.setattr(workspace_auth, 'lookup_session', fake_lookup_session)
    monkeypatch.setattr(workspace_auth, 'db', SimpleNamespace(sessions=sessions))
    monkeypatch.setattr(workspace_auth.secrets, 'token_urlsafe', lambda _n: 'test-cookie-raw-token')

    response = Response()
    result = asyncio.run(workspace_auth.establish(SimpleNamespace(cookies={}), response))

    assert result.ready is True
    assert sessions.inserted and sessions.inserted.get('id')

    set_cookie = response.headers.get('set-cookie', '')
    assert set_cookie.startswith('__Host-relay_workspace=')

    parts = [p.strip() for p in set_cookie.split(';') if p.strip()]
    attrs = {}
    flags = set()
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            attrs[key.lower()] = value.lower()
        else:
            flags.add(part.lower())

    assert attrs.get('path') == '/'
    assert attrs.get('samesite') == 'lax'
    assert 'domain' not in attrs
    assert 'secure' in flags
    assert 'httponly' in flags
    assert 'partitioned' not in flags