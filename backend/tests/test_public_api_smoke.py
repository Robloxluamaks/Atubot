import os

import requests


# Public deployment smoke tests (real preview URL, no credentialed success flow)
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')


def test_base_url_present():
    assert BASE_URL, 'REACT_APP_BACKEND_URL is required for public smoke tests.'


def test_public_health_endpoint_ok():
    response = requests.get(f'{BASE_URL}/api/health', timeout=15)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['service'] == 'relay'


def test_public_connect_malformed_token_422_sanitized():
    bad_token = 'bad token ###'
    response = requests.post(f'{BASE_URL}/api/bot/connect', json={'token': bad_token}, timeout=15)
    assert response.status_code == 422
    data = response.json()
    assert data['detail'] == 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).'
    assert bad_token not in str(data)


def test_public_connect_invalid_token_401_discord_rejection():
    response = requests.post(
        f'{BASE_URL}/api/bot/connect',
        json={'token': 'A23456789012345678901234567890'},
        timeout=20,
    )
    assert response.status_code == 401
    data = response.json()
    assert 'token bota' in data.get('detail', '').lower()
