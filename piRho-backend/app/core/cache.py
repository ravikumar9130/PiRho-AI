"""In-memory cache implementation with TTL support."""
import time
from typing import Any, Optional
from threading import Lock


class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        with self._lock:
            if key not in self._cache:
                return None
            value, expiry = self._cache[key]
            if expiry and time.time() > expiry:
                del self._cache[key]
                return None
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL in seconds."""
        with self._lock:
            expiry = time.time() + ttl if ttl else None
            self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        with self._lock:
            now = time.time()
            expired = [k for k, (_, exp) in self._cache.items() if exp and now > exp]
            for key in expired:
                del self._cache[key]
            return len(expired)


# Global cache instance
cache_manager = InMemoryCache()


class RateLimiter:
    """Token bucket rate limiter using in-memory storage."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.limit = requests_per_minute
        self._buckets: dict[str, tuple[int, float]] = {}
        self._lock = Lock()
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit."""
        with self._lock:
            now = time.time()
            window_start = now - 60
            
            if key not in self._buckets:
                self._buckets[key] = (1, now)
                return True
            
            count, first_request = self._buckets[key]
            
            # Reset window if expired
            if first_request < window_start:
                self._buckets[key] = (1, now)
                return True
            
            # Check limit
            if count >= self.limit:
                return False
            
            self._buckets[key] = (count + 1, first_request)
            return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for a key."""
        with self._lock:
            if key not in self._buckets:
                return self.limit
            count, first_request = self._buckets[key]
            if first_request < time.time() - 60:
                return self.limit
            return max(0, self.limit - count)


rate_limiter = RateLimiter()

