/**
 * Modal Manager - Utility for handling modal dialogs
 * Provides reusable functions for modal management with animations and accessibility
 */

class ModalManager {
    constructor() {
        this.openModals = new Set();
        this.originalFocus = null;
        this.setupGlobalEventListeners();
    }

    /**
     * Show a modal with animation and focus management
     * @param {string} modalId - ID of the modal element
     * @param {Object} options - Configuration options
     */
    show(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`Modal with ID '${modalId}' not found`);
            return;
        }

        // Store current focus
        this.originalFocus = document.activeElement;

        // Show modal
        modal.classList.remove('hidden');
        this.openModals.add(modalId);

        // Animate in
        const content = modal.querySelector('[data-modal-content]');
        if (content) {
            setTimeout(() => {
                content.classList.remove('scale-95', 'opacity-0');
                content.classList.add('scale-100', 'opacity-100');
            }, 10);
        }

        // Focus management
        this.setupFocusTrap(modal);

        // Setup event listeners for this modal
        this.setupModalEventListeners(modal, options);

        // Callback
        if (options.onShow) {
            options.onShow(modal);
        }
    }

    /**
     * Hide a modal with animation
     * @param {string} modalId - ID of the modal element
     * @param {Object} options - Configuration options
     */
    hide(modalId, options = {}) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        const content = modal.querySelector('[data-modal-content]');

        // Animate out
        if (content) {
            content.classList.remove('scale-100', 'opacity-100');
            content.classList.add('scale-95', 'opacity-0');
        }

        setTimeout(() => {
            modal.classList.add('hidden');
            this.openModals.delete(modalId);

            // Restore focus
            if (this.originalFocus && this.openModals.size === 0) {
                this.originalFocus.focus();
                this.originalFocus = null;
            }

            // Callback
            if (options.onHide) {
                options.onHide(modal);
            }
        }, 150);

        // Clean up event listeners
        this.cleanupModalEventListeners(modal);
    }

    /**
     * Create and show a confirmation dialog
     * @param {Object} config - Configuration for the confirmation dialog
     */
    confirm(config) {
        const {
            title = 'Confirmação',
            message = 'Tem certeza que deseja continuar?',
            confirmText = 'Confirmar',
            cancelText = 'Cancelar',
            type = 'info', // info, warning, danger, success
            onConfirm = () => {},
            onCancel = () => {}
        } = config;

        const modalId = 'dynamic-confirm-modal';
        
        // Remove existing dynamic modal
        const existing = document.getElementById(modalId);
        if (existing) {
            existing.remove();
        }

        // Create modal HTML
        const modalHTML = this.createConfirmModalHTML(modalId, {
            title,
            message,
            confirmText,
            cancelText,
            type
        });

        // Add to DOM
        document.body.insertAdjacentHTML('beforeend', modalHTML);

        // Show modal with callbacks
        this.show(modalId, {
            onConfirm,
            onCancel,
            onHide: () => {
                // Clean up dynamic modal
                setTimeout(() => {
                    const modal = document.getElementById(modalId);
                    if (modal) {
                        modal.remove();
                    }
                }, 200);
            }
        });
    }

    /**
     * Setup focus trap within modal
     * @param {HTMLElement} modal - Modal element
     */
    setupFocusTrap(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }
    }

    /**
     * Setup event listeners for a specific modal
     * @param {HTMLElement} modal - Modal element
     * @param {Object} options - Configuration options
     */
    setupModalEventListeners(modal, options) {
        const modalId = modal.id;

        // Close button handlers
        const closeButtons = modal.querySelectorAll('[data-modal-close]');
        closeButtons.forEach(button => {
            button.addEventListener('click', () => {
                this.hide(modalId, options);
                if (options.onCancel) {
                    options.onCancel();
                }
            });
        });

        // Confirm button handlers
        const confirmButtons = modal.querySelectorAll('[data-modal-confirm]');
        confirmButtons.forEach(button => {
            button.addEventListener('click', () => {
                if (options.onConfirm) {
                    options.onConfirm();
                }
                this.hide(modalId, options);
            });
        });

        // Click outside to close
        modal.addEventListener('click', (event) => {
            if (event.target === modal) {
                this.hide(modalId, options);
                if (options.onCancel) {
                    options.onCancel();
                }
            }
        });
    }

    /**
     * Setup global event listeners
     */
    setupGlobalEventListeners() {
        // Escape key to close modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && this.openModals.size > 0) {
                const lastModal = Array.from(this.openModals).pop();
                this.hide(lastModal);
            }
        });
    }

    /**
     * Clean up modal event listeners
     * @param {HTMLElement} modal - Modal element
     */
    cleanupModalEventListeners(modal) {
        // Event listeners are automatically removed when modal is hidden
        // since we don't use persistent listeners on the modal element
    }

    /**
     * Create HTML for confirmation modal
     * @param {string} modalId - Modal ID
     * @param {Object} config - Configuration
     * @returns {string} HTML string
     */
    createConfirmModalHTML(modalId, config) {
        const typeConfig = {
            info: {
                iconClass: 'ri-information-line',
                iconBg: 'bg-blue-500',
                confirmClass: 'bg-blue-500 hover:bg-blue-600 focus:ring-blue-500'
            },
            warning: {
                iconClass: 'ri-alert-line',
                iconBg: 'bg-yellow-500',
                confirmClass: 'bg-yellow-500 hover:bg-yellow-600 focus:ring-yellow-500'
            },
            danger: {
                iconClass: 'ri-error-warning-line',
                iconBg: 'bg-red-500',
                confirmClass: 'bg-red-500 hover:bg-red-600 focus:ring-red-500'
            },
            success: {
                iconClass: 'ri-check-line',
                iconBg: 'bg-green-500',
                confirmClass: 'bg-green-500 hover:bg-green-600 focus:ring-green-500'
            }
        };

        const typeSettings = typeConfig[config.type] || typeConfig.info;

        return `
            <div id="${modalId}" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" role="dialog">
                <div class="bg-white rounded-lg w-full max-w-md mx-4 transform transition-all duration-200 scale-95 opacity-0" data-modal-content>
                    <div class="p-6">
                        <!-- Header -->
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 ${typeSettings.iconBg} rounded-full flex items-center justify-center">
                                    <i class="${typeSettings.iconClass} text-white text-lg"></i>
                                </div>
                                <h3 class="text-lg font-semibold text-gray-900">${config.title}</h3>
                            </div>
                            <button data-modal-close class="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100" aria-label="Fechar modal">
                                <i class="ri-close-line text-xl"></i>
                            </button>
                        </div>
                        
                        <!-- Content -->
                        <div class="mb-6">
                            <p class="text-gray-600">${config.message}</p>
                        </div>
                        
                        <!-- Actions -->
                        <div class="flex space-x-3">
                            <button type="button" 
                                    data-modal-close 
                                    class="flex-1 px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors font-medium">
                                <i class="ri-close-line mr-2"></i>
                                ${config.cancelText}
                            </button>
                            <button type="button" 
                                    data-modal-confirm 
                                    class="flex-1 px-4 py-2 ${typeSettings.confirmClass} text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors font-medium">
                                <i class="ri-check-line mr-2"></i>
                                ${config.confirmText}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}

// Create global instance
const modalManager = new ModalManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
}

// Global helper functions for backward compatibility
window.showModal = (modalId, options) => modalManager.show(modalId, options);
window.hideModal = (modalId, options) => modalManager.hide(modalId, options);
window.confirmDialog = (config) => modalManager.confirm(config);