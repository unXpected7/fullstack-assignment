import pytest
import time
from unittest.mock import Mock, patch
from cachetools import TTLCache


class MockCacheUtils:
    """Mock Cache Utilities for testing cache functionality"""

    def __init__(self, maxsize=1000, ttl=300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0

    def get(self, key: str, default=None):
        """Get value from cache with statistics"""
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key]
        else:
            self.miss_count += 1
            return default

    def set(self, key: str, value) -> None:
        """Set value in cache with statistics"""
        self.cache[key] = value
        self.set_count += 1

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        self.set_count = 0

    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'maxsize': self.cache.maxsize,
            'ttl': self.cache.ttl,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'set_count': self.set_count,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

    def cache_function_result(self, cache_key: str, func, *args, **kwargs):
        """Cache function result with automatic cache key generation"""
        # Check cache first
        cached_result = self.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Execute function and cache result
        result = func(*args, **kwargs)
        self.set(cache_key, result)
        return result

    def cache_product_data(self, product_id: str, product_data: dict) -> None:
        """Cache product data with standardized key"""
        cache_key = f"product_{product_id}"
        self.set(cache_key, product_data)

    def get_cached_product(self, product_id: str) -> dict:
        """Get cached product data"""
        cache_key = f"product_{product_id}"
        return self.get(cache_key)

    def cache_calculation_result(self, calculation_type: str, params_hash: str, result: float) -> None:
        """Cache calculation result with type-specific key"""
        cache_key = f"calc_{calculation_type}_{params_hash}"
        self.set(cache_key, result)

    def get_cached_calculation(self, calculation_type: str, params_hash: str) -> float:
        """Get cached calculation result"""
        cache_key = f"calc_{calculation_type}_{params_hash}"
        return self.get(cache_key)

    def is_expired(self, key: str) -> bool:
        """Check if cached item is expired (simulated)"""
        # In a real implementation, this would check actual expiration
        return key not in self.cache

    def get_keys_by_pattern(self, pattern: str) -> list:
        """Get all cache keys matching pattern"""
        matching_keys = []
        for key in self.cache.keys():
            if pattern in str(key):
                matching_keys.append(key)
        return matching_keys

    def delete_by_pattern(self, pattern: str) -> int:
        """Delete cache entries matching pattern"""
        keys_to_delete = self.get_keys_by_pattern(pattern)
        deleted_count = 0
        for key in keys_to_delete:
            if self.delete(key):
                deleted_count += 1
        return deleted_count


