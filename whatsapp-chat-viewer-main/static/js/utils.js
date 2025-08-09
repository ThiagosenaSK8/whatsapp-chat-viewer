// Utility functions

function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 minute
    if (diff < 60000) {
        return 'agora';
    }
    
    // Less than 1 hour
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}min`;
    }
    
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h`;
    }
    
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d`;
    }
    
    // More than 7 days - show date
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit'
    });
}

function formatTime(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleTimeString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatPhoneNumber(phone) {
    // Remove non-numeric characters
    const numbers = phone.replace(/\D/g, '');
    
    // Check if it's a Brazilian phone number
    if (numbers.length === 13 && numbers.startsWith('55')) {
        const ddd = numbers.substr(2, 2);
        const number = numbers.substr(4);
        return `+55 (${ddd}) ${number.substr(0, 5)}-${number.substr(5)}`;
    }
    
    // Return original if not Brazilian format
    return phone;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    }
}

function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        return new Promise((resolve, reject) => {
            if (document.execCommand('copy')) {
                textArea.remove();
                resolve();
            } else {
                textArea.remove();
                reject();
            }
        });
    }
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(amount);
}

function isValidPhoneNumber(phone) {
    // Basic phone validation - adjust as needed
    const phoneRegex = /^\+?\d{10,15}$/;
    return phoneRegex.test(phone.replace(/\s/g, ''));
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

function smoothScrollTo(element, duration = 300) {
    const targetPosition = element.offsetTop;
    const startPosition = window.pageYOffset;
    const distance = targetPosition - startPosition;
    let startTime = null;

    function animation(currentTime) {
        if (startTime === null) startTime = currentTime;
        const timeElapsed = currentTime - startTime;
        const run = ease(timeElapsed, startPosition, distance, duration);
        window.scrollTo(0, run);
        if (timeElapsed < duration) requestAnimationFrame(animation);
    }

    function ease(t, b, c, d) {
        t /= d / 2;
        if (t < 1) return c / 2 * t * t + b;
        t--;
        return -c / 2 * (t * (t - 2) - 1) + b;
    }

    requestAnimationFrame(animation);
}

// Loading state management
function showLoadingState(element, text = 'Carregando...') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = `
            <div class="flex items-center justify-center p-4">
                <i class="ri-loader-4-line animate-spin text-xl mr-2"></i>
                <span>${text}</span>
            </div>
        `;
    }
}

function hideLoadingState(element, content = '') {
    if (typeof element === 'string') {
        element = document.getElementById(element);
    }
    
    if (element) {
        element.innerHTML = content;
    }
}

// Local storage helpers
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : defaultValue;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return defaultValue;
    }
}

function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Error removing from localStorage:', error);
        return false;
    }
}

// Network helpers
async function fetchWithTimeout(url, options = {}, timeout = 10000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

// Export functions for use in other scripts
window.utils = {
    formatDate,
    formatTime,
    formatPhoneNumber,
    escapeHtml,
    debounce,
    throttle,
    copyToClipboard,
    formatCurrency,
    isValidPhoneNumber,
    isValidEmail,
    generateId,
    smoothScrollTo,
    showLoadingState,
    hideLoadingState,
    saveToStorage,
    loadFromStorage,
    removeFromStorage,
    fetchWithTimeout
};

// Export specific functions to global scope for backward compatibility
window.formatDate = formatDate;
window.formatTime = formatTime;
window.formatPhoneNumber = formatPhoneNumber;
window.escapeHtml = escapeHtml;
window.debounce = debounce;
window.throttle = throttle;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.isValidPhoneNumber = isValidPhoneNumber;
window.isValidEmail = isValidEmail;
window.generateId = generateId;
window.smoothScrollTo = smoothScrollTo;
window.showLoadingState = showLoadingState;
window.hideLoadingState = hideLoadingState;
window.saveToStorage = saveToStorage;
window.loadFromStorage = loadFromStorage;
window.removeFromStorage = removeFromStorage;
window.fetchWithTimeout = fetchWithTimeout;