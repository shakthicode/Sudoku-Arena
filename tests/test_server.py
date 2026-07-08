"""
Suduku-Arena – Server Tests
============================
Run from the project root:
    python -m pytest tests/ -v

Tests cover:
  - UUID validation helper
  - Password hashing / verification
  - Auth register / login (via live server)
  - UUID injection guard on mutating endpoints

"""

import base64
import json
import sys
import os
import threading
import time
import uuid
import urllib.request
import urllib.error

# ── Make sure the backend package is importable ────────────────────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Isolated test server on a different port ───────────────────────────────────
TEST_PORT   = 18888
BASE_URL    = f"http://127.0.0.1:{TEST_PORT}"
_server_ref = None


def _start_test_server():
    """Spin up a real SudokuHandler server on TEST_PORT in a daemon thread."""
    import backend.server as srv_mod
    import tempfile

    # Override dirs to a temp location so tests don't pollute real data
    tmp = tempfile.mkdtemp(prefix="sudoku_test_")
    srv_mod.DATA_DIR         = tmp
    srv_mod.USERS_DIR        = os.path.join(tmp, "users")
    srv_mod.GAMES_DIR        = os.path.join(tmp, "games")
    srv_mod.LEADERBOARD_FILE = os.path.join(tmp, "leaderboard.json")
    os.makedirs(srv_mod.USERS_DIR, exist_ok=True)
    os.makedirs(srv_mod.GAMES_DIR, exist_ok=True)


    from http.server import HTTPServer
    server = HTTPServer(("127.0.0.1", TEST_PORT), srv_mod.SudokuHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.4)
    return server


def _request(method, path, body=None, headers=None):
    """Helper: make an HTTP request, return (status, parsed_json)."""
    url  = BASE_URL + path
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ══════════════════════════════════════════════════════════════════════════════
# Unit tests — no network needed
# ══════════════════════════════════════════════════════════════════════════════

def test_is_valid_uuid_accepts_valid():
    from backend.server import is_valid_uuid
    assert is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
    assert is_valid_uuid(str(uuid.uuid4()))


def test_is_valid_uuid_rejects_traversal():
    from backend.server import is_valid_uuid
    assert not is_valid_uuid("../../../etc/passwd")
    assert not is_valid_uuid("..\\..\\users\\admin")
    assert not is_valid_uuid("")
    assert not is_valid_uuid(None)
    assert not is_valid_uuid("not-a-uuid")
    assert not is_valid_uuid(123)


def test_is_valid_uuid_rejects_short_uuid():
    from backend.server import is_valid_uuid
    assert not is_valid_uuid("550e8400-e29b-41d4-a716")   # truncated


def test_hash_and_verify_password():
    from backend.server import hash_password, verify_password
    pw     = "MyS3cretPass!"
    hashed = hash_password(pw)
    assert verify_password(pw, hashed)
    assert not verify_password("wrong", hashed)


def test_hash_and_verify_sha256_legacy():
    """Legacy SHA-256 hashes (pre-bcrypt) must still verify correctly."""
    import hashlib
    from backend.server import verify_password
    pw       = "oldpassword"
    sha_hash = hashlib.sha256(pw.encode()).hexdigest()
    assert verify_password(pw, sha_hash)
    assert not verify_password("notright", sha_hash)


# ══════════════════════════════════════════════════════════════════════════════
# Integration tests — spin up a live server
# ══════════════════════════════════════════════════════════════════════════════

def setup_module(module):
    global _server_ref
    _server_ref = _start_test_server()


def teardown_module(module):
    if _server_ref:
        _server_ref.shutdown()


# ── Registration & Login ───────────────────────────────────────────────────────

def test_register_success():
    status, data = _request("POST", "/api/auth/register", {
        "username": "tester01",
        "email":    "tester01@example.com",
        "password": "pass123",
        "avatar":   "🤖",
    })
    assert status == 201, data
    assert "user" in data
    assert "password_hash" not in data["user"]


def test_register_duplicate_email():
    _request("POST", "/api/auth/register", {
        "username": "dup_user",
        "email":    "dup@example.com",
        "password": "pass123",
    })
    status, data = _request("POST", "/api/auth/register", {
        "username": "dup_user2",
        "email":    "dup@example.com",
        "password": "pass123",
    })
    assert status == 409, data


def test_register_short_password():
    status, _ = _request("POST", "/api/auth/register", {
        "username": "shortpw",
        "email":    "shortpw@example.com",
        "password": "abc",
    })
    assert status == 400


def test_login_success():
    _request("POST", "/api/auth/register", {
        "username": "loginuser",
        "email":    "loginuser@example.com",
        "password": "secure99",
    })
    status, data = _request("POST", "/api/auth/login", {
        "email":    "loginuser@example.com",
        "password": "secure99",
    })
    assert status == 200, data
    assert "token" in data["user"]


def test_login_wrong_password():
    status, _ = _request("POST", "/api/auth/login", {
        "email":    "loginuser@example.com",
        "password": "wrongpass",
    })
    assert status == 401


def test_progress_save_and_load():
    _request("POST", "/api/auth/register", {
        "username": "progressuser",
        "email":    "progressuser@example.com",
        "password": "pass123",
    })
    status, login_data = _request("POST", "/api/auth/login", {
        "email":    "progressuser@example.com",
        "password": "pass123",
    })
    assert status == 200, login_data
    user_id = login_data["user"]["id"]
    token = login_data["user"]["token"]

    payload = {
        "userId": user_id,
        "campaignProgress": {"Easy": 3},
        "resumeProgress": {
            "difficulty": "Easy",
            "campaignPhase": "Easy",
            "campaignRound": 2,
            "isBoss": False,
        },
    }
    status, saved = _request("POST", "/api/progress/save", payload,
                             headers={"Authorization": f"Bearer {token}"})
    assert status == 200, saved

    status, loaded = _request("GET", f"/api/progress?userId={user_id}",
                              headers={"Authorization": f"Bearer {token}"})
    assert status == 200, loaded
    assert loaded["progress"]["campaignProgress"]["Easy"] == 3
    assert loaded["progress"]["resumeProgress"]["campaignRound"] == 2


# ── UUID injection guard on mutating endpoints ─────────────────────────────────

def test_update_user_rejects_traversal_id():
    status, _ = _request("POST", "/api/users/update", {
        "id":       "../../../etc/passwd",
        "username": "hacker",
    })
    assert status == 400


def test_save_game_rejects_traversal_id():
    status, _ = _request("POST", "/api/games/save", {
        "userId":     "../../sensitive",
        "difficulty": "Easy",
    })
    assert status == 400


def test_leaderboard_update_rejects_traversal_id():
    status, _ = _request("POST", "/api/leaderboard/update", {
        "id":    "not-a-uuid",
        "score": 9999,
    })
    assert status == 400


def test_get_games_rejects_traversal_userid():
    status, _ = _request("GET", "/api/games?userId=../../../etc/passwd")
    assert status == 400





if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
