import base64, hashlib, hmac, os
from itsdangerous import URLSafeTimedSerializer

SECRET = os.getenv("REVIEWER_SECRET", "change-this-secret-in-production")
serializer = URLSafeTimedSerializer(SECRET)

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    return base64.b64encode(salt + digest).decode()

def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored.encode())
        salt, digest = raw[:16], raw[16:]
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
        return hmac.compare_digest(digest, check)
    except Exception:
        return False

def make_token(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})

def read_token(token: str) -> int | None:
    try:
        return int(serializer.loads(token, max_age=60 * 60 * 24 * 7)["user_id"])
    except Exception:
        return None
