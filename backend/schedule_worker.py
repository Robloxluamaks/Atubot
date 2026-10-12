import os
from datetime import timedelta
from uuid import uuid4
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException
from pymongo import ReturnDocument
from database import db, utcnow
from discord_models import SendRequest
from discord_routes import send_batch


async def run_due_schedules():
    # Finite work triggered by the platform; no in-process scheduling loop.
    await db.schedules.update_many({'state': 'running', 'started_at': {'$lt': utcnow() - timedelta(minutes=30)}},
        {'$set': {'state': 'error', 'last_error': 'Poprzednia wysyłka nie została potwierdzona. Sprawdź kanały przed wznowieniem.'}})
    for _ in range(20):
        run_key = str(uuid4())
        job = await db.schedules.find_one_and_update(
            {'state': 'active', 'next_run': {'$lte': utcnow()}, 'expires_at': {'$gt': utcnow()}},
            {'$set': {'state': 'running', 'run_key': run_key, 'started_at': utcnow()}},
            sort=[('next_run', 1)], return_document=ReturnDocument.AFTER, projection={'_id': 0})
        if not job:
            break
        await execute_job(job)


async def execute_job(job):
    query = {'id': job['id'], 'run_key': job['run_key']}

    async def still_running():
        return bool(await db.schedules.find_one({**query, 'state': 'running'}, {'_id': 0, 'id': 1}))

    try:
        token = Fernet(os.environ['FERNET_KEY']).decrypt(job['token_ciphertext'].encode()).decode()
        payload = SendRequest(token=token, request_id=job['run_key'], channel_ids=job['channel_ids'],
            content=job['content'], embed=job.get('embed'), overrides=job.get('overrides', {}))
        result = await send_batch(payload, should_continue=still_running)
        all_sent = all(r.status == 'sent' for r in result.results)
        count = job['run_count'] + 1
        finish = not job['interval_minutes'] or count >= job['max_runs']
        changes = {'last_results': [r.model_dump() for r in result.results], 'last_run': utcnow(), 'run_count': count}
        await db.schedules.update_one(query, {'$set': changes})
        if not all_sent:
            changes = {'state': 'error', 'last_error': 'Nie wszystkie wiadomości dostarczono. Sprawdź raport przed wznowieniem.'}
        elif finish:
            changes = {'state': 'completed', 'token_ciphertext': None, 'next_run': None, 'last_error': None}
        else:
            interval = timedelta(minutes=job['interval_minutes'])
            # Skip missed intervals, never burst-send historical occurrences.
            jumps = max(1, (utcnow() - job['next_run']) // interval + 1)
            changes = {'state': 'active', 'next_run': job['next_run'] + interval * jumps, 'last_error': None}
        await db.schedules.update_one({**query, 'state': 'running'}, {'$set': changes})
    except (InvalidToken, KeyError):
        await db.schedules.update_one(query, {'$set': {'state': 'error', 'token_ciphertext': None,
            'last_error': 'Nie można odczytać tokenu. Utwórz nowy harmonogram.'}})
    except HTTPException as exc:
        changes = {'state': 'error', 'last_error': exc.detail}
        if exc.status_code == 401:
            changes['token_ciphertext'] = None
        await db.schedules.update_one({**query, 'state': 'running'}, {'$set': changes})
    except Exception:
        # Do not log exceptions containing secrets; never blindly retry a send.
        await db.schedules.update_one({**query, 'state': 'running'}, {'$set': {
            'state': 'error', 'last_error': 'Nie potwierdzono wykonania. Sprawdź kanały przed ponowieniem.'}})