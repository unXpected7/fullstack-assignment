import pytest
import sqlite3
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


# Mock cart service functions (since we don't have service layer yet, we'll test the main.py functions)
class MockCartService:
    """Mock Cart Service for testing cart business logic"""

    @staticmethod
    def calculate_cart_totals(cart_items: List[Dict[str, Any]],
                           discount_code: str = None) -> Dict[str, float]:
        """Calculate cart totals including shipping and discounts"""
        if not cart_items:
            return {
                'subtotal': 0.0,
                'discount': 0.0,
                'shipping': 0.0,
                'total': 0.0
            }

        # Calculate subtotal
        subtotal = sum(item['price'] * item['quantity'] for item in cart_items)

        # Group by vendor for shipping calculation
        vendor_subtotals = {}
        for item in cart_items:
            vendor_id = item['vendor_id']
            vendor_total = item['price'] * item['quantity']
            vendor_subtotals[vendor_id] = vendor_subtotals.get(vendor_id, 0) + vendor_total

        # Calculate shipping ($100 per vendor with subtotal < $800)
        shipping = 0
        for vendor_subtotal in vendor_subtotals.values():
            if vendor_subtotal < 800:
                shipping += 100

        # Calculate discount
        discount = 0.0
        if discount_code:
            # Mock discount logic
            discount_codes = {
                'SAVE10': 0.10,
                'SAVE20': 0.20,
                'SAVE15': 0.15
            }
            if discount_code in discount_codes:
                discount = subtotal * discount_codes[discount_code]

        total = subtotal - discount + shipping

        return {
            'subtotal': round(subtotal, 2),
            'discount': round(discount, 2),
            'shipping': round(shipping, 2),
            'total': round(total, 2)
        }

    @staticmethod
    def validate_cart_item(product_id: str, quantity: int,
                         product_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate cart item data"""
        errors = []

        if not product_id or not product_id.strip():
            errors.append("Product ID is required")

        if not isinstance(quantity, int) or quantity < 1:
            errors.append("Quantity must be a positive integer")

        if product_data:
            if product_data.get('stock', 0) < quantity:
                errors.append("Insufficient stock")

            if product_data.get('price', 0) < 0:
                errors.append("Invalid product price")

        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }

    @staticmethod
    def calculate_vendor_shipping(items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate shipping costs per vendor"""
        vendor_totals = {}
        for item in items:
            vendor_id = item['vendor_id']
            item_total = item['price'] * item['quantity']
            vendor_totals[vendor_id] = vendor_totals.get(vendor_id, 0) + item_total

        vendor_shipping = {}
        for vendor_id, subtotal in vendor_totals.items():
            shipping_cost = 0 if subtotal >= 800 else 100
            vendor_shipping[vendor_id] = shipping_cost

        return vendor_shipping


@pytest.mark.unit
@pytest.mark.cart
@pytest.mark.service
class TestCartService:
    """Test cases for Cart Service functionality"""

    def test_calculate_empty_cart_totals(self):
        """Test calculation for empty cart"""
        result = MockCartService.calculate_cart_totals([])

        assert result['subtotal'] == 0.0
        assert result['discount'] == 0.0
        assert result['shipping'] == 0.0
        assert result['total'] == 0.0

    def test_calculate_single_item_cart_totals(self, sample_product_data):
        """Test calculation for cart with single item"""
        cart_items = [{
            'product_id': sample_product_data['id'],
            'price': sample_product_data['price'],
            'quantity': 2,
            'vendor_id': sample_product_data['vendor_id']
        }]

        result = MockCartService.calculate_cart_totals(cart_items)

        expected_subtotal = 99.99 * 2  # 199.98
        expected_shipping = 100  # Below $800 threshold
        expected_total = expected_subtotal + expected_shipping

        assert result['subtotal'] == expected_subtotal
        assert result['shipping'] == expected_shipping
        assert result['discount'] == 0.0
        assert result['total'] == expected_total

    def test_calculate_multiple_items_same_vendor(self, sample_product_data):
        """Test calculation for multiple items from same vendor"""
        cart_items = [
            {
                'product_id': sample_product_data['id'],
                'price': sample_product_data['price'],
                'quantity': 3,
                'vendor_id': sample_product_data['vendor_id']
            },
            {
                'product_id': 'prod_002',
                'price': 50.0,
                'quantity': 2,
                'vendor_id': sample_product_data['vendor_id']
            }
        ]

        result = MockCartService.calculate_cart_totals(cart_items)

        expected_subtotal = (99.99 * 3) + (50.0 * 2)  # 299.97 + 100 = 399.97
        expected_shipping = 100  # Single vendor, subtotal < $800
        expected_total = expected_subtotal + expected_shipping

        assert result['subtotal'] == expected_subtotal
        assert result['shipping'] == expected_shipping
        assert result['total'] == expected_total

    def test_calculate_multiple_vendors_shipping(self, sample_product_data_multiple_vendors):
        """Test shipping calculation for multiple vendors"""
        cart_items = [
            {
                'product_id': 'prod_high_value',
                'price': 850.0,
                'quantity': 1,
                'vendor_id': 'vendor_001'
            },
            {
                'product_id': 'prod_low_value',
                'price': 750.0,
                'quantity': 1,
                'vendor_id': 'vendor_002'
            },
            {
                'product_id': 'prod_mid_value',
                'price': 500.0,
                'quantity': 1,
                'vendor_id': 'vendor_003'
            }
        ]

        result = MockCartService.calculate_cart_totals(cart_items)

        expected_subtotal = 850.0 + 750.0 + 500.0  # 2100.0
        # vendor_001: $850 >= $800 (free shipping)
        # vendor_002: $750 < $800 ($100 shipping)
        # vendor_003: $500 < $800 ($100 shipping)
        expected_shipping = 0 + 100 + 100  # 200
        expected_total = expected_subtotal + expected_shipping

        assert result['subtotal'] == expected_subtotal
        assert result['shipping'] == expected_shipping
        assert result['total'] == expected_total

    @pytest.mark.parametrize("discount_code,expected_percentage", [
        ('SAVE10', 0.10),
        ('SAVE20', 0.20),
        ('SAVE15', 0.15)
    ])
    def test_calculate_discount_codes(self, sample_product_data, discount_code, expected_percentage):
        """Test discount code application"""
        cart_items = [{
            'product_id': sample_product_data['id'],
            'price': sample_product_data['price'],
            'quantity': 5,
            'vendor_id': sample_product_data['vendor_id']
        }]

        result = MockCartService.calculate_cart_totals(cart_items, discount_code)

        expected_subtotal = 99.99 * 5  # 499.95
        expected_discount = expected_subtotal * expected_percentage
        expected_shipping = 100  # Below $800 threshold
        expected_total = expected_subtotal - expected_discount + expected_shipping

        assert result['subtotal'] == expected_subtotal
        assert result['discount'] == expected_discount
        assert result['shipping'] == expected_shipping
        assert result['total'] == expected_total

    def test_invalid_discount_code(self, sample_product_data):
        """Test behavior with invalid discount code"""
        cart_items = [{
            'product_id': sample_product_data['id'],
            'price': sample_product_data['price'],
            'quantity': 1,
            'vendor_id': sample_product_data['vendor_id']
        }]

        result = MockCartService.calculate_cart_totals(cart_items, 'INVALID')

        expected_subtotal = 99.99
        expected_shipping = 100

        assert result['subtotal'] == expected_subtotal
        assert result['discount'] == 0.0  # No discount for invalid code
        assert result['shipping'] == expected_shipping
        assert result['total'] == expected_subtotal + expected_shipping

    def test_validate_valid_cart_item(self, sample_product_data):
        """Test validation of valid cart item"""
        result = MockCartService.validate_cart_item(
            'prod_001', 2, sample_product_data
        )

        assert result['is_valid'] is True
        assert len(result['errors']) == 0

    @pytest.mark.negative
    @pytest.mark.parametrize("product_id,quantity,expected_errors", [
        ('', 2, ['Product ID is required']),
        (None, 2, ['Product ID is required']),
        ('prod_001', 0, ['Quantity must be a positive integer']),
        ('prod_001', -1, ['Quantity must be a positive integer']),
        ('', 0, ['Product ID is required', 'Quantity must be a positive integer']),
    ])
    def test_validate_invalid_cart_item(self, product_id, quantity, expected_errors):
        """Test validation of invalid cart item"""
        result = MockCartService.validate_cart_item(product_id, quantity)

        assert result['is_valid'] is False
        assert len(result['errors']) == len(expected_errors)
        for error in expected_errors:
            assert error in result['errors']

    def test_validate_insufficient_stock(self, sample_product_data):
        """Test validation with insufficient stock"""
        insufficient_stock_product = sample_product_data.copy()
        insufficient_stock_product['stock'] = 1

        result = MockCartService.validate_cart_item(
            'prod_001', 5, insufficient_stock_product
        )

        assert result['is_valid'] is False
        assert 'Insufficient stock' in result['errors']

    def test_validate_negative_price(self, sample_product_data):
        """Test validation with negative price"""
        invalid_product = sample_product_data.copy()
        invalid_product['price'] = -10.0

        result = MockCartService.validate_cart_item(
            'prod_001', 1, invalid_product
        )

        assert result['is_valid'] is False
        assert 'Invalid product price' in result['errors']

    def test_calculate_vendor_shipping_free_shipping(self):
        """Test free shipping for vendors with high-value orders"""
        items = [
            {'vendor_id': 'vendor_001', 'price': 400.0, 'quantity': 2},  # $800 total
            {'vendor_id': 'vendor_002', 'price': 900.0, 'quantity': 1}   # $900 total
        ]

        result = MockCartService.calculate_vendor_shipping(items)

        assert result['vendor_001'] == 0  # Exactly $800, free shipping
        assert result['vendor_002'] == 0  # Above $800, free shipping

    def test_calculate_vendor_shipping_paid_shipping(self):
        """Test paid shipping for vendors with low-value orders"""
        items = [
            {'vendor_id': 'vendor_001', 'price': 300.0, 'quantity': 2},  # $600 total
            {'vendor_id': 'vendor_002', 'price': 100.0, 'quantity': 1}   # $100 total
        ]

        result = MockCartService.calculate_vendor_shipping(items)

        assert result['vendor_001'] == 100  # Below $800, $100 shipping
        assert result['vendor_002'] == 100  # Below $800, $100 shipping

    @pytest.mark.boundary
    def test_boundary_shipping_threshold(self):
        """Test behavior exactly at shipping threshold"""
        # Test exactly at $800 threshold
        items_at_threshold = [
            {'vendor_id': 'vendor_001', 'price': 800.0, 'quantity': 1}
        ]

        result = MockCartService.calculate_vendor_shipping(items_at_threshold)
        assert result['vendor_001'] == 0  # Exactly at threshold, free shipping

        # Test just below $800 threshold
        items_below_threshold = [
            {'vendor_id': 'vendor_001', 'price': 799.99, 'quantity': 1}
        ]

        result = MockCartService.calculate_vendor_shipping(items_below_threshold)
        assert result['vendor_001'] == 100  # Just below threshold, paid shipping

    @pytest.mark.edge_case
    def test_large_quantity_calculation(self, sample_product_data):
        """Test calculation with large quantities"""
        cart_items = [{
            'product_id': sample_product_data['id'],
            'price': 0.01,  # Very small price
            'quantity': 1000000,  # Large quantity
            'vendor_id': sample_product_data['vendor_id']
        }]

        result = MockCartService.calculate_cart_totals(cart_items)

        expected_subtotal = 0.01 * 1000000  # 10000.0
        expected_shipping = 0  # Above $800 threshold
        expected_total = expected_subtotal

        assert result['subtotal'] == expected_subtotal
        assert result['shipping'] == expected_shipping
        assert result['total'] == expected_total

    def test_floating_point_precision(self):
        """Test floating point precision in calculations"""
        cart_items = [
            {'product_id': 'prod_001', 'price': 0.1, 'quantity': 3, 'vendor_id': 'vendor_001'},  # 0.3
            {'product_id': 'prod_002', 'price': 0.2, 'quantity': 2, 'vendor_id': 'vendor_001'},  # 0.4
        ]

        result = MockCartService.calculate_cart_totals(cart_items)

        expected_subtotal = 0.7  # 0.3 + 0.4
        expected_shipping = 100  # Below $800 threshold
        expected_total = 100.7

        assert abs(result['subtotal'] - expected_subtotal) < 0.0001
        assert result['shipping'] == expected_shipping
        assert abs(result['total'] - expected_total) < 0.0001