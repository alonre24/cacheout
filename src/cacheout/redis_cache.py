import os
import redis
from cacheout import Cache

class RedisCache(Cache):
    """A cache implementation using Redis as the backend."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the RedisCache with given arguments and create the Redis client."""
        super().__init__(*args, **kwargs)
        self.redis_client = self._create_redis_client()

    def _create_redis_client(self):
        """Create and return a Redis client connected to the specified host and port."""
        try:
            pool = redis.ConnectionPool(
                host=os.environ.get('REDIS_HOST', 'localhost'),
                port=int(os.environ.get('REDIS_PORT', 6379)),
                username=os.environ.get('REDIS_USERNAME'),
                password=os.environ.get('REDIS_PASSWORD'),
                decode_responses=True
            )
            return redis.Redis(connection_pool=pool)
        except Exception as e:
            raise ConnectionError("Could not connect to Redis: " + str(e))

    def get(self, key):
        """Retrieve the value associated with the given key from the cache."""
        try:
            value = self.redis_client.get(key)
            return value if value is not None else self._on_miss(key)
        except Exception as e:
            raise e

    def set(self, key, value, expire=None):
        """Set the value for the given key in the cache with an optional expiration time."""
        try:
            result = self.redis_client.set(key, value)
            if expire:
                self.redis_client.expire(key, expire)
            return result
        except Exception as e:
            raise e

    def delete(self, key):
        """Delete the value associated with the given key from the cache."""
        try:
            return self.redis_client.delete(key)
        except Exception as e:
            raise e

    def clear(self):
        """Clear all entries in the cache."""
        try:
            self.redis_client.flushdb()
        except Exception as e:
            raise e

    def has(self, key):
        """Check if the cache contains the given key."""
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            raise e

    def add(self, key, value, expire=None):
        """Add a value for the given key in the cache if the key does not already exist."""
        if not self.has(key):
            return self.set(key, value, expire)
        return False
            
    def add_many(self, items, expire=None):
        """Add multiple items to the cache."""
        results = {}
        for key, value in items.items():
            results[key] = self.add(key, value, expire)
        return results
    
    def delete_many(self, keys):
        """Delete multiple items from the cache."""
        return sum(self.delete(key) for key in keys)

    def delete_expired(self):
        """Delete expired items from the cache (if supported)."""
        # Not typically needed with Redis, but can implement as needed
        pass

    def popitem(self):
        """Remove and return a key-value pair from the cache."""
        try:
            key = self.redis_client.randomkey()
            if key is not None:
                value = self.redis_client.get(key)
                self.delete(key)
                return key, value
            return None
        except Exception as e:
            raise e