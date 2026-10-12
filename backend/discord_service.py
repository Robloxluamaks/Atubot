import math
import os

import httpx
from fastapi import HTTPException

from discord_models import BotProfile, ChannelProfile, GuildProfile, GuildChannelProfile

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Relay/1.0'


def make_client(token: str, mode: str = 'bot'):
    is_bot = mode != 'selfbot'
    return httpx.AsyncClient(
        base_url=os.environ['DISCORD_API_URL'],
        headers={
            'Authorization': f'Bot {token}' if is_bot else token,
            'User-Agent': 'RelayBot/1.0' if is_bot else BROWSER_UA,
        },
        timeout=httpx.Timeout(12.0, connect=5.0),
        follow_redirects=False,
    )


async def discord_request(client, method, path, expect='object', **kwargs):
    try:
        response = await client.request(method, path, **kwargs)
    except httpx.RequestError:
        message = ('Nie udało się potwierdzić wysyłki. Sprawdź kanał przed ponowieniem.'
                   if method == 'POST' else 'Brak odpowiedzi Discorda. Spróbuj ponownie później.')
        raise HTTPException(504, message) from None
    try:
        data = response.json()
    except ValueError:
        data = {}
    if response.status_code == 429:
        info = data if isinstance(data, dict) else {}
        try:
            seconds = float(info.get('retry_after', response.headers.get('Retry-After', 1)))
            seconds = max(1, math.ceil(seconds)) if math.isfinite(seconds) else 60
        except (TypeError, ValueError, OverflowError):
            seconds = 60
        raise HTTPException(429, f'Limit Discorda. Spróbuj za {seconds} s.',
                            headers={'Retry-After': str(seconds)})
    errors = {
        400: 'Discord odrzucił wiadomość. Sprawdź jej treść i kanał.',
        401: 'Nieprawidłowy lub wygasły token. Sprawdź go i spróbuj ponownie.',
        403: 'Brak dostępu. Sprawdź uprawnienia / obecność na serwerze.',
        404: 'Nie znaleziono kanału. Sprawdź ID i obecność na serwerze.',
    }
    if response.status_code >= 400:
        status = response.status_code if response.status_code in errors else 502
        raise HTTPException(status, errors.get(status, 'Discord jest chwilowo niedostępny.'))
    if expect == 'list':
        if not isinstance(data, list):
            raise HTTPException(502, 'Discord zwrócił nieprawidłową odpowiedź.')
        return data
    if not isinstance(data, dict) or not data.get('id'):
        raise HTTPException(502, 'Discord zwrócił nieprawidłową odpowiedź.')
    return data


async def get_identity(client, mode: str = 'bot'):
    """Działa dla bota i dla konta użytkownika. Wymusza zgodność trybu z tokenem."""
    data = await discord_request(client, 'GET', '/users/@me')
    is_bot_account = data.get('bot') is True
    if mode == 'selfbot' and is_bot_account:
        raise HTTPException(403, 'To token bota — przełącz na tryb Bot.')
    if mode != 'selfbot' and not is_bot_account:
        raise HTTPException(403, 'To token użytkownika — przełącz na tryb Self-bot.')
    avatar = data.get('avatar')
    return BotProfile(
        id=data['id'],
        username=data.get('global_name') or data['username'],
        avatar_url=(f"{os.environ['DISCORD_CDN_URL']}/avatars/{data['id']}/{avatar}.png?size=80"
                    if avatar else None),
    )


# alias dla zgodności ze starymi importami
async def get_bot(client, mode: str = 'bot'):
    return await get_identity(client, mode)


async def get_channel(client, channel_id):
    data = await discord_request(client, 'GET', f'/channels/{channel_id}')
    if data.get('type') not in {0, 5, 10, 11, 12} or not data.get('guild_id'):
        raise HTTPException(400, 'Wybierz kanał tekstowy, ogłoszeniowy lub wątek na serwerze.')
    return ChannelProfile(id=data['id'], name=data.get('name', channel_id), guild_id=data['guild_id'])


async def get_guilds(client):
    data = await discord_request(client, 'GET', '/users/@me/guilds', expect='list')
    return [GuildProfile(id=g['id'], name=g.get('name', g['id'])) for g in data]


async def get_guild_channels(client, guild_id):
    data = await discord_request(client, 'GET', f'/guilds/{guild_id}/channels', expect='list')
    return [GuildChannelProfile(id=c['id'], name=c.get('name', c['id']), type=c.get('type', 0))
            for c in data if c.get('type') in {0, 5, 10, 11, 12}]