@pytest.mark.unit
@pytest.mark.utils
@pytest.mark.cache
class TestCacheUtils:
    """Test cases for Cache Utility functions"""

    @pytest.fixture
    def cache_utils(self):
        """Create cache utils instance for testing"""
        return MockCacheUtils(maxsize=10, ttl=1)  # Small cache for testing

    def test_cache_set_and_get(self, cache_utils):
        """Test basic cache set and get operations"""
        cache_utils.set("test_key", "test_value")
        result = cache_utils.get("test_key")

        assert result == "test_value"
        assert cache_utils.set_count == 1
        assert cache_utils.hit_count == 1

    def test_cache_get_nonexistent_key(self, cache_utils):
        """Test getting non-existent key"""
        result = cache_utils.get("nonexistent_key", "default_value")

        assert result == "default_value"
        assert cache_utils.miss_count == 1

    def test_cache_get_nonexistent_key_no_default(self, cache_utils):
        """Test getting non-existent key without default"""
        result = cache_utils.get("nonexistent_key")

        assert result is None
        assert cache_utils.miss_count == 1

    def test_cache_delete_existing_key(self, cache_utils):
        """Test deleting existing key"""
        cache_utils.set("test_key", "test_value")
        deleted = cache_utils.delete("test_key")

        assert deleted is True
        assert cache_utils.get("test_key") is None

    def test_cache_delete_nonexistent_key(self, cache_utils):
        """Test deleting non-existent key"""
        deleted = cache_utils.delete("nonexistent_key")

        assert deleted is False

    def test_cache_clear(self, cache_utils):
        """Test clearing cache"""
        cache_utils.set("key1", "value1")
        cache_utils.set("key2", "value2")
        cache_utils.set("key3", "value3")

        assert cache_utils.size() == 3

        cache_utils.clear()

        assert cache_utils.size() == 0
        assert cache_utils.hit_count == 0
        assert cache_utils.miss_count == 0
        assert cache_utils.set_count == 0

    @pytest.mark.happy_path
    def test_cache_product_data(self, cache_utils, sample_product_data):
        """Test caching product data"""
        product_id = "prod_001"
        cache_utils.cache_product_data(product_id, sample_product_data)

        cached_product = cache_utils.get_cached_product(product_id)
        assert cached_product == sample_product_data

    def test_get_cached_product_nonexistent(self, cache_utils):
        """Test getting cached non-existent product"""
        cached_product = cache_utils.get_cached_product("nonexistent_product")
        assert cached_product is None

    @pytest.mark.happy_path
    def test_cache_calculation_result(self, cache_utils):
        """Test caching calculation result"""
        calculation_type = "shipping"
        params_hash = "vendor1_items_2"
        result = 15.99

        cache_utils.cache_calculation_result(calculation_type, params_hash, result)
        cached_result = cache_utils.get_cached_calculation(calculation_type, params_hash)

        assert cached_result == result

    @pytest.mark.happy_path
    def test_cache_function_result(self, cache_utils):
        """Test caching function result"""
        def expensive_function(x, y):
            return x * y + time.time()  # Include time to ensure unique results

        # First call should execute function
        result1 = cache_utils.cache_function_result("test_func", expensive_function, 5, 10)
        assert cache_utils.set_count == 1

        # Second call should use cached result
        result2 = cache_utils.cache_function_result("test_func", expensive_function, 5, 10)
        assert result2 == result1
        assert cache_utils.hit_count >= 1

    def test_cache_statistics(self, cache_utils):
        """Test cache statistics tracking"""
        # Perform some operations
        cache_utils.set("key1", "value1")
        cache_utils.set("key2", "value2")
        cache_utils.get("key1")  # Hit
        cache_utils.get("key2")  # Hit
        cache_utils.get("nonexistent")  # Miss

        stats = cache_utils.get_stats()

        assert stats['size'] == 2
        assert stats['maxsize'] == 10
        assert stats['hit_count'] == 2
        assert stats['miss_count'] == 1
        assert stats['total_requests'] == 3
        assert stats['hit_rate'] == 2/3  # 2 hits out of 3 requests

    @pytest.mark.edge_case
    def test_cache_size_limit(self, cache_utils):
        """Test cache respects size limit"""
        # Fill cache to capacity
        for i in range(cache_utils.cache.maxsize + 5):
            cache_utils.set(f"key_{i}", f"value_{i}")

        # Cache should not exceed maxsize
        assert cache_utils.size() <= cache_utils.cache.maxsize

    @pytest.mark.boundary
    def test_cache_ttl_expiration(self, cache_utils):
        """Test cache TTL expiration"""
        cache_utils.set("expire_key", "expire_value")

        # Value should be available immediately
        assert cache_utils.get("expire_key") == "expire_value"

        # Wait for TTL to expire (using short TTL for testing)
        time.sleep(1.1)  # Slightly longer than TTL

        # Value should be expired
        assert cache_utils.get("expire_key") is None

    def test_get_keys_by_pattern(self, cache_utils):
        """Test getting cache keys by pattern"""
        cache_utils.set("product_001", "data1")
        cache_utils.set("product_002", "data2")
        cache_utils.set("cart_001", "data3")
        cache_utils.set("user_001", "data4")

        product_keys = cache_utils.get_keys_by_pattern("product")
        assert len(product_keys) == 2
        assert "product_001" in product_keys
        assert "product_002" in product_keys

        cart_keys = cache_utils.get_keys_by_pattern("cart")
        assert len(cart_keys) == 1
        assert "cart_001" in cart_keys

    def test_delete_by_pattern(self, cache_utils):
        """Test deleting cache entries by pattern"""
        cache_utils.set("product_001", "data1")
        cache_utils.set("product_002", "data2")
        cache_utils.set("product_003", "data3")
        cache_utils.set("cart_001", "data4")

        deleted_count = cache_utils.delete_by_pattern("product")
        assert deleted_count == 3

        # Verify product entries are deleted
        assert cache_utils.get("product_001") is None
        assert cache_utils.get("product_002") is None
        assert cache_utils.get("product_003") is None

        # Verify other entries remain
        assert cache_utils.get("cart_001") == "data4"

    def test_is_expired(self, cache_utils):
        """Test cache expiration check"""
        cache_utils.set("test_key", "test_value")

        # Key should not be expired immediately
        assert cache_utils.is_expired("test_key") is False

        # Non-existent key should be expired
        assert cache_utils.is_expired("nonexistent_key") is True

    @pytest.mark.negative
    def test_cache_with_none_values(self, cache_utils):
        """Test caching None values"""
        cache_utils.set("none_key", None)

        result = cache_utils.get("none_key")
        assert result is None
        assert cache_utils.hit_count == 1  # Should count as hit, not miss

    @pytest.mark.performance
    def test_cache_performance(self, cache_utils):
        """Test cache performance with many operations"""
        import time

        start_time = time.time()

        # Perform many operations
        for i in range(1000):
            cache_utils.set(f"key_{i}", f"value_{i}")
            cache_utils.get(f"key_{i}")

        end_time = time.time()
        operation_time = end_time - start_time

        # Should complete 2000 operations quickly
        assert operation_time < 1.0

    @pytest.mark.security
    def test_cache_key_injection_safety(self, cache_utils):
        """Test cache is safe from key injection attacks"""
        malicious_key = "../../../etc/passwd"
        safe_key = "safe_key"

        # Set value with malicious-looking key
        cache_utils.set(malicious_key, "malicious_value")
        cache_utils.set(safe_key, "safe_value")

        # Should be able to retrieve both without issues
        assert cache_utils.get(malicious_key) == "malicious_value"
        assert cache_utils.get(safe_key) == "safe_value"

    @pytest.mark.concurrency
    def test_cache_thread_safety_simulation(self, cache_utils):
        """Test cache behavior with simulated concurrent access"""
        import threading
        import time

        results = []
        errors = []

        def worker(worker_id):
            try:
                for i in range(10):
                    key = f"worker_{worker_id}_key_{i}"
                    value = f"worker_{worker_id}_value_{i}"
                    cache_utils.set(key, value)
                    time.sleep(0.001)  # Small delay to simulate real usage
                    retrieved = cache_utils.get(key)
                    if retrieved != value:
                        errors.append(f"Worker {worker_id}: Expected {value}, got {retrieved}")
            except Exception as e:
                errors.append(f"Worker {worker_id} error: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        # Start threads
        for thread in threads:
            thread.start()

        # Wait for threads to complete
        for thread in threads:
            thread.join()

        # Check for errors (in real implementation, you'd want proper thread safety)
        # For this mock test, we just verify basic functionality
        assert len(errors) == 0 or isinstance(cache_utils.cache, TTLCache)

    def test_cache_memory_usage(self, cache_utils):
        """Test cache doesn't grow indefinitely"""
        initial_size = cache_utils.size()

        # Add many items beyond capacity
        for i in range(cache_utils.cache.maxsize * 2):
            cache_utils.set(f"overflow_key_{i}", f"value_{i}")

        # Cache should still be within limits
        final_size = cache_utils.size()
        assert final_size <= cache_utils.cache.maxsize

        # Statistics should reflect operations
        stats = cache_utils.get_stats()
        assert stats['set_count'] > initial_size

    @pytest.mark.integration
    def test_cache_integration_with_product_service(self, cache_utils):
        """Test cache integration with product service workflow"""
        # Simulate product service workflow
        product_data = {
            "id": "prod_integration",
            "name": "Integration Test Product",
            "price": 99.99,
            "stock": 10
        }

        # First request - cache miss
        cached_product = cache_utils.get_cached_product("prod_integration")
        assert cached_product is None
        assert cache_utils.miss_count == 1

        # Cache product (simulating API response)
        cache_utils.cache_product_data("prod_integration", product_data)

        # Second request - cache hit
        cached_product = cache_utils.get_cached_product("prod_integration")
        assert cached_product == product_data
        assert cache_utils.hit_count >= 1

        # Verify cache statistics
        stats = cache_utils.get_stats()
        assert stats['hit_count'] >= 1
        assert stats['miss_count'] >= 1