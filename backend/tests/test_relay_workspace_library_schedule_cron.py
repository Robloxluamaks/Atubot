import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import requests
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from pymongo import MongoClient


# External preview integration tests for workspace/library/schedule/cron flows
def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


_cfg = {
    **{k: _clean(v) for k, v in dotenv_values('/app/backend/.env').items()},
    **{k: _clean(v) for k, v in dotenv_values('/app/frontend/.env').items()},
    **{k: _clean(v) for k, v in os.environ.items()},
}

BASE_URL = _cfg.get('REACT_APP_BACKEND_URL')
APP_ORIGIN = _cfg.get('APP_ORIGIN')
MONGO_URL = _cfg.get('MONGO_URL')
DB_NAME = _cfg.get('DB_NAME')
SESSION_HASH_KEY = _cfg.get('SESSION_HASH_KEY')
FERNET_KEY = _cfg.get('FERNET_KEY')
WEBHOOK_CRON_SECRET = _cfg.get('WEBHOOK_CRON_SECRET')
COOKIE = '__Host-relay_workspace'


def _assert_required_env():
    assert BASE_URL, 'REACT_APP_BACKEND_URL is required.'
    assert APP_ORIGIN, 'APP_ORIGIN is required.'
    assert MONGO_URL, 'MONGO_URL is required.'
    assert DB_NAME, 'DB_NAME is required.'
    assert SESSION_HASH_KEY, 'SESSION_HASH_KEY is required.'
    assert FERNET_KEY, 'FERNET_KEY is required.'
    assert WEBHOOK_CRON_SECRET, 'WEBHOOK_CRON_SECRET is required.'


def _db():
    client = MongoClient(MONGO_URL, tz_aware=True)
    return client, client[DB_NAME]


def _origin_headers():
    return {'Origin': APP_ORIGIN, 'Content-Type': 'application/json'}


def _workspace_session(http: requests.Session):
    response = http.post(f'{BASE_URL}/api/workspace/session', json={}, headers=_origin_headers(), timeout=20)
    assert response.status_code == 200
    body = response.json()
    assert body['ready'] is True
    assert 'expires_at' in body
    return response


def _set_cookie_headers(response: requests.Response) -> list[str]:
    raw_headers = getattr(response.raw, 'headers', None)
    if raw_headers is not None and hasattr(raw_headers, 'getlist'):
        return raw_headers.getlist('Set-Cookie')
    header = response.headers.get('set-cookie')
    return [header] if header else []


def _workspace_cookie_header(response: requests.Response) -> str:
    for header in _set_cookie_headers(response):
        if header and header.strip().startswith(f'{COOKIE}='):
            return header
    raise AssertionError(f'{COOKIE} header was not present in Set-Cookie headers.')


def _cookie_parts(cookie_header: str):
    parts = [p.strip() for p in cookie_header.split(';') if p.strip()]
    assert parts and parts[0].startswith(f'{COOKIE}='), f'Unexpected cookie header: {cookie_header}'
    attrs = {}
    flags = set()
    for part in parts[1:]:
        if '=' in part:
            key, value = part.split('=', 1)
            attrs[key.lower()] = value
        else:
            flags.add(part.lower())
    return attrs, flags


def _owner(http: requests.Session):
    raw_cookie = http.cookies.get(COOKIE)
    assert raw_cookie, 'Workspace cookie was not set.'
    token_hash = hmac.new(bytes.fromhex(SESSION_HASH_KEY), raw_cookie.encode(), hashlib.sha256).hexdigest()
    client, db = _db()
    try:
        session_doc = db.sessions.find_one({'token_hash': token_hash}, {'_id': 0, 'id': 1, 'expires_at': 1})
        assert session_doc and session_doc.get('id')
        return session_doc
    finally:
        client.close()


