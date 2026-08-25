// Cart Dropdown System for Natural Foods Static HTML
console.log('🛒 Loading cart-dropdown.js...');

(function() {
    'use strict';
    
    // Demo cart items
    const DEMO_CART_ITEMS = [
        {
            id: 1,
            name: "Organic Roma Tomatoes",
            price: 2.99,
            quantity: 2,
            image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=80&h=80&fit=crop"
        },
        {
            id: 5,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            quantity: 1,
            image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=80&h=80&fit=crop"
        }
    ];
    
    let cartDropdownElement = null;
    let cartDropdownTimer = null;
    
    // Initialize cart dropdown
    function initializeCartDropdown() {
        const cartButton = document.querySelector('button[onclick*="cart.html"]');
        if (!cartButton) {
            console.warn('⚠️ Cart button not found');
            return;
        }
        
        // Create dropdown HTML
        const dropdownHTML = createCartDropdownHTML();
        
        // Insert dropdown after cart button
        const cartContainer = cartButton.closest('div.relative') || cartButton.parentElement;
        cartContainer.classList.add('relative');
        cartContainer.insertAdjacentHTML('beforeend', dropdownHTML);
        
        cartDropdownElement = cartContainer.querySelector('#cart-dropdown');
        
        // Add event listeners
        cartContainer.addEventListener('mouseenter', showCartDropdown);
        cartContainer.addEventListener('mouseleave', hideCartDropdown);
        
        console.log('✅ Cart dropdown initialized');
    }
    
    // Create cart dropdown HTML
    function createCartDropdownHTML() {
        const subtotal = DEMO_CART_ITEMS.reduce((total, item) => total + (item.price * item.quantity), 0);
        
        return `
            <div id="cart-dropdown" class="hidden absolute top-full right-0 mt-2 w-96 bg-white border border-gray-200 rounded-2xl shadow-2xl overflow-hidden z-50 transform opacity-0 scale-95 transition-all duration-200">
                <!-- Dropdown Header -->
                <div class="bg-gradient-to-r from-green-600 to-emerald-600 text-white p-4">
                    <div class="flex items-center justify-between">
                        <h3 class="font-bold text-lg flex items-center gap-2">
                            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5H19"></path>
                            </svg>
                            Shopping Cart
                        </h3>
                        <span class="bg-white/20 px-2 py-1 rounded-full text-sm">${DEMO_CART_ITEMS.length} items</span>
                    </div>
                </div>
                
                <!-- Cart Items -->
                <div class="max-h-80 overflow-y-auto">
                    ${DEMO_CART_ITEMS.map(item => createCartItemHTML(item)).join('')}
                </div>
                
                <!-- Cart Footer -->
                <div class="border-t border-gray-200 p-4 bg-gray-50">
                    <div class="flex items-center justify-between mb-4">
                        <span class="font-semibold text-gray-900">Subtotal:</span>
                        <span class="font-bold text-xl text-green-600">$${subtotal.toFixed(2)}</span>
                    </div>
                    
                    <div class="grid grid-cols-2 gap-3">
                        <button onclick="window.location.href='cart.html'" class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors">
                            View Cart
                        </button>
                        <button onclick="window.location.href='checkout.html'" class="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white px-4 py-2 rounded-lg font-medium transition-all">
                            Checkout
                        </button>
                    </div>
                    
                    <div class="mt-3 text-center">
                        <p class="text-xs text-gray-500">🚚 Free shipping on orders over $50</p>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Create individual cart item HTML
    function createCartItemHTML(item) {
        const itemTotal = item.price * item.quantity;
        
        return `
            <div class="flex items-center gap-3 p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors">
                <div class="flex-shrink-0">
                    <img src="${item.image}" alt="${item.name}" class="w-12 h-12 rounded-lg object-cover">
                </div>
                
                <div class="flex-1 min-w-0">
                    <h4 class="font-medium text-gray-900 text-sm truncate">${item.name}</h4>
                    <p class="text-xs text-gray-500">Organic & Fresh</p>
                    <div class="flex items-center justify-between mt-1">
                        <div class="flex items-center gap-2">
                            <button onclick="updateCartItemQuantity(${item.id}, -1)" class="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-xs">−</button>
                            <span class="text-sm font-medium w-8 text-center">${item.quantity}</span>
                            <button onclick="updateCartItemQuantity(${item.id}, 1)" class="w-6 h-6 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-xs">+</button>
                        </div>
                        <span class="font-semibold text-green-600">$${itemTotal.toFixed(2)}</span>
                    </div>
                </div>
                
                <button onclick="removeCartItem(${item.id})" class="flex-shrink-0 text-gray-400 hover:text-red-500 transition-colors">
                    <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
    }
    
    // Show cart dropdown
    function showCartDropdown() {
        if (cartDropdownElement) {
            clearTimeout(cartDropdownTimer);
            cartDropdownElement.classList.remove('hidden');
            // Trigger animation
            setTimeout(() => {
                cartDropdownElement.classList.remove('opacity-0', 'scale-95');
                cartDropdownElement.classList.add('opacity-100', 'scale-100');
            }, 10);
            console.log('🛒 Cart dropdown shown');
        }
    }
    
    // Hide cart dropdown
    function hideCartDropdown() {
        if (cartDropdownElement) {
            cartDropdownTimer = setTimeout(() => {
                cartDropdownElement.classList.add('opacity-0', 'scale-95');
                cartDropdownElement.classList.remove('opacity-100', 'scale-100');
                // Hide after animation
                setTimeout(() => {
                    cartDropdownElement.classList.add('hidden');
                }, 200);
                console.log('🛒 Cart dropdown hidden');
            }, 150);
        }
    }
    
    // Update cart item quantity
    window.updateCartItemQuantity = function(itemId, change) {
        const item = DEMO_CART_ITEMS.find(item => item.id === itemId);
        if (item) {
            item.quantity = Math.max(1, item.quantity + change);
            refreshCartDropdown();
            console.log('🛒 Updated quantity for item:', itemId, 'new quantity:', item.quantity);
        }
    };
    
    // Remove cart item
    window.removeCartItem = function(itemId) {
        const index = DEMO_CART_ITEMS.findIndex(item => item.id === itemId);
        if (index > -1) {
            DEMO_CART_ITEMS.splice(index, 1);
            refreshCartDropdown();
            updateCartCount();
            console.log('🛒 Removed item from cart:', itemId);
        }
    };
    
    // Refresh cart dropdown content
    function refreshCartDropdown() {
        if (!cartDropdownElement) return;
        
        const cartContainer = cartDropdownElement.parentElement;
        cartDropdownElement.remove();
        
        const dropdownHTML = createCartDropdownHTML();
        cartContainer.insertAdjacentHTML('beforeend', dropdownHTML);
        cartDropdownElement = cartContainer.querySelector('#cart-dropdown');
        
        // Show dropdown if it was visible
        const wasVisible = !cartDropdownElement.classList.contains('hidden');
        if (wasVisible) {
            cartDropdownElement.classList.remove('hidden', 'opacity-0', 'scale-95');
            cartDropdownElement.classList.add('opacity-100', 'scale-100');
        }
    }
    
    // Update cart count in header
    function updateCartCount() {
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = DEMO_CART_ITEMS.length;
        }
    }
    
    // Make functions globally available
    window.showCartDropdown = showCartDropdown;
    window.hideCartDropdown = hideCartDropdown;
    
    // Initialize when DOM is ready
    function initialize() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initializeCartDropdown);
        } else {
            initializeCartDropdown();
        }
    }
    
    initialize();
    console.log('✅ Cart dropdown system loaded');
    
})();