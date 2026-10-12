import os
from datetime import timedelta
from uuid import uuid4
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from database import db, utcnow
from discord_service import get_bot, get_channel, make_client
from schedule_models import ScheduleIn, ScheduleOut, ScheduleAction
from workspace_auth import owner

router = APIRouter(prefix='/api/schedules')
PUBLIC = {'_id': 0, 'token_ciphertext': 0, 'owner_id': 0, 'run_key': 0, 'started_at': 0}


@router.get('', response_model=list[ScheduleOut])
async def list_schedules(session=Depends(owner)):
    return await db.schedules.find({'owner_id': session['id']}, PUBLIC).sort('created_at', -1).to_list(100)


@router.post('', response_model=ScheduleOut)
async def create_schedule(payload: ScheduleIn, session=Depends(owner)):
    if not utcnow() + timedelta(seconds=30) < payload.next_run < session['expires_at']:
        raise HTTPException(400, 'Wybierz przyszłą datę przed końcem ważności przestrzeni (do 30 dni).')
    if await db.schedules.count_documents({'owner_id': session['id']}) >= 30:
        raise HTTPException(400, 'Maksymalnie 30 harmonogramów w przestrzeni.')
    async with make_client(payload.token.get_secret_value()) as client:
        bot = await get_bot(client)
        for channel_id in payload.channel_ids:
            await get_channel(client, channel_id)
    data = payload.model_dump(exclude={'token', 'consent', 'request_id'})
    data.update(id=str(uuid4()), owner_id=session['id'], bot_name=bot.username,
        created_at=utcnow(), expires_at=session['expires_at'], state='active', run_count=0,
        token_ciphertext=Fernet(os.environ['FERNET_KEY']).encrypt(payload.token.get_secret_value().encode()).decode())
    await db.schedules.insert_one(data)
    return await db.schedules.find_one({'id': data['id'], 'owner_id': session['id']}, PUBLIC)


@router.patch('/{schedule_id}', response_model=ScheduleOut)
async def update_schedule(schedule_id: str, payload: ScheduleAction, session=Depends(owner)):
    query = {'id': schedule_id, 'owner_id': session['id']}
    schedule = await db.schedules.find_one(query, {'_id': 0})
    if not schedule:
        raise HTTPException(404, 'Nie znaleziono harmonogramu.')
    if payload.action == 'pause':
        if schedule['state'] not in {'active', 'running'}:
            raise HTTPException(409, 'Ten harmonogram nie jest aktywny.')
        changes = {'state': 'paused'}
        query['state'] = {'$in': ['active', 'running']}
    else:
        if schedule['state'] not in {'paused', 'error'} or not schedule.get('token_ciphertext'):
            raise HTTPException(409, 'Utwórz nowy harmonogram z aktualnym tokenem bota.')
        if schedule['run_count'] >= schedule['max_runs']:
            raise HTTPException(409, 'Wykonano wszystkie zaplanowane wysyłki.')
        query['state'] = {'$in': ['paused', 'error']}
        changes = {'state': 'active', 'next_run': utcnow() + timedelta(minutes=15), 'last_error': None}
    changed = await db.schedules.update_one(query, {'$set': changes})
    if not changed.matched_count:
        raise HTTPException(409, 'Status zmienił się. Odśwież listę.')
    return await db.schedules.find_one({'id': schedule_id, 'owner_id': session['id']}, PUBLIC)


@router.delete('/{schedule_id}')
async def delete_schedule(schedule_id: str, session=Depends(owner)):
    result = await db.schedules.delete_one({'id': schedule_id, 'owner_id': session['id']})
    if not result.deleted_count:
        raise HTTPException(404, 'Nie znaleziono harmonogramu.')
    return {'deleted': True}