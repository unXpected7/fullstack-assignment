// DOM manipulation utilities
export const $ = (selector, context = document) => context.querySelector(selector);
export const $$ = (selector, context = document) => context.querySelectorAll(selector);

// Create element utility
export const createElement = (tag, attributes = {}, children = []) => {
    const element = document.createElement(tag);

    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'className') {
            element.className = value;
        } else if (key === 'innerHTML') {
            element.innerHTML = value;
        } else if (key === 'textContent') {
            element.textContent = value;
        } else {
            element.setAttribute(key, value);
        }
    });

    children.forEach(child => {
        if (typeof child === 'string') {
            element.appendChild(document.createTextNode(child));
        } else {
            element.appendChild(child);
        }
    });

    return element;
};

// Event delegation utility
export const addEventDelegate = (parentSelector, eventType, childSelector, handler) => {
    document.addEventListener(eventType, (event) => {
        const parentElement = $(parentSelector);
        if (!parentElement) return;

        const childElement = event.target.closest(childSelector);
        if (childElement && parentElement.contains(childElement)) {
            handler.call(childElement, event);
        }
    });
};

// Load state management
export const showLoading = (show = true) => {
    const loadingOverlay = $('#loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = show ? 'flex' : 'none';
    }
};

export const showToast = (message, type = 'info') => {
    const toast = createElement('div', {
        className: `toast toast-${type}`,
        id: 'toast'
    }, [message]);

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
};

export const showError = (message) => showToast(message, 'error');
export const showSuccess = (message) => showToast(message, 'success');
export const showWarning = (message) => showToast(message, 'warning');
export const showInfo = (message) => showToast(message, 'info');

// Form utilities
export const getInputValue = (selector) => $(selector).value;
export const setInputValue = (selector, value) => {
    const element = $(selector);
    if (element) element.value = value;
};

export const clearForm = (formSelector) => {
    const form = $(formSelector);
    if (form) form.reset();
};

// Storage utilities
export const storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    },

    get: (key) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },

    remove: (key) => localStorage.removeItem(key),

    clear: () => localStorage.clear()
};