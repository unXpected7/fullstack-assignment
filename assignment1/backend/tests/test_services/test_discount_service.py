import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from unittest.mock import Mock


class MockDiscountService:
    """Mock Discount Service for testing discount business logic"""

    def __init__(self):
        self.discount_codes = {
            'SAVE10': {
                'code': 'SAVE10',
                'percentage': 10.0,
                'is_active': True,
                'created_at': datetime.now(),
                'usage_limit': None,
                'usage_count': 0,
                'minimum_amount': 0.0,
                'maximum_discount': None
            },
            'SAVE20': {
                'code': 'SAVE20',
                'percentage': 20.0,
                'is_active': True,
                'created_at': datetime.now(),
                'usage_limit': 100,
                'usage_count': 25,
                'minimum_amount': 50.0,
                'maximum_discount': 100.0
            },
            'SAVE15': {
                'code': 'SAVE15',
                'percentage': 15.0,
                'is_active': False,  # Inactive code
                'created_at': datetime.now(),
                'usage_limit': None,
                'usage_count': 0,
                'minimum_amount': 0.0,
                'maximum_discount': None
            },
            'EXPIRED': {
                'code': 'EXPIRED',
                'percentage': 25.0,
                'is_active': True,
                'created_at': datetime.now() - timedelta(days=400),
                'expires_at': datetime.now() - timedelta(days=1),
                'usage_limit': None,
                'usage_count': 0,
                'minimum_amount': 0.0,
                'maximum_discount': None
            },
            'SPECIAL50': {
                'code': 'SPECIAL50',
                'percentage': 50.0,
                'is_active': True,
                'created_at': datetime.now(),
                'usage_limit': 10,
                'usage_count': 10,  # Already at limit
                'minimum_amount': 200.0,
                'maximum_discount': 250.0
            }
        }

    def validate_discount_code(self, code: str) -> Dict[str, Any]:
        """Validate discount code existence and basic properties"""
        if not code or not isinstance(code, str):
            return {
                'valid': False,
                'error': 'Invalid discount code format'
            }

        code = code.upper().strip()
        discount = self.discount_codes.get(code)

        if not discount:
            return {
                'valid': False,
                'error': 'Discount code not found'
            }

        return {
            'valid': True,
            'discount': discount
        }

    def check_discount_eligibility(self, code: str, cart_total: float = 0.0) -> Dict[str, Any]:
        """Check if discount code can be applied based on various conditions"""
        validation = self.validate_discount_code(code)

        if not validation['valid']:
            return {
                'eligible': False,
                'error': validation['error']
            }

        discount = validation['discount']

        # Check if discount is active
        if not discount.get('is_active', True):
            return {
                'eligible': False,
                'error': 'Discount code is inactive'
            }

        # Check expiration
        if 'expires_at' in discount and discount['expires_at'] < datetime.now():
            return {
                'eligible': False,
                'error': 'Discount code has expired'
            }

        # Check usage limit
        usage_limit = discount.get('usage_limit')
        if usage_limit and discount.get('usage_count', 0) >= usage_limit:
            return {
                'eligible': False,
                'error': 'Discount code usage limit exceeded'
            }

        # Check minimum order amount
        minimum_amount = discount.get('minimum_amount', 0.0)
        if cart_total < minimum_amount:
            return {
                'eligible': False,
                'error': f'Minimum order amount of ${minimum_amount:.2f} required'
            }

        return {
            'eligible': True,
            'discount': discount
        }

    def calculate_discount_amount(self, discount: Dict[str, Any], cart_total: float) -> Dict[str, Any]:
        """Calculate the discount amount based on discount rules"""
        percentage = discount.get('percentage', 0.0)
        maximum_discount = discount.get('maximum_discount')

        # Calculate percentage discount
        discount_amount = cart_total * (percentage / 100)

        # Apply maximum discount limit if specified
        if maximum_discount and discount_amount > maximum_discount:
            discount_amount = maximum_discount

        return {
            'original_total': cart_total,
            'discount_percentage': percentage,
            'discount_amount': round(discount_amount, 2),
            'final_total': round(cart_total - discount_amount, 2),
            'capped_by_maximum': maximum_discount and discount_amount >= maximum_discount
        }

    def apply_discount_code(self, code: str, cart_total: float) -> Dict[str, Any]:
        """Apply discount code to cart total"""
        eligibility = self.check_discount_eligibility(code, cart_total)

        if not eligibility['eligible']:
            return {
                'success': False,
                'error': eligibility['error'],
                'original_total': cart_total,
                'discount_amount': 0.0,
                'final_total': cart_total
            }

        calculation = self.calculate_discount_amount(eligibility['discount'], cart_total)

        # Increment usage count
        self.increment_usage_count(code)

        return {
            'success': True,
            'code': code,
            'original_total': cart_total,
            'discount_amount': calculation['discount_amount'],
            'final_total': calculation['final_total'],
            'discount_percentage': calculation['discount_percentage'],
            'capped_by_maximum': calculation['capped_by_maximum']
        }

    def increment_usage_count(self, code: str) -> None:
        """Increment the usage count for a discount code"""
        code = code.upper().strip()
        if code in self.discount_codes:
            self.discount_codes[code]['usage_count'] = \
                self.discount_codes[code].get('usage_count', 0) + 1

    def get_discount_info(self, code: str) -> Dict[str, Any]:
        """Get detailed information about a discount code"""
        validation = self.validate_discount_code(code)

        if not validation['valid']:
            return validation

        discount = validation['discount']
        return {
            'valid': True,
            'code': discount['code'],
            'percentage': discount['percentage'],
            'is_active': discount.get('is_active', True),
            'minimum_amount': discount.get('minimum_amount', 0.0),
            'maximum_discount': discount.get('maximum_discount'),
            'usage_limit': discount.get('usage_limit'),
            'usage_count': discount.get('usage_count', 0),
            'remaining_uses': (
                discount.get('usage_limit') - discount.get('usage_count', 0)
                if discount.get('usage_limit') else None
            ),
            'expires_at': discount.get('expires_at')
        }

    def list_active_discounts(self) -> List[Dict[str, Any]]:
        """List all active discount codes"""
        active_discounts = []
        current_time = datetime.now()

        for discount in self.discount_codes.values():
            if not discount.get('is_active', True):
                continue

            if 'expires_at' in discount and discount['expires_at'] < current_time:
                continue

            # Don't include usage limits reached
            usage_limit = discount.get('usage_limit')
            if usage_limit and discount.get('usage_count', 0) >= usage_limit:
                continue

            active_discounts.append({
                'code': discount['code'],
                'percentage': discount['percentage'],
                'minimum_amount': discount.get('minimum_amount', 0.0),
                'maximum_discount': discount.get('maximum_discount')
            })

        return active_discounts


