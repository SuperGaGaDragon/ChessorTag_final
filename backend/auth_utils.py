import os
from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("AUTH_SECRET_KEY") or "SUPER_SECRET_KEY"  # Railway 里要设置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 天

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _normalize_password(password: str) -> str:
    """
    bcrypt 只支持前 72 bytes，我们统一在这里截断，避免 ValueError。
    """
    if password is None:
        return ""
    # 按字节长度截断到 72
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    return password_bytes.decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    pw = _normalize_password(password)
    return pwd_context.hash(pw)


def verify_password(plain: str, hashed: str) -> bool:
    pw = _normalize_password(plain)
    return pwd_context.verify(pw, hashed)


def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
