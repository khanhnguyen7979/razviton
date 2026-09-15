import requests
import os
import sys
import uuid
import secrets

BASE = os.getenv("RAZVITON_TEST_BASE", "http://127.0.0.1:8000")
RUN_ID = uuid.uuid4().hex[:12]
USERNAME = "audit_" + RUN_ID
EMAIL = USERNAME + "@example.invalid"
FAILURES = 0
TEST_PASSWORD = secrets.token_urlsafe(24)
S = requests.Session()


def test(name, fn):
    global FAILURES
    try:
        fn()
        print(f"[PASS] {name}")
    except Exception as e:
        FAILURES += 1
        print(f"[FAIL] {name}: {type(e).__name__}")


def register():
    payload = {
        "username": USERNAME,
        "email": EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Demo User",
    }
    r = S.post(f"{BASE}/api/auth/register", json=payload, timeout=10)
    assert r.status_code in (200, 201), r.text


def duplicate_register():
    payload = {
        "username": USERNAME,
        "email": EMAIL,
        "password": TEST_PASSWORD,
        "full_name": "Demo User 2",
    }
    r = S.post(f"{BASE}/api/auth/register", json=payload, timeout=10)
    assert r.status_code == 409


def login_fail_then_ok():
    S.cookies.clear()
    r = S.post(f"{BASE}/api/auth/login", json={"identifier": EMAIL, "password": "wrong-but-valid-length"}, timeout=10)
    assert r.status_code == 401
    r = S.post(f"{BASE}/api/auth/login", json={"identifier": EMAIL, "password": TEST_PASSWORD}, timeout=10)
    assert r.status_code == 200


def me_and_logout():
    r = S.get(f"{BASE}/api/auth/me", timeout=10)
    assert r.status_code == 200
    r = S.post(f"{BASE}/api/auth/logout", json={"all_devices": False}, timeout=10)
    assert r.status_code == 200
    r = S.get(f"{BASE}/api/auth/me", timeout=10)
    assert r.status_code == 401


if __name__ == "__main__":
    test("register", register)
    test("duplicate register blocked", duplicate_register)
    test("login fail + success", login_fail_then_ok)
    test("me and logout", me_and_logout)
    sys.exit(1 if FAILURES else 0)
