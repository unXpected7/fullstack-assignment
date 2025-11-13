import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional
from cachetools import TTLCache


class MockProductService:
    """Mock Product Service for testing product business logic"""

    def __init__(self):
        self.cache = TTLCache(maxsize=1000, ttl=300)
        self.config = {
            'endpoint': 'https://api.example.com/products',
            'api_key': None,
            'headers': {}
        }

    async def fetch_product_from_external_api(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Mock external API product fetching with caching"""
        # Check cache first
        cache_key = f"product_{product_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Mock external API call
        mock_products = {
            'prod_001': {
                'id': 'prod_001',
                'name': 'Test Product',
                'price': 99.99,
                'stock': 50,
                'vendor_id': 'vendor_001',
                'vendor_name': 'Test Vendor',
                'image_url': 'https://example.com/image.jpg'
            },
            'prod_002': {
                'id': 'prod_002',
                'name': 'Another Product',
                'price': 49.99,
                'stock': 0,
                'vendor_id': 'vendor_001',
                'vendor_name': 'Test Vendor',
                'image_url': 'https://example.com/image2.jpg'
            },
            'prod_003': {
                'id': 'prod_003',
                'name': 'Premium Product',
                'price': 999.99,
                'stock': 5,
                'vendor_id': 'vendor_002',
                'vendor_name': 'Premium Vendor',
                'image_url': 'https://example.com/premium.jpg'
            }
        }

        product_data = mock_products.get(product_id)

        # Cache the result (even None to avoid repeated API calls)
        self.cache[cache_key] = product_data

        return product_data

    def validate_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate product data structure and values"""
        required_fields = ['id', 'name', 'price', 'stock', 'vendor_id', 'vendor_name']
        errors = []

        # Check required fields
        for field in required_fields:
            if field not in product_data:
                errors.append(f"Missing required field: {field}")
            elif product_data[field] is None:
                errors.append(f"Field '{field}' cannot be null")

        # Validate data types and values
        if 'price' in product_data:
            if not isinstance(product_data['price'], (int, float)):
                errors.append("Price must be a number")
            elif product_data['price'] < 0:
                errors.append("Price cannot be negative")

        if 'stock' in product_data:
            if not isinstance(product_data['stock'], int):
                errors.append("Stock must be an integer")
            elif product_data['stock'] < 0:
                errors.append("Stock cannot be negative")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    def check_stock_availability(self, product_data: Dict[str, Any],
                                required_quantity: int) -> Dict[str, Any]:
        """Check if product has sufficient stock"""
        if not product_data:
            return {
                'available': False,
                'error': 'Product not found'
            }

        available_stock = product_data.get('stock', 0)

        if available_stock >= required_quantity:
            return {
                'available': True,
                'stock_level': available_stock,
                'can_fulfill': True
            }
        else:
            return {
                'available': True,
                'stock_level': available_stock,
                'can_fulfill': False,
                'shortage': required_quantity - available_stock
            }

    def get_product_summary(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of product information"""
        if not product_data:
            return {}

        return {
            'id': product_data.get('id'),
            'name': product_data.get('name'),
            'price': product_data.get('price', 0),
            'vendor': {
                'id': product_data.get('vendor_id'),
                'name': product_data.get('vendor_name')
            },
            'availability': {
                'in_stock': product_data.get('stock', 0) > 0,
                'stock_level': product_data.get('stock', 0)
            },
            'shipping_eligible': product_data.get('price', 0) > 0
        }

    def update_config(self, endpoint: str, api_key: str = None,
                     headers: Dict[str, str] = None) -> None:
        """Update product service configuration"""
        self.config['endpoint'] = endpoint
        self.config['api_key'] = api_key
        self.config['headers'] = headers or {}

        # Clear cache when config changes
        self.cache.clear()

    def clear_cache(self) -> None:
        """Clear the product cache"""
        self.cache.clear()


@pytest.mark.unit
@pytest.mark.product
@pytest.mark.service
class TestProductService:
    """Test cases for Product Service functionality"""

    @pytest.fixture
    def product_service(self):
        """Create product service instance for testing"""
        return MockProductService()

    @pytest.mark.asyncio
    async def test_fetch_existing_product(self, product_service):
        """Test fetching an existing product"""
        product_data = await product_service.fetch_product_from_external_api('prod_001')

        assert product_data is not None
        assert product_data['id'] == 'prod_001'
        assert product_data['name'] == 'Test Product'
        assert product_data['price'] == 99.99
        assert product_data['stock'] == 50

    @pytest.mark.asyncio
    async def test_fetch_nonexistent_product(self, product_service):
        """Test fetching a non-existent product"""
        product_data = await product_service.fetch_product_from_external_api('nonexistent')

        assert product_data is None

    @pytest.mark.asyncio
    async def test_product_caching(self, product_service):
        """Test that products are cached after first fetch"""
        # First call - should fetch from API
        product_data_1 = await product_service.fetch_product_from_external_api('prod_001')

        # Second call - should use cache
        product_data_2 = await product_service.fetch_product_from_external_api('prod_001')

        assert product_data_1 is not None
        assert product_data_2 is not None
        assert product_data_1 == product_data_2

        # Verify it's in cache
        assert f"product_prod_001" in product_service.cache

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, product_service):
        """Test cache clearing when config updates"""
        # Fetch product to populate cache
        await product_service.fetch_product_from_external_api('prod_001')
        assert len(product_service.cache) > 0

        # Update config should clear cache
        product_service.update_config('https://new-api.example.com/products')
        assert len(product_service.cache) == 0

    @pytest.mark.asyncio
    async def test_multiple_product_fetches(self, product_service):
        """Test fetching multiple different products"""
        products = ['prod_001', 'prod_002', 'prod_003']
        fetched_products = []

        for product_id in products:
            product_data = await product_service.fetch_product_from_external_api(product_id)
            fetched_products.append(product_data)

        assert len(fetched_products) == 3
        assert all(p is not None for p in fetched_products)
        assert len(product_service.cache) == 3  # All products should be cached

    def test_validate_complete_product_data(self, product_service, sample_product_data):
        """Test validation of complete product data"""
        result = product_service.validate_product_data(sample_product_data)

        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    @pytest.mark.negative
    @pytest.mark.parametrize("missing_field", ['id', 'name', 'price', 'stock', 'vendor_id', 'vendor_name'])
    def test_validate_missing_required_field(self, product_service, sample_product_data, missing_field):
        """Test validation with missing required field"""
        invalid_product = sample_product_data.copy()
        del invalid_product[missing_field]

        result = product_service.validate_product_data(invalid_product)

        assert result['is_valid'] is False
        assert any(missing_field in error for error in result['errors'])

    def test_validate_null_fields(self, product_service, sample_product_data):
        """Test validation with null field values"""
        invalid_product = sample_product_data.copy()
        invalid_product['price'] = None
        invalid_product['stock'] = None

        result = product_service.validate_product_data(invalid_product)

        assert result['is_valid'] is False
        assert any('price' in error for error in result['errors'])
        assert any('stock' in error for error in result['errors'])

    @pytest.mark.negative
    @pytest.mark.parametrize("field,invalid_value,error_message", [
        ('price', -10.0, 'Price cannot be negative'),
        ('price', 'invalid', 'Price must be a number'),
        ('stock', -5, 'Stock cannot be negative'),
        ('stock', 10.5, 'Stock must be an integer'),
    ])
    def test_validate_invalid_field_values(self, product_service, sample_product_data,
                                         field, invalid_value, error_message):
        """Test validation with invalid field values"""
        invalid_product = sample_product_data.copy()
        invalid_product[field] = invalid_value

        result = product_service.validate_product_data(invalid_product)

        assert result['is_valid'] is False
        assert any(error_message in error for error in result['errors'])

    def test_check_sufficient_stock(self, product_service, sample_product_data):
        """Test stock check with sufficient quantity"""
        result = product_service.check_stock_availability(sample_product_data, 5)

        assert result['available'] is True
        assert result['can_fulfill'] is True
        assert result['stock_level'] == 50

    def test_check_insufficient_stock(self, product_service, sample_product_data):
        """Test stock check with insufficient quantity"""
        result = product_service.check_stock_availability(sample_product_data, 100)

        assert result['available'] is True
        assert result['can_fulfill'] is False
        assert result['shortage'] == 50
        assert result['stock_level'] == 50

    def test_check_stock_no_product(self, product_service):
        """Test stock check with no product data"""
        result = product_service.check_stock_availability(None, 5)

        assert result['available'] is False
        assert result['error'] == 'Product not found'
        assert 'can_fulfill' not in result

    def test_check_stock_zero_quantity(self, product_service, sample_product_data):
        """Test stock check with zero quantity"""
        result = product_service.check_stock_availability(sample_product_data, 0)

        assert result['available'] is True
        assert result['can_fulfill'] is True

    def test_get_product_summary_complete(self, product_service, sample_product_data):
        """Test getting product summary for complete data"""
        summary = product_service.get_product_summary(sample_product_data)

        assert summary['id'] == sample_product_data['id']
        assert summary['name'] == sample_product_data['name']
        assert summary['price'] == sample_product_data['price']
        assert summary['vendor']['id'] == sample_product_data['vendor_id']
        assert summary['vendor']['name'] == sample_product_data['vendor_name']
        assert summary['availability']['in_stock'] is True
        assert summary['availability']['stock_level'] == sample_product_data['stock']
        assert summary['shipping_eligible'] is True

    def test_get_product_summary_no_stock(self, product_service):
        """Test product summary for out-of-stock product"""
        no_stock_product = {
            'id': 'prod_002',
            'name': 'Out of Stock Product',
            'price': 49.99,
            'stock': 0,
            'vendor_id': 'vendor_001',
            'vendor_name': 'Test Vendor'
        }

        summary = product_service.get_product_summary(no_stock_product)

        assert summary['availability']['in_stock'] is False
        assert summary['availability']['stock_level'] == 0

    def test_get_product_summary_empty_product(self, product_service):
        """Test product summary with empty product data"""
        summary = product_service.get_product_summary({})
        assert summary == {}

        summary = product_service.get_product_summary(None)
        assert summary == {}

    def test_update_service_config(self, product_service):
        """Test updating product service configuration"""
        new_endpoint = 'https://new-api.example.com/products'
        new_api_key = 'new_api_key'
        new_headers = {'Authorization': 'Bearer new_api_key'}

        product_service.update_config(new_endpoint, new_api_key, new_headers)

        assert product_service.config['endpoint'] == new_endpoint
        assert product_service.config['api_key'] == new_api_key
        assert product_service.config['headers'] == new_headers

    def test_update_config_without_optional_params(self, product_service):
        """Test updating config with only required endpoint"""
        new_endpoint = 'https://simple-api.example.com/products'

        product_service.update_config(new_endpoint)

        assert product_service.config['endpoint'] == new_endpoint
        assert product_service.config['api_key'] is None
        assert product_service.config['headers'] == {}

    def test_clear_cache_directly(self, product_service):
        """Test direct cache clearing"""
        # Add something to cache
        product_service.cache['test_key'] = 'test_value'
        assert len(product_service.cache) > 0

        product_service.clear_cache()
        assert len(product_service.cache) == 0

    @pytest.mark.edge_case
    def test_zero_price_product(self, product_service):
        """Test validation of zero-price product"""
        zero_price_product = {
            'id': 'prod_free',
            'name': 'Free Product',
            'price': 0.0,
            'stock': 100,
            'vendor_id': 'vendor_001',
            'vendor_name': 'Test Vendor'
        }

        result = product_service.validate_product_data(zero_price_product)

        assert result['is_valid'] is True  # Zero price should be valid
        assert len(result['errors']) == 0

    @pytest.mark.edge_case
    async def test_concurrent_product_fetches(self, product_service):
        """Test concurrent product fetching"""
        product_ids = ['prod_001', 'prod_002', 'prod_003']

        # Fetch all products concurrently
        tasks = [
            product_service.fetch_product_from_external_api(pid)
            for pid in product_ids
        ]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r is not None for r in results)

    @pytest.mark.boundary
    def test_very_large_stock_number(self, product_service, sample_product_data):
        """Test validation with very large stock numbers"""
        large_stock_product = sample_product_data.copy()
        large_stock_product['stock'] = 999999999

        result = product_service.validate_product_data(large_stock_product)

        assert result['is_valid'] is True  # Large numbers should be valid

    @pytest.mark.performance
    async def test_cache_performance(self, product_service):
        """Test cache improves performance"""
        import time

        # Time first fetch (should be slower)
        start_time = time.time()
        await product_service.fetch_product_from_external_api('prod_001')
        first_fetch_time = time.time() - start_time

        # Time second fetch (should be faster due to cache)
        start_time = time.time()
        await product_service.fetch_product_from_external_api('prod_001')
        second_fetch_time = time.time() - start_time

        # Second fetch should be faster (though this may not always be true in tests)
        assert second_fetch_time <= first_fetch_time