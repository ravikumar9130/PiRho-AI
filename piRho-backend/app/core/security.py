"""Security utilities for encryption, hashing, and JWT handling."""
import base64
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Generate bcrypt hash of password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


# JWT Token handling
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# API Key Encryption using Fernet (symmetric encryption)
class APIKeyEncryptor:
    """Encrypt/decrypt API keys using Fernet symmetric encryption."""
    
    def __init__(self):
        key = settings.ENCRYPTION_KEY
        # Fernet key must be 32 url-safe base64-encoded bytes (44 chars)
        if isinstance(key, str):
            key = key.encode()
        self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        return self._fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext."""
        return self._fernet.decrypt(ciphertext.encode()).decode()


# Lazy-loaded encryptor instance
_encryptor: Optional[APIKeyEncryptor] = None


def get_encryptor() -> APIKeyEncryptor:
    """Get or create the API key encryptor instance."""
    global _encryptor
    if _encryptor is None:
        _encryptor = APIKeyEncryptor()
    return _encryptor


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage."""
    return get_encryptor().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt a stored API key."""
    return get_encryptor().decrypt(encrypted_key)

