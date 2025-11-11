// API client for shopping cart operations
class APIClient {
    constructor(baseURL = 'http://localhost:8000/api/v1') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...(options.headers || {}) },
            ...options,
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Cart operations
    async getCart(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart${params}`);
    }

    async addToCart(item, sessionId = null) {
        const body = JSON.stringify(item);
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart/items${params}`, {
            method: 'POST',
            body,
        });
    }

    async updateItemQuantity(itemId, quantity, sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart/items/${itemId}${params}`, {
            method: 'PUT',
            body: JSON.stringify({ quantity }),
        });
    }

    async removeItem(itemId, sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart/items/${itemId}${params}`, {
            method: 'DELETE',
        });
    }

    async clearCart(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart${params}`, {
            method: 'DELETE',
        });
    }

    // Discount operations
    async applyDiscountCode(code, sessionId = null) {
        const body = JSON.stringify({ code });
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart/discount${params}`, {
            method: 'POST',
            body,
        });
    }

    async removeDiscountCode(sessionId = null) {
        const params = sessionId ? `?session_id=${sessionId}` : '';
        return this.request(`/cart/discount${params}`, {
            method: 'DELETE',
        });
    }

    // Session management
    async createSession() {
        return this.request('/cart', {
            method: 'GET',
        });
    }

    // Product service configuration
    async getProductServiceConfig() {
        return this.request('/config/product-service');
    }

    async configureProductService(config) {
        return this.request('/config/product-service', {
            method: 'POST',
            body: JSON.stringify(config),
        });
    }
}

// Export singleton instance
export const apiClient = new APIClient();
export default APIClient;