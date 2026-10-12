import os
from dotenv import dotenv_values

import requests


# Public deployment smoke tests (real preview URL, no credentialed success flow)
def _clean(value):
    if value is None:
        return None
    return str(value).strip().strip('"').strip("'")


_cfg = {
    **{k: _clean(v) for k, v in dotenv_values('/app/frontend/.env').items()},
    **{k: _clean(v) for k, v in dotenv_values('/app/backend/.env').items()},
    **{k: _clean(v) for k, v in os.environ.items()},
}

BASE_URL = _cfg.get('REACT_APP_BACKEND_URL')
APP_ORIGIN = _cfg.get('APP_ORIGIN')


def _workspace():
    http = requests.Session()
    http.headers.update({'Origin': APP_ORIGIN})
    response = http.post(f'{BASE_URL}/api/workspace/session', json={}, timeout=20)
    assert response.status_code == 200
    return http


def test_base_url_present():
    assert BASE_URL, 'REACT_APP_BACKEND_URL is required for public smoke tests.'
    assert APP_ORIGIN, 'APP_ORIGIN is required for public smoke tests.'


def test_public_health_endpoint_ok():
    response = requests.get(f'{BASE_URL}/api/health', timeout=15)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['service'] == 'relay'
    assert response.headers.get('X-Frame-Options') == 'DENY'
    assert response.headers.get('Referrer-Policy') == 'no-referrer'


def test_public_connect_without_session_rejected():
    no_origin = requests.post(f'{BASE_URL}/api/bot/connect', json={'token': 'A' * 30}, timeout=15)
    assert no_origin.status_code == 403
    no_cookie = requests.post(f'{BASE_URL}/api/bot/connect', json={'token': 'A' * 30},
                              headers={'Origin': APP_ORIGIN}, timeout=15)
    assert no_cookie.status_code == 401


def test_public_connect_malformed_token_422_sanitized():
    bad_token = 'bad token ###'
    response = _workspace().post(f'{BASE_URL}/api/bot/connect', json={'token': bad_token}, timeout=15)
    assert response.status_code == 422
    data = response.json()
    assert data['detail'] == 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).'
    assert bad_token not in str(data)


def test_public_connect_invalid_token_401_discord_rejection():
    response = _workspace().post(
        f'{BASE_URL}/api/bot/connect',
        json={'token': 'A23456789012345678901234567890'},
        timeout=20,
    )
    assert response.status_code == 401
    data = response.json()
    assert 'token bota' in data.get('detail', '').lower()
