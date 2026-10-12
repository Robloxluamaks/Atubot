from types import SimpleNamespace
from uuid import uuid4


# Message payload contract tests: embeds/footer transform and per-channel overrides
class TestMessagePayloadContract:
    def test_send_embed_footer_and_allowed_mentions_payload(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '9', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, channel_id):
            return SimpleNamespace(id=channel_id, name='chan', guild_id='guild-1')

        sent_payloads = []

        async def fake_discord_request(_client, method, _path, **kwargs):
            if method == 'POST':
                sent_payloads.append(kwargs['json'])
                return {'id': 'msg-1'}
            raise AssertionError('Unexpected method')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        monkeypatch.setattr(discord_routes, 'discord_request', fake_discord_request)

        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': ['12345678901234567'],
            'content': '',
            'request_id': str(uuid4()),
            'embed': {
                'title': 'Hello',
                'description': 'World',
                'color': 11259375,
                'url': 'https://example.com',
                'footer': 'Footer text',
            },
            'overrides': {},
        })
        assert response.status_code == 200
        payload = sent_payloads[0]
        assert payload['allowed_mentions'] == {'parse': []}
        assert payload['embeds'][0]['footer'] == {'text': 'Footer text'}
        assert payload['embeds'][0]['color'] == 11259375

    def test_send_rejects_override_not_in_selected_channels(self, client):
        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': ['12345678901234567'],
            'content': 'TEST',
            'request_id': str(uuid4()),
            'embed': None,
            'overrides': {
                '12345678901234568': 'rogue override',
            },
        })
        assert response.status_code == 422
        detail = response.json().get('detail', '')
        assert 'Sprawdź token' in detail

    def test_send_uses_per_channel_override_content(self, client, monkeypatch, patch_make_client):
        import discord_routes

        async def fake_get_bot(_client):
            return {'id': '9', 'username': 'RelayBot', 'avatar_url': None}

        async def fake_get_channel(_client, channel_id):
            return SimpleNamespace(id=channel_id, name=f'chan-{channel_id[-2:]}', guild_id='guild-1')

        sent_payloads = {}

        async def fake_discord_request(_client, method, path, **kwargs):
            if method == 'POST':
                channel_id = path.split('/')[2]
                sent_payloads[channel_id] = kwargs['json']
                return {'id': f'msg-{channel_id[-2:]}' }
            raise AssertionError('Unexpected method')

        monkeypatch.setattr(discord_routes, 'get_bot', fake_get_bot)
        monkeypatch.setattr(discord_routes, 'get_channel', fake_get_channel)
        monkeypatch.setattr(discord_routes, 'discord_request', fake_discord_request)

        first_channel = '12345678901234567'
        second_channel = '12345678901234568'
        response = client.post('/api/messages/send', json={
            'token': 'A' * 30,
            'channel_ids': [first_channel, second_channel],
            'content': 'DEFAULT_CONTENT',
            'request_id': str(uuid4()),
            'embed': None,
            'overrides': {
                second_channel: 'OVERRIDE_CONTENT',
            },
        })

        assert response.status_code == 200
        assert sent_payloads[first_channel]['content'] == 'DEFAULT_CONTENT'
        assert sent_payloads[second_channel]['content'] == 'OVERRIDE_CONTENT'