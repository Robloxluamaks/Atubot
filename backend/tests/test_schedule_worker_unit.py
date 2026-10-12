import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from fastapi import HTTPException

# Ensure env keys expected by database.py exist before importing schedule_worker.
for key, value in dotenv_values('/app/backend/.env').items():
    if value is not None:
        os.environ.setdefault(key, value.strip().strip('"').strip("'"))

import schedule_worker
from discord_models import ChannelResult


# Isolated schedule worker tests for state transitions without real Discord calls
class FakeSchedulesCollection:
    def __init__(self):
        self.updates = []
        self.find_one_running = True
        self.claims = []

    async def find_one(self, query, projection=None):
        if query.get('state') == 'running' and self.find_one_running:
            return {'id': query.get('id', 'x')}
        return None

    async def update_one(self, query, update):
        self.updates.append((query, update))
        return SimpleNamespace(matched_count=1)

    async def update_many(self, query, update):
        self.updates.append((query, update))
        return SimpleNamespace(modified_count=0)

    async def find_one_and_update(self, query, update, sort=None, return_document=None, projection=None):
        if self.claims:
            return self.claims.pop(0)
        return None


@pytest.mark.anyio
async def test_execute_job_completed_clears_ciphertext(monkeypatch):
    fake = FakeSchedulesCollection()
    monkeypatch.setattr(schedule_worker, 'db', SimpleNamespace(schedules=fake))
    monkeypatch.setenv('FERNET_KEY', Fernet.generate_key().decode())

    async def fake_send_batch(_payload, should_continue=None):
        return SimpleNamespace(results=[
            ChannelResult(channel_id='123456789012345678', status='sent', detail='Wysłano')
        ])

    monkeypatch.setattr(schedule_worker, 'send_batch', fake_send_batch)

    key = schedule_worker.os.environ['FERNET_KEY']
    job = {
        'id': 'sch-1',
        'run_key': str(uuid4()),
        'token_ciphertext': Fernet(key).encrypt(b'A23456789012345678901234567890').decode(),
        'channel_ids': ['123456789012345678'],
        'content': 'TEST',
        'embed': None,
        'overrides': {},
        'interval_minutes': 0,
        'max_runs': 1,
        'run_count': 0,
        'next_run': datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    await schedule_worker.execute_job(job)

    final_set = fake.updates[-1][1]['$set']
    assert final_set['state'] == 'completed'
    assert final_set['token_ciphertext'] is None
    assert final_set['next_run'] is None


@pytest.mark.anyio
async def test_execute_job_recurring_advances_next_run_without_catchup_burst(monkeypatch):
    fake = FakeSchedulesCollection()
    monkeypatch.setattr(schedule_worker, 'db', SimpleNamespace(schedules=fake))
    monkeypatch.setenv('FERNET_KEY', Fernet.generate_key().decode())

    async def fake_send_batch(_payload, should_continue=None):
        return SimpleNamespace(results=[
            ChannelResult(channel_id='123456789012345678', status='sent', detail='Wysłano')
        ])

    monkeypatch.setattr(schedule_worker, 'send_batch', fake_send_batch)

    key = schedule_worker.os.environ['FERNET_KEY']
    old_next_run = datetime.now(timezone.utc) - timedelta(hours=2)
    job = {
        'id': 'sch-2',
        'run_key': str(uuid4()),
        'token_ciphertext': Fernet(key).encrypt(b'A23456789012345678901234567890').decode(),
        'channel_ids': ['123456789012345678'],
        'content': 'TEST',
        'embed': None,
        'overrides': {},
        'interval_minutes': 15,
        'max_runs': 10,
        'run_count': 0,
        'next_run': old_next_run,
    }

    await schedule_worker.execute_job(job)

    final_set = fake.updates[-1][1]['$set']
    assert final_set['state'] == 'active'
    assert final_set['next_run'] > old_next_run + timedelta(minutes=15)


@pytest.mark.anyio
async def test_execute_job_401_sets_error_and_clears_ciphertext(monkeypatch):
    fake = FakeSchedulesCollection()
    monkeypatch.setattr(schedule_worker, 'db', SimpleNamespace(schedules=fake))
    monkeypatch.setenv('FERNET_KEY', Fernet.generate_key().decode())

    async def fake_send_batch(_payload, should_continue=None):
        raise HTTPException(status_code=401, detail='Nieprawidłowy lub wygasły token bota.')

    monkeypatch.setattr(schedule_worker, 'send_batch', fake_send_batch)

    key = schedule_worker.os.environ['FERNET_KEY']
    job = {
        'id': 'sch-3',
        'run_key': str(uuid4()),
        'token_ciphertext': Fernet(key).encrypt(b'A23456789012345678901234567890').decode(),
        'channel_ids': ['123456789012345678'],
        'content': 'TEST',
        'embed': None,
        'overrides': {},
        'interval_minutes': 0,
        'max_runs': 1,
        'run_count': 0,
        'next_run': datetime.now(timezone.utc),
    }

    await schedule_worker.execute_job(job)

    final_set = fake.updates[-1][1]['$set']
    assert final_set['state'] == 'error'
    assert final_set['token_ciphertext'] is None


@pytest.mark.anyio
async def test_run_due_schedules_claims_jobs_once(monkeypatch):
    fake = FakeSchedulesCollection()
    fake.claims = [{
        'id': 'sch-4',
        'run_key': str(uuid4()),
        'token_ciphertext': 'cipher',
        'channel_ids': ['123456789012345678'],
        'content': 'x',
        'embed': None,
        'overrides': {},
        'interval_minutes': 0,
        'max_runs': 1,
        'run_count': 0,
        'next_run': datetime.now(timezone.utc),
        'expires_at': datetime.now(timezone.utc) + timedelta(days=1),
        'state': 'running',
    }]

    executed = {'count': 0}

    async def fake_execute(_job):
        executed['count'] += 1

    monkeypatch.setattr(schedule_worker, 'db', SimpleNamespace(schedules=fake))
    monkeypatch.setattr(schedule_worker, 'execute_job', fake_execute)

    await schedule_worker.run_due_schedules()

    assert executed['count'] == 1