def _seed_schedule(owner_id: str, expires_at: datetime, token: str):
    now = datetime.now(timezone.utc)
    schedule_id = str(uuid4())
    payload = {
        'id': schedule_id,
        'owner_id': owner_id,
        'name': f'TEST_seed_{schedule_id[:8]}',
        'bot_name': 'RelayBot',
        'channel_ids': ['123456789012345678'],
        'content': 'TEST seeded schedule',
        'embed': None,
        'overrides': {},
        'next_run': now - timedelta(minutes=1),
        'interval_minutes': 0,
        'max_runs': 1,
        'run_count': 0,
        'state': 'active',
        'created_at': now,
        'expires_at': expires_at,
        'last_run': None,
        'last_error': None,
        'last_results': [],
        'token_ciphertext': Fernet(FERNET_KEY).encrypt(token.encode()).decode(),
    }
    client, db = _db()
    try:
        db.schedules.insert_one(payload)
    finally:
        client.close()
    return schedule_id


def _delete_schedule(schedule_id: str):
    client, db = _db()
    try:
        db.schedules.delete_one({'id': schedule_id})
    finally:
        client.close()


def test_workspace_session_cookie_flags_and_reload_persistence():
    _assert_required_env()
    http = requests.Session()
    response = _workspace_session(http)

    cookie_header = _workspace_cookie_header(response)
    attrs, flags = _cookie_parts(cookie_header)

    assert 'httponly' in flags
    assert 'secure' in flags
    assert attrs.get('path') == '/'
    assert 'domain' not in attrs

    host = (urlparse(BASE_URL).hostname or '').lower()
    is_preview_host = host == 'preview.emergentagent.com' or host.endswith('.preview.emergentagent.com')
    same_site = (attrs.get('samesite') or '').lower()
    has_partitioned = 'partitioned' in flags
    if is_preview_host and same_site == 'none':
        assert has_partitioned, 'Preview rewrite acceptance requires SameSite=None with Partitioned.'
    else:
        assert same_site == 'lax', f'Expected SameSite=Lax outside preview rewrite case, got {same_site!r}.'

    reload_response = _workspace_session(http)
    assert reload_response.status_code == 200
    templates = http.get(f'{BASE_URL}/api/library/templates', timeout=20)
    assert templates.status_code == 200
    assert isinstance(templates.json(), list)


def test_workspace_origin_enforcement_and_missing_cookie_unauthorized():
    _assert_required_env()

    no_origin = requests.post(f'{BASE_URL}/api/workspace/session', json={}, timeout=20)
    assert no_origin.status_code == 403

    bad_origin = requests.post(
        f'{BASE_URL}/api/workspace/session',
        json={},
        headers={'Origin': 'https://evil.example'},
        timeout=20,
    )
    assert bad_origin.status_code == 403

    no_cookie = requests.get(f'{BASE_URL}/api/library/templates', timeout=20)
    assert no_cookie.status_code == 401


def test_cookie_auth_mutations_reject_missing_null_and_foreign_origin():
    _assert_required_env()
    http = requests.Session()
    _workspace_session(http)

    template_payload = {
        'name': 'TEST_origin_enforcement',
        'content': 'Treść',
        'embed': None,
        'overrides': {},
    }
    template_update_payload = {
        'name': 'TEST_origin_enforcement_update',
        'content': 'Treść 2',
        'embed': None,
        'overrides': {},
    }

    cases = [
        ('missing', {}),
        ('null', {'Origin': 'null'}),
        ('foreign', {'Origin': 'https://evil.example'}),
    ]

    for label, headers in cases:
        post_template = http.post(f'{BASE_URL}/api/library/templates', json=template_payload, headers=headers, timeout=20)
        assert post_template.status_code == 403, f'POST should reject {label} origin'

        put_template = http.put(
            f'{BASE_URL}/api/library/templates/non-existent-id',
            json=template_update_payload,
            headers=headers,
            timeout=20,
        )
        assert put_template.status_code == 403, f'PUT should reject {label} origin'

        patch_schedule = http.patch(
            f'{BASE_URL}/api/schedules/non-existent-id',
            json={'action': 'pause'},
            headers=headers,
            timeout=20,
        )
        assert patch_schedule.status_code == 403, f'PATCH should reject {label} origin'

        delete_schedule = http.delete(
            f'{BASE_URL}/api/schedules/non-existent-id',
            headers=headers,
            timeout=20,
        )
        assert delete_schedule.status_code == 403, f'DELETE should reject {label} origin'


