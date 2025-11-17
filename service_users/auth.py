from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "eANno-EM-Li4tPzYFOLS-A9khJO-FhKjCZucrVFVyIo")
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Создает JWT токен"""
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Проверяет JWT токен и возвращает payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_token_payload(token: str) -> Optional[dict]:
    """Получает payload из JWT токена"""
    try:
        logger.info(f"Verifying token in Users Service: {token[:50]}...")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        logger.info(f"Token payload in Users Service: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed in Users Service: {str(e)}")
        return None