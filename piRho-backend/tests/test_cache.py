"""Tests for in-memory cache."""
import pytest
import time
from app.core.cache import InMemoryCache, RateLimiter


class TestInMemoryCache:
    """Test in-memory cache implementation."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        
        assert cache.get("key1") == "value1"

    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = InMemoryCache()
        
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        """Test that keys expire after TTL."""
        cache = InMemoryCache()
        cache.set("expiring", "value", ttl=1)
        
        assert cache.get("expiring") == "value"
        time.sleep(1.1)
        assert cache.get("expiring") is None

    def test_delete(self):
        """Test key deletion."""
        cache = InMemoryCache()
        cache.set("key", "value")
        
        assert cache.delete("key") is True
        assert cache.get("key") is None
        assert cache.delete("key") is False

    def test_clear(self):
        """Test clearing all cache."""
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = InMemoryCache()
        cache.set("permanent", "value")
        cache.set("expiring1", "value", ttl=1)
        cache.set("expiring2", "value", ttl=1)
        
        time.sleep(1.1)
        removed = cache.cleanup_expired()
        
        assert removed == 2
        assert cache.get("permanent") == "value"


class TestRateLimiter:
    """Test rate limiter implementation."""

    def test_allows_requests_under_limit(self):
        """Test that requests under limit are allowed."""
        limiter = RateLimiter(requests_per_minute=10)
        
        for _ in range(10):
            assert limiter.is_allowed("user1") is True

    def test_blocks_requests_over_limit(self):
        """Test that requests over limit are blocked."""
        limiter = RateLimiter(requests_per_minute=5)
        
        for _ in range(5):
            limiter.is_allowed("user1")
        
        assert limiter.is_allowed("user1") is False

    def test_separate_limits_per_key(self):
        """Test that different keys have separate limits."""
        limiter = RateLimiter(requests_per_minute=2)
        
        limiter.is_allowed("user1")
        limiter.is_allowed("user1")
        
        assert limiter.is_allowed("user1") is False
        assert limiter.is_allowed("user2") is True

    def test_get_remaining(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(requests_per_minute=10)
        
        assert limiter.get_remaining("user1") == 10
        limiter.is_allowed("user1")
        assert limiter.get_remaining("user1") == 9

