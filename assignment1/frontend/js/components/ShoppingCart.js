// Shopping cart main class
import { apiClient } from '../api/client.js';
import { storage, showLoading, showToast } from '../utils/domUtils.js';

export class ShoppingCart {
    constructor(client = apiClient) {
        this.sessionId = null;
        this.cartData = null;
        this.currentDiscountCode = null;
        this.apiClient = client;
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

    // Session management
    getSessionId() {
        return storage.get('cart_session_id');
    }

    setSessionId(sessionId) {
        storage.set('cart_session_id', sessionId);
        this.sessionId = sessionId;
    }

    async createNewSession() {
        try {
            const data = await this.apiClient.createSession();
            this.setSessionId(data.session_id);
            return data.session_id;
        } catch (error) {
            throw new Error('Failed to create session');
        }
    }

    // Cart operations
    async loadCart() {
        showLoading(true);
        try {
            this.cartData = await this.apiClient.getCart(this.sessionId);
            this.currentDiscountCode = this.cartData.discount_code || null;
            this.renderCart();
            this.updateCartSummary();
        } catch (error) {
            this.showError('Failed to load cart: ' + error.message);
        } finally {
            showLoading(false);
        }
    }

    async addToCart(productId, quantity = 1) {
        try {
            await this.apiClient.addToCart({
                product_id: productId,
                quantity: quantity
            }, this.sessionId);

            showSuccess('Item added to cart');
            await this.loadCart();
        } catch (error) {
            this.showError('Failed to add item: ' + error.message);
        }
    }

    async updateItemQuantity(itemId, quantity) {
        if (quantity < 1) {
            this.removeItem(itemId);
            return;
        }

        try {
            await this.apiClient.updateItemQuantity(itemId, quantity, this.sessionId);
            await this.loadCart();
        } catch (error) {
            this.showError('Failed to update quantity: ' + error.message);
        }
    }

    async removeItem(itemId) {
        try {
            await this.apiClient.removeItem(itemId, this.sessionId);
            showSuccess('Item removed from cart');
            await this.loadCart();
        } catch (error) {
            this.showError('Failed to remove item: ' + error.message);
        }
    }

    async clearCart() {
        if (!confirm('Are you sure you want to clear your cart?')) return;

        try {
            await this.apiClient.clearCart(this.sessionId);
            showSuccess('Cart cleared');
            await this.loadCart();
        } catch (error) {
            this.showError('Failed to clear cart: ' + error.message);
        }
    }

    // Discount operations
    async applyDiscountCode(code) {
        try {
            const result = await this.apiClient.applyDiscountCode(code, this.sessionId);
            this.currentDiscountCode = code;
            showSuccess(`Discount applied! You saved $${result.discount_amount}`);
            await this.loadCart();
        } catch (error) {
            this.showError('Invalid discount code');
        }
    }

    async removeDiscountCode() {
        try {
            await this.apiClient.removeDiscountCode(this.sessionId);
            this.currentDiscountCode = null;
            showSuccess('Discount code removed');
            await this.loadCart();
        } catch (error) {
            this.showError('Failed to remove discount code');
        }
    }

    // Rendering methods
    renderCart() {
        const cartContainer = $('#cartContainer');
        if (!cartContainer) return;

        if (!this.cartData.items || this.cartData.items.length === 0) {
            cartContainer.innerHTML = `
                <div class="cart-empty">
                    <div class="empty-icon">🛒</div>
                    <div class="empty-message">Your cart is empty</div>
                    <div class="empty-subtitle">Add some items to get started!</div>
                </div>
            `;
            return;
        }

        const cartHTML = this.cartData.items.map(item => `
            <div class="cart-item" data-item-id="${item.id}">
                <img src="${item.image_url || 'https://via.placeholder.com/80'}"
                     alt="${item.product_name}"
                     class="item-image"
                     onerror="this.src='https://via.placeholder.com/80'">
                <div class="item-details">
                    <div class="item-name">${item.product_name}</div>
                    <div class="item-vendor">by ${item.vendor_name}</div>
                    <div class="item-price">$${item.price.toFixed(2)}</div>
                </div>
                <div class="item-controls">
                    <div class="quantity-controls">
                        <button class="quantity-btn" onclick="cart.decrementQuantity(${item.id})">-</button>
                        <input type="number" class="quantity-input" value="${item.quantity}"
                               min="1" onchange="cart.updateQuantity(${item.id}, this.value)">
                        <button class="quantity-btn" onclick="cart.incrementQuantity(${item.id})">+</button>
                    </div>
                    <button class="remove-btn" onclick="cart.removeItem(${item.id})">Remove</button>
                </div>
            </div>
        `).join('');

        cartContainer.innerHTML = cartHTML;
    }

    updateCartSummary() {
        const summaryElement = $('#cartSummary');
        if (!summaryElement) return;

        const discountAmount = this.cartData.discount || 0;
        const summaryHTML = `
            <div class="summary-header">Order Summary</div>
            <div class="summary-row">
                <span class="summary-label">Subtotal</span>
                <span class="summary-value">$${this.cartData.subtotal.toFixed(2)}</span>
            </div>
            ${discountAmount > 0 ? `
                <div class="summary-row">
                    <span class="summary-label">Discount (${this.currentDiscountCode})</span>
                    <span class="summary-value discount">-$${discountAmount.toFixed(2)}</span>
                </div>
            ` : ''}
            <div class="summary-row">
                <span class="summary-label">Shipping</span>
                <span class="summary-value">$${this.cartData.shipping.toFixed(2)}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-row">
                <span class="summary-label">Total</span>
                <span class="summary-value total">$${this.cartData.total.toFixed(2)}</span>
            </div>
            ${this.currentDiscountCode ? `
                <div class="discount-section">
                    <button class="remove-discount-btn" onclick="cart.removeDiscountCode()">
                        Remove Discount
                    </button>
                </div>
            ` : ''}
            <div class="discount-section">
                <input type="text" class="discount-input" id="discountInput"
                       placeholder="Enter discount code" maxlength="20">
                <button class="apply-discount-btn" onclick="cart.applyDiscountCode()">
                    Apply
                </button>
            </div>
            <div class="action-buttons">
                <button class="clear-cart-btn" onclick="cart.clearCart()">
                    Clear Cart
                </button>
                <button class="checkout-btn" onclick="checkout()">
                    Checkout
                </button>
            </div>
        `;

        summaryElement.innerHTML = summaryHTML;
    }

    // Quantity management helpers
    incrementQuantity(itemId) {
        this.updateQuantity(itemId, parseInt(this.getQuantityInput(itemId).value) + 1);
    }

    decrementQuantity(itemId) {
        const input = this.getQuantityInput(itemId);
        const currentValue = parseInt(input.value);
        if (currentValue > 1) {
            this.updateQuantity(itemId, currentValue - 1);
        }
    }

    updateQuantity(itemId, newQuantity) {
        this.updateItemQuantity(itemId, parseInt(newQuantity));
    }

    getQuantityInput(itemId) {
        return $(`[data-item-id="${itemId}"] .quantity-input`);
    }

    // UI helpers
    showSessionInfo() {
        const sessionInfo = $('#sessionInfo');
        if (sessionInfo) {
            sessionInfo.textContent = `Session: ${this.sessionId.substring(0, 8)}...`;
        }
    }

    showError(message) {
        showToast(message, 'error');
    }

    showSuccess(message) {
        showToast(message, 'success');
    }
}

// Global checkout function
function checkout() {
    if (!cart.cartData || cart.cartData.items.length === 0) {
        showToast('Your cart is empty', 'warning');
        return;
    }

    const total = cart.cartData.total;
    showToast(`Redirecting to checkout with total: $${total.toFixed(2)}`, 'success');

    // In a real application, this would redirect to checkout page
    setTimeout(() => {
        console.log('Would redirect to checkout with total:', total);
    }, 1500);
}

// Export shopping cart instance
export let cart;