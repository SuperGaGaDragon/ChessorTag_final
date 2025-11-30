from datetime import datetime, timedelta
import os
import jwt
import bcrypt  # 直接用 bcrypt，而不是 passlib

# ---- JWT 配置 ----
SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("AUTH_SECRET_KEY") or "DEV_ONLY_SECRET_KEY"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 天

# ---- 密码工具 ----


def _normalize_password(password: str) -> bytes:
    """
    bcrypt 只使用前 72 bytes，这里统一截断，并返回 bytes。
    """
    if password is None:
        password = ""
    pw_bytes = password.encode("utf-8")
    if len(pw_bytes) > 72:
        pw_bytes = pw_bytes[:72]
    return pw_bytes


def hash_password(password: str) -> str:
    pw_bytes = _normalize_password(password)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pw_bytes, salt)
    # 存 DB 时用 str
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = _normalize_password(plain_password)
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


# ---- JWT 生成 ----


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    # pyjwt 在新版本里已经默认返回 str，这里保险一下
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token