@pytest.mark.unit
@pytest.mark.discount
@pytest.mark.service
class TestDiscountService:
    """Test cases for Discount Service functionality"""

    @pytest.fixture
    def discount_service(self):
        """Create discount service instance for testing"""
        return MockDiscountService()

    def test_validate_valid_discount_code(self, discount_service):
        """Test validation of valid discount code"""
        result = discount_service.validate_discount_code('SAVE10')

        assert result['valid'] is True
        assert 'discount' in result
        assert result['discount']['code'] == 'SAVE10'

    def test_validate_case_insensitive(self, discount_service):
        """Test case insensitive discount code validation"""
        test_cases = ['save10', 'Save10', 'SAVE10', 'sAvE10']

        for code in test_cases:
            result = discount_service.validate_discount_code(code)
            assert result['valid'] is True

    @pytest.mark.negative
    def test_validate_empty_discount_code(self, discount_service):
        """Test validation of empty discount code"""
        result = discount_service.validate_discount_code('')

        assert result['valid'] is False
        assert 'Invalid discount code format' in result['error']

    @pytest.mark.negative
    def test_validate_none_discount_code(self, discount_service):
        """Test validation of None discount code"""
        result = discount_service.validate_discount_code(None)

        assert result['valid'] is False
        assert 'Invalid discount code format' in result['error']

    @pytest.mark.negative
    def test_validate_nonexistent_discount_code(self, discount_service):
        """Test validation of non-existent discount code"""
        result = discount_service.validate_discount_code('NONEXISTENT')

        assert result['valid'] is False
        assert 'Discount code not found' in result['error']

    def test_eligibility_active_code(self, discount_service):
        """Test eligibility check for active discount code"""
        result = discount_service.check_discount_eligibility('SAVE10', 100.0)

        assert result['eligible'] is True
        assert 'discount' in result

    @pytest.mark.negative
    def test_eligibility_inactive_code(self, discount_service):
        """Test eligibility check for inactive discount code"""
        result = discount_service.check_discount_eligibility('SAVE15', 100.0)

        assert result['eligible'] is False
        assert 'inactive' in result['error']

    @pytest.mark.negative
    def test_eligibility_expired_code(self, discount_service):
        """Test eligibility check for expired discount code"""
        result = discount_service.check_discount_eligibility('EXPIRED', 100.0)

        assert result['eligible'] is False
        assert 'expired' in result['error']

    @pytest.mark.negative
    def test_eligibility_usage_limit_exceeded(self, discount_service):
        """Test eligibility check when usage limit is exceeded"""
        result = discount_service.check_discount_eligibility('SPECIAL50', 300.0)

        assert result['eligible'] is False
        assert 'usage limit' in result['error']

    @pytest.mark.negative
    def test_eligibility_minimum_amount_not_met(self, discount_service):
        """Test eligibility check when minimum amount is not met"""
        result = discount_service.check_discount_eligibility('SAVE20', 25.0)

        assert result['eligible'] is False
        assert 'Minimum order amount' in result['error']

    def test_eligibility_minimum_amount_met(self, discount_service):
        """Test eligibility check when minimum amount is met"""
        result = discount_service.check_discount_eligibility('SAVE20', 75.0)

        assert result['eligible'] is True

    def test_calculate_simple_discount(self, discount_service):
        """Test simple percentage discount calculation"""
        discount = {'percentage': 10.0}
        cart_total = 100.0

        result = discount_service.calculate_discount_amount(discount, cart_total)

        assert result['original_total'] == cart_total
        assert result['discount_percentage'] == 10.0
        assert result['discount_amount'] == 10.0
        assert result['final_total'] == 90.0
        assert result['capped_by_maximum'] is False

    def test_calculate_discount_with_maximum_cap(self, discount_service):
        """Test discount calculation with maximum discount cap"""
        discount = {'percentage': 50.0, 'maximum_discount': 25.0}
        cart_total = 100.0

        result = discount_service.calculate_discount_amount(discount, cart_total)

        # 50% of 100 = 50, but capped at 25
        assert result['discount_amount'] == 25.0
        assert result['final_total'] == 75.0
        assert result['capped_by_maximum'] is True

    def test_calculate_discount_below_maximum_cap(self, discount_service):
        """Test discount calculation below maximum cap"""
        discount = {'percentage': 20.0, 'maximum_discount': 50.0}
        cart_total = 100.0

        result = discount_service.calculate_discount_amount(discount, cart_total)

        # 20% of 100 = 20, below the 50 cap
        assert result['discount_amount'] == 20.0
        assert result['final_total'] == 80.0
        assert result['capped_by_maximum'] is False

    def test_apply_successful_discount(self, discount_service):
        """Test successful discount application"""
        original_usage_count = discount_service.discount_codes['SAVE10']['usage_count']

        result = discount_service.apply_discount_code('SAVE10', 100.0)

        assert result['success'] is True
        assert result['code'] == 'SAVE10'
        assert result['original_total'] == 100.0
        assert result['discount_amount'] == 10.0
        assert result['final_total'] == 90.0
        assert result['discount_percentage'] == 10.0

        # Check usage count was incremented
        assert discount_service.discount_codes['SAVE10']['usage_count'] == original_usage_count + 1

    @pytest.mark.negative
    def test_apply_invalid_discount_code(self, discount_service):
        """Test applying invalid discount code"""
        result = discount_service.apply_discount_code('INVALID', 100.0)

        assert result['success'] is False
        assert 'error' in result
        assert result['discount_amount'] == 0.0
        assert result['final_total'] == 100.0

    def test_get_discount_info_active_code(self, discount_service):
        """Test getting information about active discount code"""
        result = discount_service.get_discount_info('SAVE20')

        assert result['valid'] is True
        assert result['code'] == 'SAVE20'
        assert result['percentage'] == 20.0
        assert result['is_active'] is True
        assert result['minimum_amount'] == 50.0
        assert result['maximum_discount'] == 100.0
        assert result['usage_limit'] == 100
        assert result['usage_count'] == 25
        assert result['remaining_uses'] == 75

    def test_get_discount_info_no_usage_limit(self, discount_service):
        """Test getting info for discount with no usage limit"""
        result = discount_service.get_discount_info('SAVE10')

        assert result['valid'] is True
        assert result['usage_limit'] is None
        assert result['remaining_uses'] is None

    def test_get_discount_info_invalid_code(self, discount_service):
        """Test getting info for invalid discount code"""
        result = discount_service.get_discount_info('INVALID')

        assert result['valid'] is False
        assert 'error' in result

    def test_list_active_discounts(self, discount_service):
        """Test listing active discount codes"""
        result = discount_service.list_active_discounts()

        # Should include SAVE10 and SAVE20 (active, not expired, usage limit not reached)
        # Should exclude SAVE15 (inactive), EXPIRED (expired), SPECIAL50 (usage limit reached)
        assert len(result) == 2

        codes = [d['code'] for d in result]
        assert 'SAVE10' in codes
        assert 'SAVE20' in codes
        assert 'SAVE15' not in codes
        assert 'EXPIRED' not in codes
        assert 'SPECIAL50' not in codes

    def test_list_active_discounts_structure(self, discount_service):
        """Test structure of active discounts list"""
        result = discount_service.list_active_discounts()

        for discount in result:
            assert 'code' in discount
            assert 'percentage' in discount
            assert 'minimum_amount' in discount
            assert isinstance(discount['percentage'], (int, float))
            assert isinstance(discount['minimum_amount'], (int, float))

    @pytest.mark.edge_case
    def test_zero_percentage_discount(self, discount_service):
        """Test discount with zero percentage"""
        discount = {'percentage': 0.0}
        cart_total = 100.0

        result = discount_service.calculate_discount_amount(discount, cart_total)

        assert result['discount_amount'] == 0.0
        assert result['final_total'] == cart_total

    @pytest.mark.edge_case
    def test_hundred_percent_discount_with_cap(self, discount_service):
        """Test 100% discount with maximum cap"""
        discount = {'percentage': 100.0, 'maximum_discount': 50.0}
        cart_total = 100.0

        result = discount_service.calculate_discount_amount(discount, cart_total)

        assert result['discount_amount'] == 50.0  # Capped at 50
        assert result['final_total'] == 50.0
        assert result['capped_by_maximum'] is True

    @pytest.mark.boundary
    def test_minimum_amount_boundary(self, discount_service):
        """Test behavior exactly at minimum amount boundary"""
        # Test exactly at minimum amount
        result = discount_service.check_discount_eligibility('SAVE20', 50.0)
        assert result['eligible'] is True

        # Test just below minimum amount
        result = discount_service.check_discount_eligibility('SAVE20', 49.99)
        assert result['eligible'] is False

    @pytest.mark.boundary
    def test_usage_limit_boundary(self, discount_service):
        """Test behavior exactly at usage limit boundary"""
        # Get current usage count for SPECIAL50 (should be 10)
        original_count = discount_service.discount_codes['SPECIAL50']['usage_count']
        usage_limit = discount_service.discount_codes['SPECIAL50']['usage_limit']

        assert original_count == usage_limit  # Should be at limit

        result = discount_service.check_discount_eligibility('SPECIAL50', 300.0)
        assert result['eligible'] is False

    @pytest.mark.parametrize("cart_total,expected_discount", [
        (100.0, 10.0),   # 10% of 100
        (0.0, 0.0),      # 10% of 0
        (0.01, 0.0),     # 10% of 0.01, rounded to 0.0
        (999.99, 100.0), # 10% of 999.99, capped at 100 (SAVE20 limit)
    ])
    def test_various_cart_totals(self, discount_service, cart_total, expected_discount):
        """Test discount calculation with various cart totals"""
        result = discount_service.apply_discount_code('SAVE20', cart_total)

        if expected_discount > 0:
            assert result['success'] is True if cart_total >= 50.0 else False
            if result['success']:
                assert result['discount_amount'] == expected_discount

    @pytest.mark.performance
    def test_bulk_discount_applications(self, discount_service):
        """Test performance of multiple discount applications"""
        import time

        codes = ['SAVE10', 'SAVE20']
        start_time = time.time()

        for i in range(1000):
            code = codes[i % len(codes)]
            discount_service.apply_discount_code(code, 100.0)

        end_time = time.time()
        processing_time = end_time - start_time

        # Should process 1000 applications quickly
        assert processing_time < 1.0  # Less than 1 second

    def test_increment_usage_count_nonexistent_code(self, discount_service):
        """Test incrementing usage count for non-existent code"""
        # Should not raise an exception
        discount_service.increment_usage_count('NONEXISTENT')

    def test_increment_usage_count_case_insensitive(self, discount_service):
        """Test increment usage count is case insensitive"""
        original_count = discount_service.discount_codes['SAVE10']['usage_count']

        discount_service.increment_usage_count('save10')

        assert discount_service.discount_codes['SAVE10']['usage_count'] == original_count + 1