"""Live SEC-001 verification tests against the preview URL."""
import os
import uuid
import time
import requests
import pytest

BASE = "https://auto-msg-bot-3.preview.emergentagent.com"
ORIGIN = "https://auto-msg-bot-3.preview.emergentagent.com"
DUMMY_TOKEN_30 = "A" * 30
DUMMY_TOKEN_VALID_FMT = "A23456789012345678901234567890"  # 30-char plausible
CHANNEL_ID = "12345678901234567"


def _assert_token_not_in_body(resp, token):
    assert token not in resp.text, f"Token leaked in response body: {resp.text[:200]}"


# ---------- No Origin / No session gating ----------
class TestRouteGating:
    def test_bot_connect_no_origin_403(self):
        r = requests.post(f"{BASE}/api/bot/connect", json={"token": DUMMY_TOKEN_30})
        assert r.status_code == 403
        _assert_token_not_in_body(r, DUMMY_TOKEN_30)

    def test_bot_connect_origin_no_cookie_401(self):
        r = requests.post(f"{BASE}/api/bot/connect",
                          json={"token": DUMMY_TOKEN_30},
                          headers={"Origin": ORIGIN})
        assert r.status_code == 401
        assert "Przestrzeń wygasła" in r.text
        _assert_token_not_in_body(r, DUMMY_TOKEN_30)

    def test_channels_resolve_no_origin_403(self):
        r = requests.post(f"{BASE}/api/channels/resolve",
                          json={"token": DUMMY_TOKEN_30, "channel_id": CHANNEL_ID})
        assert r.status_code == 403
        _assert_token_not_in_body(r, DUMMY_TOKEN_30)

    def test_channels_resolve_origin_no_cookie_401(self):
        r = requests.post(f"{BASE}/api/channels/resolve",
                          json={"token": DUMMY_TOKEN_30, "channel_id": CHANNEL_ID},
                          headers={"Origin": ORIGIN})
        assert r.status_code == 401
        assert "Przestrzeń wygasła" in r.text

    def test_messages_send_no_origin_403(self):
        r = requests.post(f"{BASE}/api/messages/send",
                          json={"token": DUMMY_TOKEN_30, "channel_ids": [CHANNEL_ID],
                                "content": "x", "request_id": str(uuid.uuid4())})
        assert r.status_code == 403
        _assert_token_not_in_body(r, DUMMY_TOKEN_30)

    def test_messages_send_origin_no_cookie_401(self):
        r = requests.post(f"{BASE}/api/messages/send",
                          json={"token": DUMMY_TOKEN_30, "channel_ids": [CHANNEL_ID],
                                "content": "x", "request_id": str(uuid.uuid4())},
                          headers={"Origin": ORIGIN})
        assert r.status_code == 401
        assert "Przestrzeń wygasła" in r.text


# ---------- Authenticated path ----------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE}/api/workspace/session", json={}, headers={"Origin": ORIGIN})
    assert r.status_code == 200, f"session create failed: {r.status_code} {r.text}"
    # cookie should be set
    assert any("relay_workspace" in c.name for c in s.cookies), f"cookies={s.cookies}"
    return s


class TestAuthenticatedPath:
    def test_connect_invalid_token_discord_401(self, session):
        r = session.post(f"{BASE}/api/bot/connect",
                         json={"token": DUMMY_TOKEN_VALID_FMT},
                         headers={"Origin": ORIGIN})
        assert r.status_code == 401
        assert "token bota" in r.text
        assert "Przestrzeń wygasła" not in r.text
        _assert_token_not_in_body(r, DUMMY_TOKEN_VALID_FMT)

    def test_connect_malformed_token_422(self, session):
        bad = "bad token ###"
        r = session.post(f"{BASE}/api/bot/connect",
                         json={"token": bad},
                         headers={"Origin": ORIGIN})
        assert r.status_code == 422
        assert "Sprawdź token" in r.text
        _assert_token_not_in_body(r, bad)


# ---------- Security headers ----------
class TestSecurityHeaders:
    def test_health_security_headers(self):
        r = requests.get(f"{BASE}/api/health")
        assert r.status_code == 200
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-frame-options") == "DENY"
        assert "frame-ancestors 'none'" in h.get("content-security-policy", "")
        assert h.get("referrer-policy") == "no-referrer"
        assert h.get("strict-transport-security", "").startswith("max-age=")
        assert "no-store" in h.get("cache-control", "")
        assert h.get("x-content-type-options") == "nosniff"


# ---------- Rate limit (run last; only one tight burst) ----------
class TestRateLimit:
    def test_connect_rate_limit_11th_429(self):
        # fresh session for isolation
        s = requests.Session()
        r = s.post(f"{BASE}/api/workspace/session", json={}, headers={"Origin": ORIGIN})
        assert r.status_code == 200
        statuses = []
        last = None
        for i in range(11):
            resp = s.post(f"{BASE}/api/bot/connect",
                          json={"token": DUMMY_TOKEN_30},
                          headers={"Origin": ORIGIN})
            statuses.append(resp.status_code)
            last = resp
        # First 10 should be 401 (invalid Discord token), 11th should be 429
        assert statuses[:10] == [401] * 10, f"expected 10x401, got {statuses}"
        assert last.status_code == 429, f"expected 429, got {last.status_code} body={last.text[:200]}"
        assert "Retry-After" in last.headers or "retry-after" in {k.lower() for k in last.headers}
        assert "Zbyt wiele prób" in last.text
