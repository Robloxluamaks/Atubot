import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import requests
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from pymongo import MongoClient


def _clean(value):
    if value is None:
        return None
    return str(value).strip().strip('"').strip("'")


cfg = {
    **{k: _clean(v) for k, v in dotenv_values('/app/backend/.env').items()},
    **{k: _clean(v) for k, v in dotenv_values('/app/frontend/.env').items()},
    **{k: _clean(v) for k, v in os.environ.items()},
}

base_url = cfg.get('REACT_APP_BACKEND_URL')
app_origin = cfg.get('APP_ORIGIN')
mongo_url = cfg.get('MONGO_URL')
db_name = cfg.get('DB_NAME')
session_hash_key = cfg.get('SESSION_HASH_KEY')
fernet_key = cfg.get('FERNET_KEY')

required = {
    'REACT_APP_BACKEND_URL': base_url,
    'APP_ORIGIN': app_origin,
    'MONGO_URL': mongo_url,
    'DB_NAME': db_name,
    'SESSION_HASH_KEY': session_hash_key,
    'FERNET_KEY': fernet_key,
}
missing = [k for k, v in required.items() if not v]
if missing:
    raise RuntimeError(f'Missing required env keys: {missing}')

session = requests.Session()
response = session.post(
    f'{base_url}/api/workspace/session',
    json={},
    headers={'Origin': app_origin, 'Content-Type': 'application/json'},
    timeout=20,
)
if response.status_code != 200:
    raise RuntimeError(f'Workspace session establish failed: {response.status_code}')

raw_cookie = session.cookies.get('__Host-relay_workspace')
if not raw_cookie:
    raise RuntimeError('Workspace cookie not set in session response.')

token_hash = hmac.new(bytes.fromhex(session_hash_key), raw_cookie.encode(), hashlib.sha256).hexdigest()

client = MongoClient(mongo_url, tz_aware=True)
db = client[db_name]
session_doc = db.sessions.find_one({'token_hash': token_hash}, {'_id': 0, 'id': 1, 'expires_at': 1})
if not session_doc:
    client.close()
    raise RuntimeError('Failed to resolve owner session from cookie hash.')

schedule_id = f'ui-test-{uuid4().hex[:10]}'
now = datetime.now(timezone.utc)
payload = {
    'id': schedule_id,
    'owner_id': session_doc['id'],
    'name': f'TEST_UI_{schedule_id[-6:]}',
    'bot_name': 'RelayBot',
    'channel_ids': ['123456789012345678'],
    'content': 'TEST schedule UI fixture',
    'embed': None,
    'overrides': {},
    'next_run': now + timedelta(hours=2),
    'interval_minutes': 15,
    'max_runs': 10,
    'run_count': 0,
    'state': 'paused',
    'created_at': now,
    'expires_at': session_doc['expires_at'],
    'last_run': None,
    'last_error': None,
    'last_results': [],
    'token_ciphertext': Fernet(fernet_key).encrypt(b'A23456789012345678901234567890').decode(),
}
db.schedules.insert_one(payload)
client.close()

out_dir = Path('/tmp/relay_test_artifacts')
out_dir.mkdir(parents=True, exist_ok=True)
out_dir.chmod(0o700)
out_file = out_dir / 'schedule_ui_fixture.json'
out_file.write_text(
    json.dumps(
        {
            'base_url': base_url,
            'app_origin': app_origin,
            'cookie_name': '__Host-relay_workspace',
            'cookie_value': raw_cookie,
            'schedule_id': schedule_id,
        }
    ),
    encoding='utf-8',
)
out_file.chmod(0o600)

print(str(out_file))