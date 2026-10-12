import hashlib
import hmac
import os
from datetime import datetime, timedelta
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError
from pymongo.errors import DuplicateKeyError
from database import db, utcnow
from schedule_worker import run_due_schedules

router = APIRouter(prefix='/api/cron')


class Envelope(BaseModel):
    event: Literal['schedule.triggered']
    schedule_id: str = Field(min_length=1, max_length=100)
    run_id: str = Field(min_length=1, max_length=200)
    dispatch_time: datetime
    data: None = None


async def authorize_cron(request: Request):
    supplied = request.headers.get('authorization', '')
    expected = 'Bearer ' + os.environ['WEBHOOK_CRON_SECRET']
    if not hmac.compare_digest(supplied.encode(), expected.encode()):
        raise HTTPException(401, 'Brak autoryzacji.')


@router.post('/dispatch', dependencies=[Depends(authorize_cron)])
async def cron_dispatch(request: Request, background: BackgroundTasks):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    try:
        event = Envelope.model_validate(await request.json())
    except (ValidationError, ValueError):
        raise HTTPException(400, 'Nieprawidłowe wywołanie harmonogramu.') from None
    run_id = request.headers.get('x-webhook-id') or event.run_id
    if run_id != event.run_id or event.schedule_id != 'relay-dispatch':
        raise HTTPException(400, 'Nieprawidłowy identyfikator zadania.')
    try:
        await db.cron_runs.insert_one({'_id': hashlib.sha256(run_id.encode()).hexdigest(),
            'created_at': utcnow(), 'expires_at': utcnow() + timedelta(days=7)})
    except DuplicateKeyError:
        return {'accepted': True, 'duplicate': True}
    background.add_task(run_due_schedules)
    return {'accepted': True, 'duplicate': False}