def test_templates_and_groups_crud_with_owner_isolation():
    _assert_required_env()
    s1 = requests.Session()
    s2 = requests.Session()
    _workspace_session(s1)
    _workspace_session(s2)

    template_payload = {
        'name': 'TEST_template_emoji',
        'content': 'Hej społeczności 👋 **aktualizacja**',
        'embed': {
            'title': 'Nowości',
            'description': 'Szczegóły i link',
            'color': 7636982,
            'url': 'https://example.com/news',
            'footer': 'Stopka',
        },
        'overrides': {},
    }
    created_template = s1.post(f'{BASE_URL}/api/library/templates', json=template_payload, headers=_origin_headers(), timeout=20)
    assert created_template.status_code == 200
    template_id = created_template.json()['id']

    bad_template = s1.post(
        f'{BASE_URL}/api/library/templates',
        json={'name': '   ', 'content': '', 'embed': None, 'overrides': {}},
        headers=_origin_headers(),
        timeout=20,
    )
    assert bad_template.status_code == 422

    list_s1 = s1.get(f'{BASE_URL}/api/library/templates', timeout=20)
    assert list_s1.status_code == 200
    assert any(item['id'] == template_id for item in list_s1.json())

    list_s2 = s2.get(f'{BASE_URL}/api/library/templates', timeout=20)
    assert list_s2.status_code == 200
    assert all(item['id'] != template_id for item in list_s2.json())

    foreign_update = s2.put(
        f'{BASE_URL}/api/library/templates/{template_id}',
        json={**template_payload, 'name': 'TEST_foreign_edit'},
        headers=_origin_headers(),
        timeout=20,
    )
    assert foreign_update.status_code == 404

    group_payload = {
        'name': 'TEST_group',
        'channels': [
            {'id': '123456789012345678', 'name': 'kanał-5678'},
            {'id': '123456789012345679', 'name': 'kanał-5679'},
        ],
    }
    created_group = s1.post(f'{BASE_URL}/api/library/groups', json=group_payload, headers=_origin_headers(), timeout=20)
    assert created_group.status_code == 200
    group_id = created_group.json()['id']

    duplicate_group = s1.post(
        f'{BASE_URL}/api/library/groups',
        json={
            'name': 'TEST_dupes',
            'channels': [
                {'id': '123456789012345678', 'name': 'a'},
                {'id': '123456789012345678', 'name': 'b'},
            ],
        },
        headers=_origin_headers(),
        timeout=20,
    )
    assert duplicate_group.status_code == 422

    remove_template = s1.delete(f'{BASE_URL}/api/library/templates/{template_id}', headers={'Origin': APP_ORIGIN}, timeout=20)
    assert remove_template.status_code == 200
    assert remove_template.json()['deleted'] is True

    remove_group = s1.delete(f'{BASE_URL}/api/library/groups/{group_id}', headers={'Origin': APP_ORIGIN}, timeout=20)
    assert remove_group.status_code == 200
    assert remove_group.json()['deleted'] is True


def test_schedule_visibility_isolation_and_hidden_token_fields():
    _assert_required_env()
    s1 = requests.Session()
    s2 = requests.Session()
    _workspace_session(s1)
    _workspace_session(s2)
    owner1 = _owner(s1)

    schedule_id = _seed_schedule(owner1['id'], owner1['expires_at'], token='A23456789012345678901234567890')
    try:
        mine = s1.get(f'{BASE_URL}/api/schedules', timeout=20)
        assert mine.status_code == 200
        matched = [item for item in mine.json() if item['id'] == schedule_id]
        assert matched
        assert 'token_ciphertext' not in matched[0]
        assert 'owner_id' not in matched[0]

        foreign_patch = s2.patch(
            f'{BASE_URL}/api/schedules/{schedule_id}',
            json={'action': 'pause'},
            headers=_origin_headers(),
            timeout=20,
        )
        assert foreign_patch.status_code == 404

        foreign_delete = s2.delete(f'{BASE_URL}/api/schedules/{schedule_id}', headers={'Origin': APP_ORIGIN}, timeout=20)
        assert foreign_delete.status_code == 404
    finally:
        _delete_schedule(schedule_id)


