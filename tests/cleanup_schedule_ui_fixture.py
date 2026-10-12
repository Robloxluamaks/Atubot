"""Revoke only the test-created workspace and erase its temporary cookie file."""
import hashlib
import hmac
import json
import os
from pathlib import Path

from dotenv import dotenv_values
from pymongo import MongoClient

cfg = {**dotenv_values('/app/backend/.env'), **os.environ}
paths = [Path('/tmp/relay_test_artifacts/schedule_ui_fixture.json'),
         Path('/app/test_reports/artifacts_iteration_3/schedule_ui_fixture.json')]

for fixture_path in paths:
    if not fixture_path.exists():
        continue
    fixture = json.loads(fixture_path.read_text(encoding='utf-8'))
    with MongoClient(cfg['MONGO_URL']) as client:
        db = client[cfg['DB_NAME']]
        raw = fixture.get('cookie_value')
        if raw:
            digest = hmac.new(bytes.fromhex(cfg['SESSION_HASH_KEY']), raw.encode(), hashlib.sha256).hexdigest()
            session = db.sessions.find_one({'token_hash': digest}, {'_id': 0, 'id': 1})
            if session:
                for collection in ['schedules', 'templates', 'groups']:
                    db[collection].delete_many({'owner_id': session['id']})
                db.sessions.delete_one({'id': session['id']})
        if fixture.get('schedule_id'):
            db.schedules.delete_one({'id': fixture['schedule_id']})
    fixture_path.unlink()
print('Test workspace revoked; temporary credential artifact removed.')