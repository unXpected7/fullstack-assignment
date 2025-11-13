import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.mark.unit
@pytest.mark.api
@pytest.mark.cart
class TestCartAPI:
    """Test cases for Cart API endpoints"""

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_add_to_cart_success(self, test_client, sample_product_data,
                                      async_mock_product_service):
        """Test successfully adding item to cart"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 2
            })

            assert response.status_code == 200
            data = response.json()
            assert "Item added to cart" in data["message"]
            assert "session_id" in data
            assert len(data["session_id"]) > 0

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_add_to_cart_product_not_found(self, test_client,
                                                async_mock_product_service):
        """Test adding non-existent product to cart"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "non_existent",
                "quantity": 1
            })

            assert response.status_code == 404
            assert "Product not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_add_to_cart_insufficient_stock(self, test_client, sample_product_data,
                                                async_mock_product_service):
        """Test adding item with insufficient stock"""
        insufficient_stock_product = sample_product_data.copy()
        insufficient_stock_product["stock"] = 1

        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = insufficient_stock_product

            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 5  # Request more than available stock
            })

            assert response.status_code == 400
            assert "Insufficient stock" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_add_to_cart_invalid_quantity(self, test_client, sample_product_data,
                                              async_mock_product_service):
        """Test adding item with invalid quantity"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            # Test zero quantity
            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 0
            })
            assert response.status_code == 422  # Validation error

            # Test negative quantity
            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": -1
            })
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_add_to_cart_missing_fields(self, test_client):
        """Test adding item with missing required fields"""
        # Missing product_id
        response = test_client.post("/api/v1/cart/items", json={
            "quantity": 1
        })
        assert response.status_code == 422

        # Missing quantity
        response = test_client.post("/api/v1/cart/items", json={
            "product_id": "prod_001"
        })
        assert response.status_code == 422

    @pytest.mark.happy_path
    def test_get_cart_empty(self, test_client):
        """Test getting empty cart"""
        response = test_client.get("/api/v1/cart")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["subtotal"] == 0.0
        assert data["discount"] == 0.0
        assert data["shipping"] == 0.0
        assert data["total"] == 0.0

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_get_cart_with_items(self, test_client, sample_product_data,
                                     async_mock_product_service):
        """Test getting cart with items"""
        # Add item to cart first
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 2
            })
            session_id = add_response.json()["session_id"]

            # Get cart
            response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            assert response.status_code == 200
            data = response.json()
            assert len(data["items"]) == 1
            assert data["items"][0]["product_id"] == "prod_001"
            assert data["items"][0]["quantity"] == 2
            assert data["items"][0]["vendor_id"] == sample_product_data["vendor_id"]
            assert data["subtotal"] == sample_product_data["price"] * 2

    @pytest.mark.happy_path
    def test_get_cart_with_session_id(self, test_client):
        """Test getting cart with specific session ID"""
        session_id = "test_session_123"
        response = test_client.get(f"/api/v1/cart?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_update_item_quantity(self, test_client, sample_product_data,
                                       async_mock_product_service):
        """Test updating item quantity"""
        # Add item first
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session_id = add_response.json()["session_id"]

            # Get cart to find item ID
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            item_id = cart_response.json()["items"][0]["id"]

            # Update quantity
            response = test_client.put(f"/api/v1/cart/items/{item_id}?session_id={session_id}",
                                     json={"quantity": 5})

            assert response.status_code == 200
            assert "Quantity updated" in response.json()["message"]

            # Verify update
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            assert cart_response.json()["items"][0]["quantity"] == 5

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_update_item_quantity_invalid(self, test_client, sample_product_data,
                                              async_mock_product_service):
        """Test updating item quantity with invalid values"""
        # Add item first
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session_id = add_response.json()["session_id"]

            # Get cart to find item ID
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            item_id = cart_response.json()["items"][0]["id"]

            # Try to update with quantity 0
            response = test_client.put(f"/api/v1/cart/items/{item_id}?session_id={session_id}",
                                     json={"quantity": 0})
            assert response.status_code == 400
            assert "Quantity must be at least 1" in response.json()["detail"]

            # Try to update with negative quantity
            response = test_client.put(f"/api/v1/cart/items/{item_id}?session_id={session_id}",
                                     json={"quantity": -1})
            assert response.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_update_nonexistent_item(self, test_client):
        """Test updating non-existent item"""
        response = test_client.put("/api/v1/cart/items/99999?session_id=test_session",
                                 json={"quantity": 2})
        assert response.status_code == 404
        assert "Item not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_remove_item(self, test_client, sample_product_data,
                             async_mock_product_service):
        """Test removing item from cart"""
        # Add item first
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session_id = add_response.json()["session_id"]

            # Get cart to find item ID
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            item_id = cart_response.json()["items"][0]["id"]

            # Remove item
            response = test_client.delete(f"/api/v1/cart/items/{item_id}?session_id={session_id}")
            assert response.status_code == 200
            assert "Item removed" in response.json()["message"]

            # Verify item is removed
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            assert len(cart_response.json()["items"]) == 0

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_remove_nonexistent_item(self, test_client):
        """Test removing non-existent item"""
        response = test_client.delete("/api/v1/cart/items/99999?session_id=test_session")
        assert response.status_code == 404
        assert "Item not found" in response.json()["detail"]

    @pytest.mark.happy_path
    def test_clear_cart(self, test_client):
        """Test clearing entire cart"""
        session_id = "test_session_clear"
        response = test_client.delete(f"/api/v1/cart?session_id={session_id}")
        assert response.status_code == 200
        assert "Cart cleared" in response.json()["message"]

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_clear_cart_with_items(self, test_client, sample_product_data,
                                       async_mock_product_service):
        """Test clearing cart with items"""
        # Add items first
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session_id = add_response.json()["session_id"]

            # Clear cart
            response = test_client.delete(f"/api/v1/cart?session_id={session_id}")
            assert response.status_code == 200
            assert "Cart cleared" in response.json()["message"]

            # Verify cart is empty
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            assert len(cart_response.json()["items"]) == 0

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_apply_discount_code(self, test_client, sample_product_data,
                                     async_mock_product_service):
        """Test applying discount code"""
        # Add item to cart
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 10  # $999.90 total
            })
            session_id = add_response.json()["session_id"]

            # Apply discount
            response = test_client.post(f"/api/v1/cart/discount?session_id={session_id}",
                                     json={"code": "SAVE10"})
            assert response.status_code == 200
            data = response.json()
            assert "Discount code applied" in data["message"]
            assert data["code"] == "SAVE10"
            assert data["discount_amount"] == 99.99  # 10% of 999.90

    @pytest.mark.asyncio
    @pytest.mark.negative
    async def test_apply_invalid_discount_code(self, test_client, sample_product_data,
                                             async_mock_product_service):
        """Test applying invalid discount code"""
        # Add item to cart
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session_id = add_response.json()["session_id"]

            # Apply invalid discount
            response = test_client.post(f"/api/v1/cart/discount?session_id={session_id}",
                                     json={"code": "INVALID"})
            assert response.status_code == 404
            assert "Invalid discount code" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_remove_discount_code(self, test_client, sample_product_data,
                                      async_mock_product_service):
        """Test removing discount code"""
        # Add item and apply discount
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            add_response = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 10
            })
            session_id = add_response.json()["session_id"]

            test_client.post(f"/api/v1/cart/discount?session_id={session_id}",
                           json={"code": "SAVE10"})

            # Remove discount
            response = test_client.delete(f"/api/v1/cart/discount?session_id={session_id}")
            assert response.status_code == 200
            assert "Discount code removed" in response.json()["message"]
            assert response.json()["discount_amount"] == 0

    @pytest.mark.asyncio
    @pytest.mark.happy_path
    async def test_add_duplicate_items_to_cart(self, test_client, sample_product_data,
                                              async_mock_product_service):
        """Test adding duplicate items to cart (should update quantity)"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            # Add item first time
            response1 = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 2
            })
            session_id = response1.json()["session_id"]

            # Add same item second time
            response2 = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 3
            })

            assert response2.status_code == 200
            assert "Item added to cart" in response2.json()["message"]

            # Check cart - should have one item with quantity 5
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            items = cart_response.json()["items"]
            assert len(items) == 1
            assert items[0]["quantity"] == 5

    @pytest.mark.asyncio
    @pytest.mark.edge_case
    async def test_cart_with_multiple_vendors_shipping(self, test_client,
                                                     sample_product_data_multiple_vendors,
                                                     async_mock_product_service):
        """Test shipping calculation with multiple vendors"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            def mock_fetch_side_effect(product_id):
                return sample_product_data_multiple_vendors.get(product_id)

            mock_fetch.side_effect = mock_fetch_side_effect

            # Add items from different vendors
            response1 = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_high_value",
                "quantity": 1
            })
            session_id = response1.json()["session_id"]

            test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_low_value",
                "quantity": 1,
                "session_id": session_id
            })

            # Check totals
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            data = cart_response.json()

            # High vendor: $850 >= $800 (free shipping)
            # Low vendor: $750 < $800 ($100 shipping)
            # Total shipping: $100
            assert data["shipping"] == 100.0
            assert data["subtotal"] == 1600.0  # 850 + 750
            assert data["total"] == 1700.0     # 1600 + 100

    @pytest.mark.asyncio
    @pytest.mark.boundary
    async def test_vendor_shipping_threshold_boundary(self, test_client,
                                                    boundary_test_data,
                                                    async_mock_product_service):
        """Test vendor shipping rules at boundary conditions"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            def mock_fetch_side_effect(product_id):
                return boundary_test_data.get(product_id)

            mock_fetch.side_effect = mock_fetch_side_effect

            # Add item exactly at shipping threshold
            response = test_client.post("/api/v1/cart/items", json={
                "product_id": "exact_shipping_threshold",
                "quantity": 1
            })
            session_id = response.json()["session_id"]

            # Check shipping - should be free (exactly $800)
            cart_response = test_client.get(f"/api/v1/cart?session_id={session_id}")
            data = cart_response.json()
            assert data["shipping"] == 0.0

    def test_cart_response_structure(self, test_client):
        """Test that cart response has correct structure"""
        response = test_client.get("/api/v1/cart")
        assert response.status_code == 200

        data = response.json()
        required_fields = ['session_id', 'items', 'subtotal', 'discount', 'shipping', 'total']

        for field in required_fields:
            assert field in data

        assert isinstance(data['items'], list)
        assert isinstance(data['subtotal'], (int, float))
        assert isinstance(data['discount'], (int, float))
        assert isinstance(data['shipping'], (int, float))
        assert isinstance(data['total'], (int, float))

    @pytest.mark.asyncio
    @pytest.mark.security
    async def test_cart_session_isolation(self, test_client, sample_product_data,
                                         async_mock_product_service):
        """Test that different sessions are isolated"""
        with patch('main.fetch_product_from_external_api', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_product_data

            # Add item to session 1
            response1 = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 1
            })
            session1 = response1.json()["session_id"]

            # Add item to session 2
            response2 = test_client.post("/api/v1/cart/items", json={
                "product_id": "prod_001",
                "quantity": 2
            })
            session2 = response2.json()["session_id"]

            # Verify sessions are different
            assert session1 != session2

            # Check cart contents are isolated
            cart1 = test_client.get(f"/api/v1/cart?session_id={session1}")
            cart2 = test_client.get(f"/api/v1/cart?session_id={session2}")

            assert cart1.json()["items"][0]["quantity"] == 1
            assert cart2.json()["items"][0]["quantity"] == 2