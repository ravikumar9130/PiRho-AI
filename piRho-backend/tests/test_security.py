"""Tests for security utilities."""
import pytest
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    encrypt_api_key, decrypt_api_key
)


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "SecurePassword123!"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = get_password_hash("Password1")
        hash2 = get_password_hash("Password2")
        
        assert hash1 != hash2


class TestJWTTokens:
    """Test JWT token functions."""

    def test_create_and_decode_access_token(self):
        """Test access token creation and decoding."""
        data = {"sub": "user-123", "email": "test@example.com"}
        token = create_access_token(data)
        
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["email"] == "test@example.com"
        assert decoded["type"] == "access"

    def test_create_and_decode_refresh_token(self):
        """Test refresh token creation and decoding."""
        data = {"sub": "user-123"}
        token = create_refresh_token(data)
        
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["sub"] == "user-123"
        assert decoded["type"] == "refresh"

    def test_invalid_token_returns_none(self):
        """Test that invalid tokens return None."""
        assert decode_token("invalid-token") is None
        assert decode_token("") is None

    def test_token_contains_expiry(self):
        """Test that tokens contain expiry claim."""
        token = create_access_token({"sub": "user-123"})
        decoded = decode_token(token)
        
        assert "exp" in decoded


class TestAPIKeyEncryption:
    """Test API key encryption functions."""

    def test_encrypt_and_decrypt(self):
        """Test encryption and decryption."""
        api_key = "my-secret-api-key-12345"
        encrypted = encrypt_api_key(api_key)
        
        assert encrypted != api_key
        assert decrypt_api_key(encrypted) == api_key

    def test_different_keys_different_ciphertext(self):
        """Test that encrypting same key twice produces different ciphertext."""
        api_key = "my-secret-api-key"
        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)
        
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2
        # But both should decrypt to same value
        assert decrypt_api_key(encrypted1) == decrypt_api_key(encrypted2)

