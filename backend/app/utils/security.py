from __future__ import annotations
import base64, hashlib, hmac, re, secrets

def hash_password(raw: str) -> str:
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(raw.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return "scrypt$16384$8$1$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(key).decode()

def verify_password(raw: str, stored: str) -> bool:
    try:
        scheme, n, r, p, salt_b64, key_b64 = stored.split("$", 5)
        if scheme != "scrypt":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode())
        expected = base64.urlsafe_b64decode(key_b64.encode())
        actual = hashlib.scrypt(raw.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False

def random_token(bytes_len: int = 32) -> str:
    return secrets.token_urlsafe(bytes_len)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))
