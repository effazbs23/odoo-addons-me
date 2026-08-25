// Missing Functions - Provides placeholder functions that may be referenced

// Quick View Product function (simple placeholder)
function quickViewProduct(productId) {
    const product = getProductById(productId);
    if (!product) {
        console.warn('Product not found for quick view:', productId);
        showNotification('Product not found', 'error');
        return;
    }
    
    console.log('Quick view for product:', product.name);
    
    // For now, redirect to product details page
    // In the future, this could show a modal with product details
    window.location.href = `product-details.html?id=${productId}`;
}

// Mobile menu toggle function
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('hidden');
    }
}

// Account dropdown toggle
function toggleAccountDropdown() {
    const dropdown = document.getElementById('account-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('hidden');
    }
}

// Cart popup functions
function toggleCartPopup() {
    const cartPopup = document.getElementById('cart-popup');
    if (!cartPopup) return;
    
    if (cartPopup.classList.contains('hidden')) {
        updateCartPopup();
        cartPopup.classList.remove('hidden');
        
        // Close on click outside
        setTimeout(() => {
            document.addEventListener('click', function closeCartPopup(e) {
                if (!cartPopup.contains(e.target) && !e.target.closest('[onclick*="toggleCartPopup"]')) {
                    cartPopup.classList.add('hidden');
                    document.removeEventListener('click', closeCartPopup);
                }
            });
        }, 100);
    } else {
        cartPopup.classList.add('hidden');
    }
}

// Ajax cart functions (placeholders if missing)
function updateAjaxCartQuantity(productId, newQuantity) {
    if (typeof updateCartItemQuantity === 'function') {
        updateCartItemQuantity(productId, newQuantity);
        
        // Update the ajax cart display if it exists
        const ajaxCart = document.querySelector('.ajax-cart-modal');
        if (ajaxCart) {
            const product = getProductById(productId);
            if (product) {
                showAjaxCartPopup(product);
            }
        }
    }
}

function removeFromAjaxCart(productId) {
    if (typeof removeFromCart === 'function') {
        removeFromCart(productId);
        
        // Update the ajax cart display if it exists
        const ajaxCart = document.querySelector('.ajax-cart-modal');
        if (ajaxCart) {
            // Check if cart is empty and hide popup if so
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            if (cart.length === 0) {
                hideAjaxCartPopup();
            } else {
                // Re-show the popup with updated content
                const remainingProduct = getProductById(cart[0].id);
                if (remainingProduct) {
                    showAjaxCartPopup(remainingProduct);
                }
            }
        }
    }
}

function hideAjaxCartPopup() {
    const popup = document.querySelector('.ajax-cart-modal');
    if (popup) {
        popup.style.transform = 'translateX(100%)';
        setTimeout(() => {
            popup.remove();
        }, 500);
    }
}

// Newsletter signup function
function subscribeNewsletter() {
    const emailInput = document.getElementById('newsletter-email');
    if (!emailInput) {
        showNotification('Newsletter form not found', 'error');
        return;
    }
    
    const email = emailInput.value.trim();
    
    if (!email) {
        showNotification('Please enter your email address', 'warning');
        return;
    }
    
    if (!isValidEmail(email)) {
        showNotification('Please enter a valid email address', 'warning');
        return;
    }
    
    // Simulate newsletter signup
    showNotification('🎉 Thanks for subscribing to our newsletter!', 'success');
    emailInput.value = '';
}

// Simple fallback for any missing functions
function createFallbackFunction(functionName) {
    return function(...args) {
        console.warn(`Function ${functionName} called but not implemented. Args:`, args);
        showNotification(`Feature "${functionName}" coming soon!`, 'info');
    };
}

// List of potentially missing functions with fallbacks
const missingFunctionFallbacks = {
    'openProductModal': createFallbackFunction('openProductModal'),
    'closeProductModal': createFallbackFunction('closeProductModal'),
    'addToCompare': createFallbackFunction('addToCompare'),
    'shareProduct': createFallbackFunction('shareProduct'),
    'applyPromoCode': createFallbackFunction('applyPromoCode'),
    'proceedToCheckout': createFallbackFunction('proceedToCheckout')
};

// Add fallback functions to window if they don't exist
Object.keys(missingFunctionFallbacks).forEach(functionName => {
    if (typeof window[functionName] === 'undefined') {
        window[functionName] = missingFunctionFallbacks[functionName];
    }
});

// Make all functions globally available
if (typeof window !== 'undefined') {
    window.quickViewProduct = quickViewProduct;
    window.toggleMobileMenu = toggleMobileMenu;
    window.toggleAccountDropdown = toggleAccountDropdown;
    window.toggleCartPopup = toggleCartPopup;
    window.updateAjaxCartQuantity = updateAjaxCartQuantity;
    window.removeFromAjaxCart = removeFromAjaxCart;
    window.hideAjaxCartPopup = hideAjaxCartPopup;
    window.subscribeNewsletter = subscribeNewsletter;
}

console.log('✅ Missing functions module loaded - providing fallbacks for any missing functionality');