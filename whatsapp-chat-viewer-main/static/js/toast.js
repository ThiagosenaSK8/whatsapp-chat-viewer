// Toast notification system

let toastCounter = 0;

function showToast(message, type = 'info', duration = 4000) {
    const toastId = `toast-${++toastCounter}`;
    const container = document.getElementById('toast-container');
    
    if (!container) {
        console.error('Toast container not found');
        return;
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `
        transform transition-all duration-300 ease-in-out toast-item
        max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto
        ring-1 ring-black ring-opacity-5 overflow-hidden
        translate-x-full opacity-0
    `;
    
    // Get icon and colors based on type
    const { icon, bgColor, iconColor, borderColor } = getToastStyle(type);
    
    toast.innerHTML = `
        <div class="p-4">
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <div class="w-6 h-6 ${bgColor} rounded-full flex items-center justify-center">
                        <i class="${icon} ${iconColor} text-sm"></i>
                    </div>
                </div>
                <div class="ml-3 w-0 flex-1 pt-0.5">
                    <p class="text-sm font-medium text-gray-900">
                        ${escapeHtml(message)}
                    </p>
                </div>
                <div class="ml-4 flex-shrink-0 flex">
                    <button onclick="hideToast('${toastId}')" 
                            class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        <span class="sr-only">Fechar</span>
                        <i class="ri-close-line text-lg"></i>
                    </button>
                </div>
            </div>
        </div>
        <div class="${borderColor} h-1 w-full">
            <div class="progress-bar ${bgColor} h-full" style="animation: shrink ${duration}ms linear;"></div>
        </div>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Trigger entrance animation
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    }, 10);
    
    // Auto-hide after duration
    setTimeout(() => {
        hideToast(toastId);
    }, duration);
    
    return toastId;
}

function hideToast(toastId) {
    const toast = document.getElementById(toastId);
    if (!toast) return;
    
    // Trigger exit animation
    toast.classList.remove('translate-x-0', 'opacity-100');
    toast.classList.add('translate-x-full', 'opacity-0');
    
    // Remove from DOM after animation
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

function getToastStyle(type) {
    const styles = {
        success: {
            icon: 'ri-check-line',
            bgColor: 'bg-green-100',
            iconColor: 'text-green-600',
            borderColor: 'bg-green-200'
        },
        error: {
            icon: 'ri-close-line',
            bgColor: 'bg-red-100',
            iconColor: 'text-red-600',
            borderColor: 'bg-red-200'
        },
        warning: {
            icon: 'ri-alert-line',
            bgColor: 'bg-yellow-100',
            iconColor: 'text-yellow-600',
            borderColor: 'bg-yellow-200'
        },
        info: {
            icon: 'ri-information-line',
            bgColor: 'bg-blue-100',
            iconColor: 'text-blue-600',
            borderColor: 'bg-blue-200'
        }
    };
    
    return styles[type] || styles.info;
}

// Convenience functions
function showSuccessToast(message, duration = 4000) {
    return showToast(message, 'success', duration);
}

function showErrorToast(message, duration = 6000) {
    return showToast(message, 'error', duration);
}

function showWarningToast(message, duration = 5000) {
    return showToast(message, 'warning', duration);
}

function showInfoToast(message, duration = 4000) {
    return showToast(message, 'info', duration);
}

// Clear all toasts
function clearAllToasts() {
    const container = document.getElementById('toast-container');
    if (container) {
        const toasts = container.querySelectorAll('[id^="toast-"]');
        toasts.forEach(toast => {
            hideToast(toast.id);
        });
    }
}

// Show loading toast (doesn't auto-hide)
function showLoadingToast(message = 'Carregando...') {
    const toastId = `toast-${++toastCounter}`;
    const container = document.getElementById('toast-container');
    
    if (!container) {
        console.error('Toast container not found');
        return;
    }
    
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `
        transform transition-all duration-300 ease-in-out
        max-w-md w-full bg-white shadow-lg rounded-lg pointer-events-auto
        ring-1 ring-black ring-opacity-5 overflow-hidden
        translate-x-full opacity-0
    `;
    
    toast.innerHTML = `
        <div class="p-4">
            <div class="flex items-start">
                <div class="flex-shrink-0">
                    <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                        <i class="ri-loader-4-line animate-spin text-blue-600 text-sm"></i>
                    </div>
                </div>
                <div class="ml-3 w-0 flex-1 pt-0.5">
                    <p class="text-sm font-medium text-gray-900">
                        ${escapeHtml(message)}
                    </p>
                </div>
            </div>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.remove('translate-x-full', 'opacity-0');
        toast.classList.add('translate-x-0', 'opacity-100');
    }, 10);
    
    return toastId;
}

// Update loading toast message
function updateLoadingToast(toastId, message) {
    const toast = document.getElementById(toastId);
    if (toast) {
        const messageElement = toast.querySelector('p');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }
}

// Convert loading toast to success/error
function finishLoadingToast(toastId, message, type = 'success', duration = 4000) {
    const toast = document.getElementById(toastId);
    if (!toast) return;
    
    const { icon, bgColor, iconColor } = getToastStyle(type);
    
    // Update icon and message
    const iconElement = toast.querySelector('i');
    const messageElement = toast.querySelector('p');
    const iconContainer = toast.querySelector('.w-6.h-6');
    
    if (iconElement) {
        iconElement.className = `${icon} ${iconColor} text-sm`;
    }
    
    if (iconContainer) {
        iconContainer.className = `w-6 h-6 ${bgColor} rounded-full flex items-center justify-center`;
    }
    
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    // Add close button if not present
    const buttonContainer = toast.querySelector('.ml-4.flex-shrink-0');
    if (!buttonContainer) {
        const messageContainer = toast.querySelector('.ml-3.w-0.flex-1');
        if (messageContainer) {
            const closeButton = document.createElement('div');
            closeButton.className = 'ml-4 flex-shrink-0 flex';
            closeButton.innerHTML = `
                <button onclick="hideToast('${toastId}')" 
                        class="bg-white rounded-md inline-flex text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    <span class="sr-only">Fechar</span>
                    <i class="ri-close-line text-lg"></i>
                </button>
            `;
            messageContainer.parentNode.appendChild(closeButton);
        }
    }
    
    // Auto-hide after duration
    setTimeout(() => {
        hideToast(toastId);
    }, duration);
}

// Add CSS for progress bar animation
const style = document.createElement('style');
style.textContent = `
    @keyframes shrink {
        from { width: 100%; }
        to { width: 0%; }
    }
`;
document.head.appendChild(style);

// Export functions to global scope
window.showToast = showToast;
window.hideToast = hideToast;
window.showSuccessToast = showSuccessToast;
window.showErrorToast = showErrorToast;
window.showWarningToast = showWarningToast;
window.showInfoToast = showInfoToast;
window.clearAllToasts = clearAllToasts;
window.showLoadingToast = showLoadingToast;
window.updateLoadingToast = updateLoadingToast;
window.finishLoadingToast = finishLoadingToast;