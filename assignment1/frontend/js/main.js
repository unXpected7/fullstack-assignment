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

// Export main functions for debugging and testing
export {
    initializeApp,
    checkAppHealth,
    cart
};