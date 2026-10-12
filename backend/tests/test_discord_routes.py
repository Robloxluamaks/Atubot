from uuid import uuid4
from types import SimpleNamespace

import pytest
from fastapi import HTTPException


# Routing/API contract tests for Discord endpoints with isolated external dependencies
class TestHealthAndValidation:
    def test_health_ok(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data == {'status': 'ok', 'service': 'relay'}

    def test_connect_malformed_token_422_and_no_echo(self, client):
        raw_token = 'not valid token !!!'
        response = client.post('/api/bot/connect', json={'token': raw_token})
        assert response.status_code == 422
        data = response.json()
        assert data['detail'] == 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).'
        assert 'fields' in data and data['fields'] == ['token']
        assert raw_token not in str(data)

    def test_send_duplicate_channels_422(self, client):
        payload = {
            'token': 'A' * 30,
            'channel_ids': ['12345678901234567', '12345678901234567'],
            'content': 'TEST_message',
            'request_id': str(uuid4()),
        }
        response = client.post('/api/messages/send', json=payload)
        assert response.status_code == 422
        data = response.json()
        assert data['detail'] == 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).'


# Sequential send behavior tests (nonce/enforce_nonce/stop-and-skip logic)
class TestSendFlow:
    def test_send_sequential_payload_and_message_link(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '9', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, channel_id):
            return SimpleNamespace(id=channel_id, name=f'chan-{channel_id[-3:]}', guild_id='555')

        posted = []

        async def fake_discord_request(_client, method, path, **kwargs):
            if method == 'POST':
                posted.append({'path': path, 'json': kwargs['json']})
                return {'id': f"msg-{path.split('/')[2]}"}
            raise AssertionError('Unexpected non-POST request in this test')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        monkeypatch.setattr(discord_routes, 'discord_request', fake_discord_request)

        request_id = str(uuid4())
        channel_ids = ['12345678901234567', '12345678901234568']
        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': channel_ids,
            'content': 'TEST hello',
            'request_id': request_id,
        })
        assert response.status_code == 200
        data = response.json()

        assert data['request_id'] == request_id
        assert len(data['results']) == 2
        assert all(item['status'] == 'sent' for item in data['results'])
        assert data['results'][0]['message_url'].endswith(f"/555/{channel_ids[0]}/msg-{channel_ids[0]}")

        assert posted[0]['json']['allowed_mentions'] == {'parse': []}
        assert posted[0]['json']['enforce_nonce'] is True
        assert posted[0]['json']['nonce'] != posted[1]['json']['nonce']

    def test_send_stops_after_429_and_skips_rest(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '9', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, channel_id):
            return SimpleNamespace(id=channel_id, name=f'chan-{channel_id[-2:]}', guild_id='999')

        counter = {'n': 0}

        async def fake_discord_request(_client, method, _path, **_kwargs):
            if method != 'POST':
                raise AssertionError('Unexpected method')
            counter['n'] += 1
            if counter['n'] == 1:
                raise HTTPException(429, 'Limit Discorda. Spróbuj za 3 s.', headers={'Retry-After': '3'})
            return {'id': 'never'}

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        monkeypatch.setattr(discord_routes, 'discord_request', fake_discord_request)

        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': ['12345678901234567', '12345678901234568', '12345678901234569'],
            'content': 'TEST hello',
            'request_id': str(uuid4()),
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data['results']) == 3
        assert data['results'][0]['status'] == 'failed'
        assert data['results'][0]['retry_after'] == 3.0
        assert data['results'][1]['status'] == 'skipped'
        assert data['results'][2]['status'] == 'skipped'
        assert counter['n'] == 1

    def test_send_marks_unknown_for_5xx_post_and_skips_rest(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '9', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, channel_id):
            return SimpleNamespace(id=channel_id, name=f'chan-{channel_id[-2:]}', guild_id='777')

        calls = {'post': 0}

        async def fake_discord_request(_client, method, _path, **_kwargs):
            if method == 'POST':
                calls['post'] += 1
                raise HTTPException(502, 'Discord jest chwilowo niedostępny.')
            raise AssertionError('Unexpected method')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        monkeypatch.setattr(discord_routes, 'discord_request', fake_discord_request)

        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': ['12345678901234567', '12345678901234568'],
            'content': 'TEST hello',
            'request_id': str(uuid4()),
        })
        assert response.status_code == 200
        data = response.json()
        assert data['results'][0]['status'] == 'unknown'
        assert data['results'][1]['status'] == 'skipped'
        assert calls['post'] == 1


# Connect/resolve route integration behavior against dependency failures
class TestConnectResolveErrors:
    def test_connect_invalid_token_401(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            raise HTTPException(401, 'Nieprawidłowy lub wygasły token bota. Sprawdź go w Discord Developer Portal.')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        response = client.post('/api/bot/connect', json={'token': 'A' * 30})
        assert response.status_code == 401
        data = response.json()
        assert 'token bota' in data['detail']

    def test_connect_rejects_non_bot_403(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            raise HTTPException(403, 'Obsługiwane są wyłącznie oficjalne tokeny botów Discord.')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        response = client.post('/api/bot/connect', json={'token': 'A' * 30})
        assert response.status_code == 403
        data = response.json()
        assert 'oficjalne tokeny botów' in data['detail']

    def test_resolve_rejects_non_guild_channel_type(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '1', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, _channel_id):
            raise HTTPException(400, 'Wybierz kanał tekstowy, ogłoszeniowy lub wątek na serwerze.')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        response = client.post('/api/channels/resolve', json={
            'token': 'A' * 30,
            'channel_id': '12345678901234567',
        })
        assert response.status_code == 400
        data = response.json()
        assert 'Wybierz kanał tekstowy' in data['detail']
