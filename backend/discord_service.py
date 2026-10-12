import math
import os

import httpx
from fastapi import HTTPException

from discord_models import BotProfile, ChannelProfile


def make_client(token: str):
    return httpx.AsyncClient(
        base_url=os.environ['DISCORD_API_URL'],
        headers={'Authorization': f'Bot {token}', 'User-Agent': 'RelayBot/1.0'},
        timeout=httpx.Timeout(12.0, connect=5.0),
        follow_redirects=False,
    )


async def discord_request(client, method, path, **kwargs):
    try:
        response = await client.request(method, path, **kwargs)
    except (httpx.TimeoutException, httpx.NetworkError):
        message = ('Nie udało się potwierdzić wysyłki. Sprawdź kanał przed ponowieniem.'
                   if method == 'POST' else 'Brak odpowiedzi Discorda. Spróbuj ponownie później.')
        raise HTTPException(504, message) from None
    try:
        data = response.json()
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}
    if response.status_code == 429:
        try:
            seconds = float(data.get('retry_after', response.headers.get('Retry-After', 1)))
            seconds = max(1, math.ceil(seconds)) if math.isfinite(seconds) else 60
        except (TypeError, ValueError, OverflowError):
            seconds = 60
        raise HTTPException(429, f'Limit Discorda. Spróbuj za {seconds} s.',
                            headers={'Retry-After': str(seconds)})
    errors = {
        400: 'Discord odrzucił wiadomość. Sprawdź jej treść i kanał.',
        401: 'Nieprawidłowy lub wygasły token bota. Sprawdź go w Discord Developer Portal.',
        403: 'Bot nie ma dostępu. Sprawdź uprawnienia Wyświetlanie kanału i Wysyłanie wiadomości.',
        404: 'Nie znaleziono kanału. Sprawdź ID i obecność bota na serwerze.',
    }
    if response.status_code >= 400:
        status = response.status_code if response.status_code in errors else 502
        raise HTTPException(status, errors.get(status, 'Discord jest chwilowo niedostępny.'))
    if not data.get('id'):
        raise HTTPException(502, 'Discord zwrócił nieprawidłową odpowiedź.')
    return data


async def get_bot(client):
    data = await discord_request(client, 'GET', '/users/@me')
    if data.get('bot') is not True:
        raise HTTPException(403, 'Obsługiwane są wyłącznie oficjalne tokeny botów Discord.')
    avatar = data.get('avatar')
    return BotProfile(
        id=data['id'], username=data['username'],
        avatar_url=f"{os.environ['DISCORD_CDN_URL']}/avatars/{data['id']}/{avatar}.png?size=80" if avatar else None,
    )


async def get_channel(client, channel_id):
    data = await discord_request(client, 'GET', f'/channels/{channel_id}')
    if data.get('type') not in {0, 5, 10, 11, 12} or not data.get('guild_id'):
        raise HTTPException(400, 'Wybierz kanał tekstowy, ogłoszeniowy lub wątek na serwerze.')
    return ChannelProfile(id=data['id'], name=data.get('name', channel_id), guild_id=data['guild_id'])