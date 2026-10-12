from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

import discord_service


# Service-level error mapping and Discord API client configuration tests
class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None, json_raises=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}
        self._json_raises = json_raises

    def json(self):
        if self._json_raises:
            raise ValueError('not-json')
        return self._payload


@pytest.mark.anyio
async def test_make_client_uses_v10_base_path(monkeypatch):
    monkeypatch.setenv('DISCORD_API_URL', 'https://discord.com/api/v10')
    client = discord_service.make_client('TOK123')
    try:
        assert str(client.base_url) == 'https://discord.com/api/v10/'
        assert client.headers['Authorization'] == 'Bot TOK123'
    finally:
        await client.aclose()


@pytest.mark.anyio
async def test_discord_request_maps_401_message():
    async def request(*_args, **_kwargs):
        return FakeResponse(401, {'message': 'bad auth'})

    client = SimpleNamespace(request=request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.discord_request(client, 'GET', '/users/@me')
    assert exc.value.status_code == 401
    assert 'token bota' in exc.value.detail


@pytest.mark.anyio
async def test_discord_request_parses_429_retry_after_header():
    async def request(*_args, **_kwargs):
        return FakeResponse(429, {}, headers={'Retry-After': '2'})

    client = SimpleNamespace(request=request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.discord_request(client, 'POST', '/channels/x/messages', json={})
    assert exc.value.status_code == 429
    assert exc.value.headers['Retry-After'] == '2'


@pytest.mark.anyio
async def test_discord_request_nonjson_5xx_maps_to_502():
    async def request(*_args, **_kwargs):
        return FakeResponse(503, json_raises=True)

    client = SimpleNamespace(request=request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.discord_request(client, 'GET', '/channels/1')
    assert exc.value.status_code == 502
    assert 'niedostępny' in exc.value.detail


@pytest.mark.anyio
async def test_discord_request_timeout_maps_to_504_for_post():
    async def request(*_args, **_kwargs):
        raise httpx.TimeoutException('timeout')

    client = SimpleNamespace(request=request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.discord_request(client, 'POST', '/channels/1/messages', json={})
    assert exc.value.status_code == 504
    assert 'Nie udało się potwierdzić wysyłki' in exc.value.detail


@pytest.mark.anyio
async def test_get_bot_rejects_non_bot(monkeypatch):
    async def fake_request(*_args, **_kwargs):
        return {'id': '123', 'username': 'human', 'bot': False}

    monkeypatch.setattr(discord_service, 'discord_request', fake_request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.get_bot(client=object())
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_get_channel_allows_only_guild_channel_types(monkeypatch):
    async def fake_request(*_args, **_kwargs):
        return {'id': '1', 'type': 1, 'guild_id': None, 'name': 'dm'}

    monkeypatch.setattr(discord_service, 'discord_request', fake_request)
    with pytest.raises(HTTPException) as exc:
        await discord_service.get_channel(client=object(), channel_id='12345678901234567')
    assert exc.value.status_code == 400
    assert 'Wybierz kanał tekstowy' in exc.value.detail
