class ShoppingCart {
    constructor() {
        this.sessionId = null;
        this.cartData = null;
        this.currentDiscountCode = null;
        this.apiBase = 'http://localhost:8000/api/v1';

        this.init();
    }

    async init() {
        try {
            this.sessionId = this.getSessionId() || await this.createNewSession();
            await this.loadCart();
            this.showSessionInfo();
        } catch (error) {
            this.showError('Failed to initialize cart: ' + error.message);
        }
    }

    getSessionId() {
        return localStorage.getItem('cart_session_id');
    }

    setSessionId(sessionId) {
        localStorage.setItem('cart_session_id', sessionId);
        this.sessionId = sessionId;
    }

    async createNewSession() {
        try {
            const response = await fetch(`${this.apiBase}/cart`, {
                method: 'GET'
            });
            const data = await response.json();
            this.setSessionId(data.session_id);
            return data.session_id;
        } catch (error) {
            throw new Error('Failed to create session');
        }
    }

    async loadCart() {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart?session_id=${this.sessionId}`);

            if (response.ok) {
                this.cartData = await response.json();
                this.currentDiscountCode = this.cartData.discount_code || null;
                this.renderCart();
                this.hideMessages();
            } else if (response.status === 404) {
                this.cartData = {
                    session_id: this.sessionId,
                    items: [],
                    subtotal: 0,
                    discount: 0,
                    shipping: 0,
                    total: 0
                };
                this.renderCart();
            } else {
                throw new Error('Failed to load cart');
            }
        } catch (error) {
            this.showError('Failed to load cart: ' + error.message);
        } finally {
            this.showLoading(false);
        }
    }

    async addItem(productId, quantity = 1) {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart/items`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    product_id: productId,
                    quantity: quantity
                }),
                // Include session in URL params
                ...(this.sessionId && { session_id: this.sessionId })
            });

            if (response.ok) {
                const data = await response.json();
                this.showSuccess('Item added to cart successfully!');
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to add item');
            }
        } catch (error) {
            this.showError('Failed to add item: ' + error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    async updateItemQuantity(itemId, quantity) {
        if (quantity < 1) {
            this.showError('Quantity must be at least 1');
            return false;
        }

        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart/items/${itemId}?session_id=${this.sessionId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quantity: quantity
                })
            });

            if (response.ok) {
                this.showSuccess('Quantity updated successfully!');
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update quantity');
            }
        } catch (error) {
            this.showError('Failed to update quantity: ' + error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    async removeItem(itemId) {
        if (!confirm('Are you sure you want to remove this item?')) {
            return false;
        }

        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart/items/${itemId}?session_id=${this.sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Item removed successfully!');
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to remove item');
            }
        } catch (error) {
            this.showError('Failed to remove item: ' + error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    async clearCart() {
        if (!confirm('Are you sure you want to clear your entire cart?')) {
            return false;
        }

        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart?session_id=${this.sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Cart cleared successfully!');
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to clear cart');
            }
        } catch (error) {
            this.showError('Failed to clear cart: ' + error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    async applyDiscountCode(code) {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart/discount?session_id=${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    code: code.trim().toUpperCase()
                })
            });

            if (response.ok) {
                const data = await response.json();
                this.currentDiscountCode = code.trim().toUpperCase();
                this.showSuccess(`Discount code "${this.currentDiscountCode}" applied successfully!`);
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to apply discount code');
            }
        } catch (error) {
            this.showError(error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    async removeDiscountCode() {
        this.showLoading(true);
        try {
            const response = await fetch(`${this.apiBase}/cart/discount?session_id=${this.sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.currentDiscountCode = null;
                this.showSuccess('Discount code removed successfully!');
                await this.loadCart();
                return true;
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to remove discount code');
            }
        } catch (error) {
            this.showError('Failed to remove discount code: ' + error.message);
            return false;
        } finally {
            this.showLoading(false);
        }
    }

    renderCart() {
        const emptyCart = document.getElementById('empty-cart');
        const cartItemsSection = document.getElementById('cart-items-section');
        const orderSummary = document.getElementById('order-summary');

        if (this.cartData.items.length === 0) {
            emptyCart.style.display = 'block';
            cartItemsSection.style.display = 'none';
            orderSummary.style.display = 'none';
        } else {
            emptyCart.style.display = 'none';
            cartItemsSection.style.display = 'block';
            orderSummary.style.display = 'block';

            this.renderCartItems();
            this.updateOrderSummary();
        }
    }

    renderCartItems() {
        const container = document.getElementById('cart-items-container');
        container.innerHTML = '';

        this.cartData.items.forEach(item => {
            const itemElement = this.createCartItemElement(item);
            container.appendChild(itemElement);
        });
    }

    createCartItemElement(item) {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'cart-item';
        itemDiv.innerHTML = `
            <img src="${item.image_url || 'https://via.placeholder.com/80x80'}"
                 alt="${item.product_name}"
                 class="item-image"
                 onerror="this.src='https://via.placeholder.com/80x80'">

            <div class="item-details">
                <div class="item-name">${item.product_name}</div>
                <div class="item-vendor">${item.vendor_name}</div>
            </div>

            <div class="item-price">$${item.price.toFixed(2)}</div>

            <div class="quantity-controls">
                <button class="quantity-btn" onclick="cart.updateItemQuantity(${item.id}, ${item.quantity - 1})">-</button>
                <input type="number"
                       class="quantity-input"
                       value="${item.quantity}"
                       min="1"
                       onchange="cart.updateItemQuantity(${item.id}, parseInt(this.value))">
                <button class="quantity-btn" onclick="cart.updateItemQuantity(${item.id}, ${item.quantity + 1})">+</button>
            </div>

            <button class="remove-btn" onclick="cart.removeItem(${item.id})">✕</button>
        `;

        return itemDiv;
    }

    updateOrderSummary() {
        document.getElementById('subtotal').textContent = `$${this.cartData.subtotal.toFixed(2)}`;
        document.getElementById('discount').textContent = `-$${this.cartData.discount.toFixed(2)}`;
        document.getElementById('shipping').textContent = `$${this.cartData.shipping.toFixed(2)}`;
        document.getElementById('total').textContent = `$${this.cartData.total.toFixed(2)}`;

        // Update discount applied display
        const discountApplied = document.getElementById('discount-applied');
        if (this.currentDiscountCode) {
            discountApplied.textContent = `Code "${this.currentDiscountCode}" applied`;
            discountApplied.style.display = 'block';
        } else {
            discountApplied.style.display = 'none';
        }

        // Update checkout button
        const checkoutBtn = document.querySelector('.checkout-btn');
        checkoutBtn.disabled = this.cartData.items.length === 0;
    }

    showSessionInfo() {
        const sessionInfo = document.getElementById('session-info');
        if (this.sessionId) {
            const shortId = this.sessionId.substring(0, 8);
            sessionInfo.innerHTML = `<span style="color: #6c757d;">Session: ${shortId}</span>`;
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (show) {
            loading.classList.add('show');
        } else {
            loading.classList.remove('show');
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        errorDiv.textContent = message;
        errorDiv.classList.add('show');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDiv.classList.remove('show');
        }, 5000);
    }

    showSuccess(message) {
        const successDiv = document.getElementById('success-message');
        successDiv.textContent = message;
        successDiv.classList.add('show');

        // Auto-hide after 3 seconds
        setTimeout(() => {
            successDiv.classList.remove('show');
        }, 3000);
    }

    hideMessages() {
        document.getElementById('error-message').classList.remove('show');
        document.getElementById('success-message').classList.remove('show');
    }

    checkout() {
        if (this.cartData.items.length === 0) {
            this.showError('Your cart is empty!');
            return;
        }

        // Here you would typically redirect to checkout page or show checkout form
        alert(`Checkout would proceed with total: $${this.cartData.total.toFixed(2)}`);
        console.log('Checkout data:', this.cartData);
    }
}

// Initialize the cart when the page loads
let cart;
document.addEventListener('DOMContentLoaded', function() {
    cart = new ShoppingCart();
});

// Global functions for HTML onclick handlers
function clearCart() {
    cart.clearCart();
}

function applyDiscount() {
    const codeInput = document.getElementById('discount-code');
    const code = codeInput.value.trim();

    if (!code) {
        cart.showError('Please enter a discount code');
        return;
    }

    cart.applyDiscountCode(code).then(() => {
        codeInput.value = '';
    });
}

function checkout() {
    cart.checkout();
}

// Handle Enter key for discount code input
document.addEventListener('DOMContentLoaded', function() {
    const discountInput = document.getElementById('discount-code');
    discountInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            applyDiscount();
        }
    });
});

// Add some sample products for testing
window.addSampleProducts = async function() {
    const sampleProducts = [
        { id: 'prod_001', name: 'Wireless Headphones', vendor: 'TechCorp' },
        { id: 'prod_002', name: 'Coffee Maker', vendor: 'HomeGoods Inc' },
        { id: 'prod_003', name: 'Running Shoes', vendor: 'SportGear' },
        { id: 'prod_004', name: 'Laptop Stand', vendor: 'TechCorp' },
        { id: 'prod_005', name: 'Desk Lamp', vendor: 'HomeGoods Inc' }
    ];

    for (const product of sampleProducts) {
        await cart.addItem(product.id, 1);
    }
};

// Add debug function for testing
window.debugCart = function() {
    console.log('Current cart data:', cart.cartData);
    console.log('Session ID:', cart.sessionId);
    console.log('Current discount:', cart.currentDiscountCode);
};