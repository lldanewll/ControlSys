import os
from jose import JWTError, jwt
from typing import Optional
import logging
import uuid

logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", "eANno-EM-Li4tPzYFOLS-A9khJO-FhKjCZucrVFVyIo")
ALGORITHM = "HS256"

def get_token_payload(token: str) -> Optional[dict]:
    """Получает payload из JWT токена"""
    try:
        logger.info(f"Verifying token in Orders Service: {token[:50]}...")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        logger.info(f"Token payload in Orders Service: {payload}")
        
        if "sub" in payload:
            try:
                uuid.UUID(payload["sub"])
            except ValueError:
                logger.error(f"Invalid UUID format in token: {payload['sub']}")
                return None
                
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed in Orders Service: {str(e)}")
        return None