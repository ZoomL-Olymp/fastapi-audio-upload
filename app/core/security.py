from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import jwt, JWTError
from passlib.context import CryptContext # keep for potential future password use

from app.core.config import settings
from app.schemas.token import TokenPayload

def create_access_token(subject: Union[str, Any], expires_delta: timedelta | None = None, yandex_id: str | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "exp": expire,
        "sub": str(subject), # User ID from our DB
        "refresh": False, # access token
        "yandex_id": yandex_id
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta | None = None, yandex_id: str | None = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "exp": expire,
        "sub": str(subject), # User ID from our DB
        "refresh": True, # refresh token
        "yandex_id": yandex_id
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        # check for specific payload structure
        token_data = TokenPayload(
            sub=payload.get("sub"),
            refresh=payload.get("refresh", False),
            yandex_id=payload.get("yandex_id")
            )
        return token_data
    except JWTError:
        return None # token is invalid or expired