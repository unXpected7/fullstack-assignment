// Main application initialization
import { apiClient } from './api/client.js';
import { ShoppingCart } from './components/ShoppingCart.js';
import { storage, showLoading, showToast } from './utils/domUtils.js';

// Global cart instance
let cart;

// Initialize application when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// Initialize the shopping cart application
async function initializeApp() {
    try {
        // Set up global event handlers
        setupEventListeners();

        // Initialize the shopping cart
        cart = new ShoppingCart(apiClient);

        // Make cart globally available for inline handlers after initialization
        window.cart = cart;

        // Show loading state
        showLoading(true);

        // Initialize cart (this will handle session creation and loading)
        await cart.init();

        // Hide loading state
        showLoading(false);

        console.log('Shopping cart application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
        showToast('Failed to initialize shopping cart. Please refresh the page.', 'error');
        showLoading(false);
    }
}

// Setup global event listeners
function setupEventListeners() {
    // Setup discount code input enter key
    setupDiscountCodeInput();

    // Setup keyboard shortcuts
    setupKeyboardShortcuts();

    // Setup error handling
    setupErrorHandler();
}

// Setup discount code input
function setupDiscountCodeInput() {
    const discountInput = document.getElementById('discountInput');
    if (discountInput) {
        discountInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                const code = discountInput.value.trim();
                if (code) {
                    cart.applyDiscountCode(code);
                    discountInput.value = '';
                }
            }
        });
    }
}

// Setup keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', (event) => {
        // Ctrl/Cmd + K: Focus on discount code input
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const discountInput = document.getElementById('discountInput');
            if (discountInput) {
                discountInput.focus();
            }
        }

        // Escape: Clear any active inputs
        if (event.key === 'Escape') {
            const activeInputs = document.querySelectorAll('input:focus, textarea:focus');
            activeInputs.forEach(input => input.blur());
        }
    });
}

// Setup global error handler
function setupErrorHandler() {
    window.addEventListener('error', (event) => {
        console.error('Global error:', event.error);
        showToast('An unexpected error occurred. Please try again.', 'error');
    });

    window.addEventListener('unhandledrejection', (event) => {
        console.error('Unhandled promise rejection:', event.reason);
        showToast('Network error. Please check your connection.', 'error');
    });
}

// Application health check
async function checkAppHealth() {
    try {
        const response = await fetch('http://localhost:8000/');
        if (response.ok) {
            console.log('Backend is healthy');
            return true;
        }
    } catch (error) {
        console.error('Backend health check failed:', error);
        showToast('Backend service is unavailable. Some features may not work.', 'warning');
        return false;
    }
}

// Periodic health check
setInterval(checkAppHealth, 30000); // Check every 30 seconds

// Load and display available products
async function loadProducts() {
    try {
        showLoading(true);
        const response = await fetch('http://localhost:8000/api/v1/config/product-service');
        if (response.ok) {
            const config = await response.json();

            // If using mock products, display the sample products
            if (config.endpoint === 'mock') {
                displaySampleProducts();
            } else {
                // Would fetch from external API in a real implementation
                showToast('External product service not configured', 'warning');
            }
        } else {
            showToast('Failed to load product configuration', 'error');
        }
    } catch (error) {
        showToast('Failed to load products: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Display sample products that can be added to cart
function displaySampleProducts() {
    const sampleProducts = [
        { id: 'prod_001', name: 'Wireless Headphones', vendor: 'TechCorp', price: 99.99 },
        { id: 'prod_002', name: 'Coffee Maker', vendor: 'HomeGoods Inc', price: 149.99 },
        { id: 'prod_003', name: 'Running Shoes', vendor: 'SportGear', price: 129.99 },
        { id: 'prod_004', name: 'Laptop Stand', vendor: 'TechCorp', price: 89.99 },
        { id: 'prod_005', name: 'Desk Lamp', vendor: 'HomeGoods Inc', price: 79.99 }
    ];

    const container = document.getElementById('productsContainer');
    if (!container) return;

    container.innerHTML = '';

    sampleProducts.forEach(product => {
        const productElement = document.createElement('div');
        productElement.className = 'product-item';
        productElement.innerHTML = `
            <div class="product-info">
                <div class="product-name">${product.name}</div>
                <div class="product-vendor">${product.vendor}</div>
                <div class="product-price">$${product.price.toFixed(2)}</div>
            </div>
            <button class="add-to-cart-btn" onclick="addToCart('${product.id}', 1)">
                Add to Cart
            </button>
        `;
        container.appendChild(productElement);
    });
}

// Global function to add products to cart
async function addToCart(productId, quantity = 1) {
    if (cart) {
        await cart.addToCart(productId, quantity);
    } else {
        showToast('Cart not initialized. Please refresh the page.', 'error');
    }
}

// Make functions globally accessible for inline onclick handlers
window.loadProducts = loadProducts;
window.addToCart = addToCart;
window.cart = cart;

// Export main functions for debugging and testing
export {
    initializeApp,
    checkAppHealth,
    cart,
    loadProducts,
    addToCart
};