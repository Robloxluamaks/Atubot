import hashlib
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from discord_models import (BotProfile, ChannelProfile, ChannelRequest, ChannelResult,
                            SendRequest, SendResponse, TokenRequest)
from discord_service import discord_request, get_bot, get_channel, make_client

router = APIRouter(prefix='/api')


@router.post('/bot/connect', response_model=BotProfile)
async def connect(payload: TokenRequest):
    async with make_client(payload.token.get_secret_value()) as client:
        return await get_bot(client)


@router.post('/channels/resolve', response_model=ChannelProfile)
async def resolve(payload: ChannelRequest):
    async with make_client(payload.token.get_secret_value()) as client:
        await get_bot(client)
        return await get_channel(client, payload.channel_id)


@router.post('/messages/send', response_model=SendResponse)
async def send(payload: SendRequest):
    results = []
    stopped = False
    async with make_client(payload.token.get_secret_value()) as client:
        await get_bot(client)
        for channel_id in payload.channel_ids:
            if stopped:
                results.append(ChannelResult(channel_id=channel_id, status='skipped',
                    detail='Pominięto po błędzie połączenia lub limicie Discorda.'))
                continue
            channel = None
            posting = False
            try:
                channel = await get_channel(client, channel_id)
                nonce = hashlib.sha256(f'{payload.request_id}:{channel_id}'.encode()).hexdigest()[:25]
                posting = True
                message = await discord_request(client, 'POST', f'/channels/{channel_id}/messages', json={
                    'content': payload.content, 'allowed_mentions': {'parse': []},
                    'nonce': nonce, 'enforce_nonce': True,
                })
                results.append(ChannelResult(
                    channel_id=channel_id, channel_name=channel.name, status='sent', detail='Wysłano',
                    message_id=message['id'],
                    message_url=f"{os.environ['DISCORD_WEB_URL']}/channels/{channel.guild_id}/{channel_id}/{message['id']}",
                ))
            except HTTPException as exc:
                uncertain = posting and exc.status_code >= 500
                results.append(ChannelResult(
                    channel_id=channel_id, channel_name=channel.name if channel else None,
                    status='unknown' if uncertain else 'failed', detail=exc.detail,
                    retry_after=float(exc.headers['Retry-After']) if exc.headers and 'Retry-After' in exc.headers else None,
                ))
                stopped = exc.status_code in {401, 429} or exc.status_code >= 500
    return SendResponse(request_id=str(payload.request_id),
                        sent_at=datetime.now(timezone.utc).isoformat(), results=results)