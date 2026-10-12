import importlib
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

TEST_COOKIE = 'test-workspace-cookie'


@pytest.fixture()
def app_module(monkeypatch):
    """Reload app module with deterministic env for isolated tests."""
    monkeypatch.setenv('MONGO_URL', 'mongodb://localhost:27017')
    monkeypatch.setenv('DB_NAME', 'test_database')
    monkeypatch.setenv('CORS_ORIGINS', '*')
    monkeypatch.setenv('DISCORD_API_URL', 'https://discord.com/api/v10')
    monkeypatch.setenv('DISCORD_CDN_URL', 'https://cdn.discordapp.com')
    monkeypatch.setenv('DISCORD_WEB_URL', 'https://discord.com')
    monkeypatch.setenv('APP_ORIGIN', 'https://testserver')
    monkeypatch.setenv('SESSION_HASH_KEY', '11' * 32)
    monkeypatch.setenv('SESSION_TTL_SECONDS', '3600')
    import rate_limit
    import workspace_auth

    rate_limit._buckets.clear()
    session = {'id': 'test-owner', 'expires_at': datetime.now(timezone.utc) + timedelta(hours=1)}

    async def fake_lookup_session(request):
        return session if request.cookies.get(workspace_auth.COOKIE) == TEST_COOKIE else None

    monkeypatch.setattr(workspace_auth, 'lookup_session', fake_lookup_session)
    import server
    return importlib.reload(server)


@pytest.fixture()
def anonymous_client(app_module):
    """Client without a workspace session (used to assert the Discord routes are gated)."""
    return TestClient(app_module.app, base_url='https://testserver')


@pytest.fixture()
def client(app_module):
    """FastAPI test client with a workspace session cookie and matching Origin (no Mongo access)."""
    return TestClient(app_module.app, base_url='https://testserver',
                      headers={'Origin': 'https://testserver'}, cookies={'__Host-relay_workspace': TEST_COOKIE})


@pytest.fixture()
def patch_make_client(monkeypatch):
    """Patch discord_routes.make_client to avoid external HTTP in route tests."""

    class DummyClient:
        def __init__(self, token):
            self.token = token

    @asynccontextmanager
    async def factory(token):
        yield DummyClient(token)

    import discord_routes

    monkeypatch.setattr(discord_routes, 'make_client', factory)
    return DummyClient