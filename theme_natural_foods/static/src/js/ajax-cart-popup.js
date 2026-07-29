/**
 * AJAX Cart Popup Functionality - Bootstrap 5.0 Compatible
 * Handles cart popup display, animations, and interactions
 */

class AjaxCartPopup {
    constructor() {
        this.isVisible = false;
        this.cartItems = [
            {
                id: 1,
                name: 'Organic Baby Spinach',
                price: 4.99,
                quantity: 2,
                image: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop',
                description: 'Fresh & Crisp'
            },
            {
                id: 2,
                name: 'Organic Strawberries',
                price: 4.99,
                quantity: 1,
                image: 'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=300&h=300&fit=crop',
                description: 'Sweet & Juicy'
            }
        ];
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Close popup when clicking overlay
        document.addEventListener('click', (e) => {
            if (e.target && e.target.id === 'cart-overlay') {
                this.hide();
            }
        });

        // Close popup when pressing Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hide();
            }
        });

        // Initialize cart popup HTML if not exists
        this.ensureCartPopupExists();
    }

    ensureCartPopupExists() {
        if (!document.getElementById('cart-popup')) {
            this.createCartPopupHTML();
        }
    }

    createCartPopupHTML() {
        const cartPopupHTML = `
            <!-- Cart Popup Overlay -->
            <div id="cart-overlay" class="cart-overlay" onclick="window.ajaxCart.hide()"></div>
            
            <!-- Cart Popup -->
            <div id="cart-popup" class="cart-popup">
                <div class="h-100 d-flex flex-column">
                    <!-- Cart Header -->
                    <div class="d-flex align-items-center justify-content-between p-4 border-bottom bg-organic-50">
                        <h3 class="h5 fw-bold text-dark mb-0 d-flex align-items-center gap-2">
                            <i class="bi bi-cart3 text-success"></i>
                            Shopping Cart (<span id="popup-cart-count">2</span>)
                        </h3>
                        <button onclick="window.ajaxCart.hide()" class="btn btn-light btn-sm rounded-circle" type="button">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                    
                    <!-- Cart Items -->
                    <div class="flex-fill overflow-auto p-3">
                        <div id="cart-items-container" class="d-flex flex-column gap-3">
                            <!-- Cart items will be populated here -->
                        </div>
                        
                        <!-- Empty Cart Message -->
                        <div id="empty-cart-message" class="d-none text-center py-5">
                            <div class="bg-light rounded-circle d-inline-flex align-items-center justify-content-center mb-3" style="width: 5rem; height: 5rem;">
                                <i class="bi bi-cart3 text-muted fs-2"></i>
                            </div>
                            <h5 class="fw-semibold text-dark mb-2">Your cart is empty</h5>
                            <p class="text-muted mb-3">Add some organic products to get started</p>
                            <button onclick="window.ajaxCart.hide()" class="btn btn-organic rounded-3">
                                Continue Shopping
                            </button>
                        </div>
                    </div>
                    
                    <!-- Cart Footer -->
                    <div id="cart-footer" class="border-top p-3 bg-light">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <span class="fw-semibold text-dark">Subtotal:</span>
                            <span id="cart-subtotal" class="h5 fw-bold text-success mb-0">$14.97</span>
                        </div>
                        <div class="small text-muted mb-3">
                            <div class="d-flex align-items-center gap-2">
                                <i class="bi bi-truck text-success"></i>
                                Free shipping on orders over $50
                            </div>
                        </div>
                        <div class="d-grid gap-2">
                            <button onclick="window.location.href='cart.html'" class="btn btn-outline-secondary rounded-3 d-flex align-items-center justify-content-center gap-2">
                                <i class="bi bi-eye"></i>
                                View Full Cart
                            </button>
                            <button onclick="window.location.href='checkout.html'" class="btn btn-organic rounded-3 d-flex align-items-center justify-content-center gap-2">
                                <i class="bi bi-credit-card"></i>
                                Checkout Now
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add Bootstrap-compatible styles if not already present
        if (!document.getElementById('cart-popup-styles')) {
            const styles = document.createElement('style');
            styles.id = 'cart-popup-styles';
            styles.textContent = `
                .cart-popup {
                    position: fixed;
                    top: 0;
                    right: -420px;
                    width: 420px;
                    height: 100vh;
                    background: white;
                    box-shadow: -8px 0 32px rgba(0, 0, 0, 0.15);
                    transition: right 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                    z-index: 1050;
                    border-left: 2px solid var(--organic-green-200, #bbf7d0);
                }
                
                .cart-popup.show {
                    right: 0;
                }
                
                .cart-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100vh;
                    background: rgba(0, 0, 0, 0.6);
                    opacity: 0;
                    visibility: hidden;
                    transition: all 0.3s ease;
                    z-index: 1040;
                    backdrop-filter: blur(4px);
                }
                
                .cart-overlay.show {
                    opacity: 1;
                    visibility: visible;
                }
                
                .cart-item {
                    animation: slideInFromRight 0.3s ease-out;
                }
                
                @keyframes slideInFromRight {
                    from {
                        opacity: 0;
                        transform: translateX(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
                
                .cart-item-remove {
                    transition: all 0.2s ease;
                }
                
                .cart-item-remove:hover {
                    transform: scale(1.05);
                }
                
                @media (max-width: 576px) {
                    .cart-popup {
                        width: 100%;
                        right: -100%;
                    }
                }
                
                .quantity-control {
                    transition: all 0.2s ease;
                    width: 2rem;
                    height: 2rem;
                    border: 1px solid #dee2e6;
                    background: white;
                }
                
                .quantity-control:hover {
                    background-color: var(--organic-green-50, #f0fdf4);
                    border-color: var(--organic-green-600, #16a34a);
                    transform: scale(1.05);
                }
                
                .quantity-control:active {
                    transform: scale(0.95);
                }

                .cart-popup .bg-organic-50 {
                    background: linear-gradient(135deg, var(--organic-green-50, #f0fdf4) 0%, var(--emerald-50, #ecfdf5) 100%);
                }

                .cart-popup .btn-organic {
                    background-color: var(--organic-green-600, #16a34a);
                    border-color: var(--organic-green-600, #16a34a);
                    color: white;
                    font-weight: 500;
                    transition: all 0.15s ease;
                }

                .cart-popup .btn-organic:hover {
                    background-color: var(--organic-green-700, #15803d);
                    border-color: var(--organic-green-700, #15803d);
                    color: white;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(22, 163, 74, 0.25);
                }

                .cart-popup .text-success {
                    color: var(--organic-green-600, #16a34a) !important;
                }

                .cart-popup .cart-item-card {
                    background: linear-gradient(135deg, #f8f9fa 0%, var(--organic-green-50, #f0fdf4) 100%);
                    border: 1px solid #e9ecef;
                    border-radius: 0.75rem;
                    transition: all 0.2s ease;
                }

                .cart-popup .cart-item-card:hover {
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    transform: translateY(-1px);
                }
            `;
            document.head.appendChild(styles);
        }

        // Add the HTML to the body
        document.body.insertAdjacentHTML('beforeend', cartPopupHTML);
    }

    show() {
        this.ensureCartPopupExists();
        this.renderCartItems();
        
        const overlay = document.getElementById('cart-overlay');
        const popup = document.getElementById('cart-popup');
        
        if (overlay && popup) {
            overlay.classList.add('show');
            popup.classList.add('show');
            document.body.style.overflow = 'hidden';
            this.isVisible = true;
            
            // Play a subtle sound effect (optional)
            this.playCartSound();
        }
    }

    hide() {
        const overlay = document.getElementById('cart-overlay');
        const popup = document.getElementById('cart-popup');
        
        if (overlay && popup) {
            overlay.classList.remove('show');
            popup.classList.remove('show');
            document.body.style.overflow = '';
            this.isVisible = false;
        }
    }

    addToCart(productData) {
        // Find existing item or create new one
        const existingItemIndex = this.cartItems.findIndex(item => item.id === productData.id);
        
        if (existingItemIndex !== -1) {
            // Increase quantity if item exists
            this.cartItems[existingItemIndex].quantity += 1;
        } else {
            // Add new item to cart
            this.cartItems.push({
                id: productData.id,
                name: productData.name || 'Organic Product',
                price: productData.price || 4.99,
                quantity: 1,
                image: productData.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&h=300&fit=crop',
                description: productData.description || 'Fresh & Organic'
            });
        }

        this.updateCartCount();
        this.showToast('Product added to cart!', 'success');
        
        // Show cart popup after a brief delay
        setTimeout(() => {
            this.show();
        }, 300);
    }

    removeFromCart(productId) {
        this.cartItems = this.cartItems.filter(item => item.id !== productId);
        this.updateCartCount();
        this.renderCartItems();
        this.showToast('Item removed from cart', 'success');
        
        // Hide popup if cart is empty
        if (this.cartItems.length === 0) {
            setTimeout(() => {
                this.hide();
            }, 1000);
        }
    }

    updateQuantity(productId, change) {
        const item = this.cartItems.find(item => item.id === productId);
        if (item) {
            item.quantity += change;
            if (item.quantity <= 0) {
                this.removeFromCart(productId);
            } else {
                this.updateCartCount();
                this.renderCartItems();
                this.showToast('Cart updated!', 'success');
            }
        }
    }

    renderCartItems() {
        const container = document.getElementById('cart-items-container');
        const emptyMessage = document.getElementById('empty-cart-message');
        const footer = document.getElementById('cart-footer');
        
        if (!container) return;

        if (this.cartItems.length === 0) {
            container.innerHTML = '';
            emptyMessage?.classList.remove('d-none');
            footer?.classList.add('d-none');
            return;
        }

        emptyMessage?.classList.add('d-none');
        footer?.classList.remove('d-none');

        const itemsHTML = this.cartItems.map(item => `
            <div class="cart-item cart-item-card p-3">
                <div class="d-flex align-items-center gap-3">
                    <img src="${item.image}" alt="${item.name}" class="rounded" style="width: 4rem; height: 4rem; object-fit: cover;">
                    <div class="flex-fill">
                        <h6 class="fw-semibold text-dark mb-1">${item.name}</h6>
                        <p class="small text-muted mb-2">${item.description}</p>
                        <div class="d-flex align-items-center gap-2">
                            <button onclick="window.ajaxCart.updateQuantity(${item.id}, -1)" class="btn quantity-control rounded-circle d-flex align-items-center justify-content-center" type="button">
                                <i class="bi bi-dash"></i>
                            </button>
                            <span class="text-center fw-semibold px-2">${item.quantity}</span>
                            <button onclick="window.ajaxCart.updateQuantity(${item.id}, 1)" class="btn quantity-control rounded-circle d-flex align-items-center justify-content-center" type="button">
                                <i class="bi bi-plus"></i>
                            </button>
                        </div>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-success mb-2">$${(item.price * item.quantity).toFixed(2)}</div>
                        <button onclick="window.ajaxCart.removeFromCart(${item.id})" class="btn btn-link btn-sm text-danger cart-item-remove p-0" type="button">
                            <i class="bi bi-trash3 me-1"></i>
                            Remove
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = itemsHTML;
        this.updateSubtotal();
    }

    updateSubtotal() {
        const subtotal = this.cartItems.reduce((total, item) => total + (item.price * item.quantity), 0);
        const subtotalElement = document.getElementById('cart-subtotal');
        if (subtotalElement) {
            subtotalElement.textContent = `$${subtotal.toFixed(2)}`;
        }
    }

    updateCartCount() {
        const totalQuantity = this.cartItems.reduce((total, item) => total + item.quantity, 0);
        
        // Update all cart count elements
        const cartCountElements = document.querySelectorAll('#cart-count, #popup-cart-count');
        cartCountElements.forEach(element => {
            if (element) {
                element.textContent = totalQuantity;
            }
        });
    }

    getCartCount() {
        return this.cartItems.reduce((total, item) => total + item.quantity, 0);
    }

    getCartItems() {
        return this.cartItems;
    }

    clearCart() {
        this.cartItems = [];
        this.updateCartCount();
        this.renderCartItems();
        this.showToast('Cart cleared!', 'success');
        this.hide();
    }

    playCartSound() {
        // Optional: Play a subtle sound when item is added to cart
        try {
            const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmMcBj2Z2O/EcSAFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmMcBj2Z2O/EcSAFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAUU');
            audio.volume = 0.1;
            audio.play().catch(() => {}); // Ignore errors if sound can't play
        } catch (e) {
            // Ignore sound errors
        }
    }

    showToast(message, type = 'info') {
        // Check if Bootstrap is available
        if (typeof bootstrap !== 'undefined' && bootstrap.Toast) {
            // Use Bootstrap Toast
            const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
            
            const toastId = 'toast-' + Date.now();
            let bgClass = 'bg-info';
            let iconClass = 'bi-info-circle';
            
            switch (type) {
                case 'success':
                    bgClass = 'bg-success';
                    iconClass = 'bi-check-circle';
                    break;
                case 'error':
                    bgClass = 'bg-danger';
                    iconClass = 'bi-x-circle';
                    break;
                case 'warning':
                    bgClass = 'bg-warning text-dark';
                    iconClass = 'bi-exclamation-triangle';
                    break;
            }
            
            const toastHTML = `
                <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                    <div class="toast-body ${bgClass} text-white fw-medium rounded d-flex align-items-center gap-2">
                        <i class="bi ${iconClass}"></i>
                        ${message}
                    </div>
                </div>
            `;
            
            toastContainer.insertAdjacentHTML('beforeend', toastHTML);
            
            const toastElement = document.getElementById(toastId);
            const bsToast = new bootstrap.Toast(toastElement, { delay: 3000 });
            bsToast.show();
            
            // Remove toast element after it's hidden
            toastElement.addEventListener('hidden.bs.toast', () => {
                toastElement.remove();
            });
        } else {
            // Fallback to custom toast
            const toast = document.createElement('div');
            toast.className = `position-fixed top-0 end-0 m-3 px-3 py-2 rounded text-white fw-medium`;
            toast.style.zIndex = '9999';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'transform 0.3s ease';
            
            switch (type) {
                case 'success':
                    toast.classList.add('bg-success');
                    break;
                case 'error':
                    toast.classList.add('bg-danger');
                    break;
                case 'warning':
                    toast.classList.add('bg-warning', 'text-dark');
                    break;
                default:
                    toast.classList.add('bg-info');
            }
            
            toast.innerHTML = `
                <div class="d-flex align-items-center gap-2">
                    <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
                    ${message}
                </div>
            `;
            
            document.body.appendChild(toast);
            
            // Animate in
            setTimeout(() => toast.style.transform = 'translateX(0)', 100);
            
            // Animate out and remove
            setTimeout(() => {
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => {
                    if (document.body.contains(toast)) {
                        document.body.removeChild(toast);
                    }
                }, 300);
            }, 3000);
        }
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }
}

// Initialize the cart popup when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.ajaxCart = new AjaxCartPopup();
    
    // Global addToCart function for backward compatibility
    window.addToCart = function(productId, productData = {}) {
        const defaultProduct = {
            id: productId,
            name: productData.name || 'Organic Product',
            price: productData.price || 4.99,
            image: productData.image || 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=300&h=300&fit=crop',
            description: productData.description || 'Fresh & Organic'
        };
        
        window.ajaxCart.addToCart(defaultProduct);
    };
    
    // Global showCartPopup function for backward compatibility
    window.showCartPopup = function() {
        if (window.ajaxCart) {
            window.ajaxCart.show();
        }
    };
    
    console.log('✅ Bootstrap AJAX Cart Popup initialized successfully');
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AjaxCartPopup;
}