def test_workspace_delete_cascades_data_and_invalidates_cookie():
    _assert_required_env()
    http = requests.Session()
    _workspace_session(http)
    session_doc = _owner(http)

    template = http.post(
        f'{BASE_URL}/api/library/templates',
        json={'name': 'TEST_to_delete', 'content': 'X', 'embed': None, 'overrides': {}},
        headers=_origin_headers(),
        timeout=20,
    )
    assert template.status_code == 200

    group = http.post(
        f'{BASE_URL}/api/library/groups',
        json={'name': 'TEST_to_delete', 'channels': [{'id': '123456789012345678', 'name': 'kanał-5678'}]},
        headers=_origin_headers(),
        timeout=20,
    )
    assert group.status_code == 200

    schedule_id = _seed_schedule(session_doc['id'], session_doc['expires_at'], token='A23456789012345678901234567890')

    deleted = http.delete(f'{BASE_URL}/api/workspace', headers={'Origin': APP_ORIGIN}, timeout=20)
    assert deleted.status_code == 200
    assert deleted.json()['deleted'] is True

    list_after_delete = http.get(f'{BASE_URL}/api/library/templates', timeout=20)
    assert list_after_delete.status_code == 401

    client, db = _db()
    try:
        assert db.templates.count_documents({'owner_id': session_doc['id']}) == 0
        assert db.groups.count_documents({'owner_id': session_doc['id']}) == 0
        assert db.schedules.count_documents({'owner_id': session_doc['id']}) == 0
        assert db.sessions.count_documents({'id': session_doc['id']}) == 0
    finally:
        client.close()
        _delete_schedule(schedule_id)


def test_cron_dispatch_auth_validation_and_duplicate_idempotency():
    _assert_required_env()
    run_id = f'test-run-{uuid4()}'
    payload = {
        'event': 'schedule.triggered',
        'schedule_id': 'relay-dispatch',
        'run_id': run_id,
        'dispatch_time': datetime.now(timezone.utc).isoformat(),
        'data': None,
    }

    unauthorized = requests.post(f'{BASE_URL}/api/cron/dispatch', json=payload, timeout=20)
    assert unauthorized.status_code == 401

    malformed = requests.post(
        f'{BASE_URL}/api/cron/dispatch',
        json={'event': 'bad'},
        headers={'Authorization': f'Bearer {WEBHOOK_CRON_SECRET}'},
        timeout=20,
    )
    assert malformed.status_code == 400

    headers = {
        'Authorization': f'Bearer {WEBHOOK_CRON_SECRET}',
        'x-webhook-id': run_id,
        'Content-Type': 'application/json',
    }
    first = requests.post(f'{BASE_URL}/api/cron/dispatch', json=payload, headers=headers, timeout=20)
    assert first.status_code == 200
    assert first.json() == {'accepted': True, 'duplicate': False}

    second = requests.post(f'{BASE_URL}/api/cron/dispatch', json=payload, headers=headers, timeout=20)
    assert second.status_code == 200
    assert second.json() == {'accepted': True, 'duplicate': True}


def test_cron_dispatch_executes_due_invalid_token_job_and_erases_ciphertext_on_401():
    _assert_required_env()
    workspace = requests.Session()
    _workspace_session(workspace)
    session_doc = _owner(workspace)

    fixture_id = _seed_schedule(session_doc['id'], session_doc['expires_at'], token='A23456789012345678901234567890')
    run_id = f'test-worker-{uuid4()}'
    payload = {
        'event': 'schedule.triggered',
        'schedule_id': 'relay-dispatch',
        'run_id': run_id,
        'dispatch_time': datetime.now(timezone.utc).isoformat(),
        'data': None,
    }
    headers = {
        'Authorization': f'Bearer {WEBHOOK_CRON_SECRET}',
        'x-webhook-id': run_id,
        'Content-Type': 'application/json',
    }

    try:
        response = requests.post(f'{BASE_URL}/api/cron/dispatch', json=payload, headers=headers, timeout=20)
        assert response.status_code == 200
        assert response.json()['accepted'] is True

        client, db = _db()
        try:
            final = None
            for _ in range(25):
                final = db.schedules.find_one({'id': fixture_id}, {'_id': 0})
                if final and final.get('state') == 'error' and final.get('token_ciphertext') is None:
                    break
                time.sleep(1)

            assert final is not None
            assert final['state'] == 'error'
            assert final['token_ciphertext'] is None
            assert final.get('last_error')
        finally:
            client.close()
    finally:
        _delete_schedule(fixture_id)