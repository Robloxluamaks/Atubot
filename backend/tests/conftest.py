import importlib
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def app_module(monkeypatch):
    """Reload app module with deterministic env for isolated tests."""
    monkeypatch.setenv('MONGO_URL', 'mongodb://localhost:27017')
    monkeypatch.setenv('DB_NAME', 'test_database')
    monkeypatch.setenv('CORS_ORIGINS', '*')
    monkeypatch.setenv('DISCORD_API_URL', 'https://discord.com/api/v10')
    monkeypatch.setenv('DISCORD_CDN_URL', 'https://cdn.discordapp.com')
    monkeypatch.setenv('DISCORD_WEB_URL', 'https://discord.com')
    import server
    return importlib.reload(server)


@pytest.fixture()
def client(app_module):
    """FastAPI test client fixture."""
    return TestClient(app_module.app)


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