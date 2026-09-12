import requests

BASE = "http://127.0.0.1:8000"
S = requests.Session()


def test(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")


def register():
    payload = {
        "username": "demo_user",
        "email": "demo@example.com",
        "password": "Password@123",
        "full_name": "Demo User",
    }
    r = S.post(f"{BASE}/api/auth/register", json=payload, timeout=10)
    assert r.status_code in (200, 201), r.text


def duplicate_register():
    payload = {
        "username": "demo_user",
        "email": "demo@example.com",
        "password": "Password@123",
        "full_name": "Demo User 2",
    }
    r = S.post(f"{BASE}/api/auth/register", json=payload, timeout=10)
    assert r.status_code == 409


def login_fail_then_ok():
    S.cookies.clear()
    r = S.post(f"{BASE}/api/auth/login", json={"identifier": "demo@example.com", "password": "wrong"}, timeout=10)
    assert r.status_code == 401
    r = S.post(f"{BASE}/api/auth/login", json={"identifier": "demo@example.com", "password": "Password@123"}, timeout=10)
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
