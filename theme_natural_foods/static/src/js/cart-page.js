// Cart page specific JavaScript

// Initialize cart page
function initializeCartPage() {
    loadCartContent();
}

// Load cart content
function loadCartContent() {
    const container = document.getElementById('cart-content');
    
    if (cartState.items.length === 0) {
        showEmptyCart();
        return;
    }
    
    container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Cart Items -->
            <div class="lg:col-span-2">
                <div class="bg-white rounded-2xl shadow-lg border overflow-hidden">
                    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
                        <h2 class="text-xl font-semibold text-gray-800">Cart Items (${cartState.itemCount})</h2>
                    </div>
                    
                    <div class="divide-y divide-gray-200">
                        ${cartState.items.map(item => createCartItem(item)).join('')}
                    </div>
                </div>
                
                <!-- Continue Shopping -->
                <div class="mt-6 text-center">
                    <button onclick="navigateTo('products.html')" class="text-green-600 hover:text-green-700 font-medium">
                        ← Continue Shopping
                    </button>
                </div>
            </div>
            
            <!-- Order Summary -->
            <div class="lg:col-span-1">
                <div class="bg-white rounded-2xl shadow-lg border p-6 sticky top-8">
                    <h2 class="text-xl font-semibold text-gray-800 mb-6">Order Summary</h2>
                    
                    <!-- Pricing Details -->
                    <div class="space-y-4 mb-6">
                        <div class="flex justify-between text-gray-600">
                            <span>Subtotal (${cartState.itemCount} items)</span>
                            <span>$${cartState.total.toFixed(2)}</span>
                        </div>
                        
                        <div class="flex justify-between text-gray-600">
                            <span>Estimated Tax</span>
                            <span>$${(cartState.total * 0.08).toFixed(2)}</span>
                        </div>
                        
                        <div class="flex justify-between text-gray-600">
                            <span>Shipping</span>
                            <span class="${cartState.total >= 50 ? 'text-green-600 font-medium' : ''}">
                                ${cartState.total >= 50 ? 'FREE' : '$4.99'}
                            </span>
                        </div>
                        
                        ${cartState.total < 50 ? `
                            <div class="bg-green-50 border border-green-200 rounded-lg p-3">
                                <p class="text-sm text-green-700">
                                    Add $${(50 - cartState.total).toFixed(2)} more to get FREE shipping! 🚚
                                </p>
                            </div>
                        ` : ''}
                        
                        <div class="border-t border-gray-200 pt-4">
                            <div class="flex justify-between text-lg font-semibold text-gray-800">
                                <span>Total</span>
                                <span class="text-green-600">$${(cartState.total + (cartState.total * 0.08) + (cartState.total >= 50 ? 0 : 4.99)).toFixed(2)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Promo Code -->
                    <div class="mb-6">
                        <label class="block text-sm font-medium text-gray-700 mb-2">Promo Code</label>
                        <div class="flex gap-2">
                            <input
                                type="text"
                                id="promo-code"
                                placeholder="Enter code"
                                class="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:border-green-500 focus:ring-green-500"
                            />
                            <button onclick="applyPromoCode()" class="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors">
                                Apply
                            </button>
                        </div>
                    </div>
                    
                    <!-- Checkout Button -->
                    <button onclick="proceedToCheckout()" class="w-full bg-green-600 hover:bg-green-700 text-white py-4 rounded-lg font-semibold text-lg transition-colors mb-4">
                        Proceed to Checkout
                    </button>
                    
                    <!-- Security Info -->
                    <div class="text-center text-sm text-gray-500">
                        <div class="flex items-center justify-center gap-2 mb-2">
                            <i data-lucide="shield-check" class="h-4 w-4 text-green-600"></i>
                            <span>Secure Checkout</span>
                        </div>
                        <p>Your payment information is protected</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    lucide.createIcons();
}

// Create cart item HTML
function createCartItem(item) {
    return `
        <div class="p-6">
            <div class="flex items-start gap-4">
                <!-- Product Image -->
                <div class="w-24 h-24 flex-shrink-0">
                    <img src="${item.image}" alt="${item.name}" class="w-full h-full object-cover rounded-lg">
                </div>
                
                <!-- Product Details -->
                <div class="flex-1 min-w-0">
                    <h3 class="font-semibold text-gray-800 mb-1">${item.name}</h3>
                    <p class="text-sm text-gray-600 mb-2">Price: $${item.price.toFixed(2)} each</p>
                    
                    <!-- Quantity Controls -->
                    <div class="flex items-center gap-3 mb-3">
                        <div class="flex items-center border border-gray-300 rounded-lg">
                            <button 
                                onclick="updateCartItemQuantity(${item.id}, ${item.quantity - 1})" 
                                class="p-2 hover:bg-gray-50 ${item.quantity <= 1 ? 'opacity-50 cursor-not-allowed' : ''}"
                                ${item.quantity <= 1 ? 'disabled' : ''}
                            >
                                <i data-lucide="minus" class="h-4 w-4"></i>
                            </button>
                            <span class="px-4 py-2 font-medium min-w-[3rem] text-center">${item.quantity}</span>
                            <button 
                                onclick="updateCartItemQuantity(${item.id}, ${item.quantity + 1})" 
                                class="p-2 hover:bg-gray-50"
                            >
                                <i data-lucide="plus" class="h-4 w-4"></i>
                            </button>
                        </div>
                        
                        <button 
                            onclick="removeCartItem(${item.id})"
                            class="text-red-500 hover:text-red-700 font-medium text-sm"
                        >
                            Remove
                        </button>
                    </div>
                    
                    <!-- Item Total -->
                    <div class="text-lg font-semibold text-green-600">
                        $${(item.price * item.quantity).toFixed(2)}
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="flex flex-col gap-2">
                    <button onclick="navigateToProduct(${item.id})" class="text-gray-400 hover:text-gray-600">
                        <i data-lucide="external-link" class="h-4 w-4"></i>
                    </button>
                    <button onclick="addToWishlist(${item.id})" class="text-gray-400 hover:text-red-500">
                        <i data-lucide="heart" class="h-4 w-4"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Update cart item quantity
function updateCartItemQuantity(productId, newQuantity) {
    if (newQuantity < 1) return;
    
    updateQuantity(productId, newQuantity);
    loadCartContent();
}

// Remove cart item
function removeCartItem(productId) {
    // Show confirmation dialog
    if (confirm('Are you sure you want to remove this item from your cart?')) {
        removeFromCart(productId);
        loadCartContent();
        
        // Show notification
        showCartUpdateNotification('Item removed from cart');
    }
}

// Add to wishlist
function addToWishlist(productId) {
    // This would typically save to wishlist
    console.log('Added to wishlist:', productId);
    showCartUpdateNotification('Added to wishlist ❤️');
}

// Apply promo code
function applyPromoCode() {
    const promoCode = document.getElementById('promo-code').value.trim().toUpperCase();
    
    if (!promoCode) {
        showPromoMessage('Please enter a promo code', 'error');
        return;
    }
    
    // Mock promo codes
    const validPromoCodes = {
        'SAVE10': { discount: 0.1, type: 'percentage', description: '10% off' },
        'WELCOME5': { discount: 5, type: 'fixed', description: '$5 off' },
        'FREESHIP': { discount: 0, type: 'shipping', description: 'Free shipping' }
    };
    
    if (validPromoCodes[promoCode]) {
        const promo = validPromoCodes[promoCode];
        showPromoMessage(`Promo code applied! ${promo.description}`, 'success');
        
        // In a real app, this would update the cart state and recalculate totals
        setTimeout(() => {
            loadCartContent();
        }, 1000);
    } else {
        showPromoMessage('Invalid promo code', 'error');
    }
}

// Show promo message
function showPromoMessage(message, type) {
    const promoInput = document.getElementById('promo-code');
    const container = promoInput.parentElement;
    
    // Remove existing message
    const existingMessage = container.querySelector('.promo-message');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // Add new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `promo-message text-sm mt-2 ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
    
    // Remove message after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 3000);
}

// Proceed to checkout
function proceedToCheckout() {
    if (cartState.items.length === 0) {
        alert('Your cart is empty');
        return;
    }
    
    // In a real app, this would navigate to checkout page
    showCartUpdateNotification('Redirecting to checkout...');
    
    setTimeout(() => {
        // This would be replaced with actual checkout page
        navigateTo('checkout.html');
    }, 1000);
}

// Show empty cart
function showEmptyCart() {
    const container = document.getElementById('cart-content');
    container.innerHTML = `
        <div class="text-center py-20">
            <div class="bg-gray-100 rounded-full w-32 h-32 mx-auto mb-6 flex items-center justify-center">
                <i data-lucide="shopping-cart" class="h-16 w-16 text-gray-400"></i>
            </div>
            <h2 class="text-2xl font-semibold text-gray-800 mb-4">Your cart is empty</h2>
            <p class="text-gray-600 mb-8 max-w-md mx-auto">
                Looks like you haven't added any items to your cart yet. Start shopping to fill it up!
            </p>
            
            <div class="space-y-4">
                <button onclick="navigateTo('products.html')" class="bg-green-600 hover:bg-green-700 text-white px-8 py-3 rounded-lg font-semibold transition-colors">
                    Start Shopping
                </button>
                
                <div class="flex flex-col sm:flex-row gap-4 justify-center">
                    <button onclick="navigateTo('products.html?filter=new')" class="text-green-600 hover:text-green-700 font-medium">
                        Browse New Arrivals
                    </button>
                    <button onclick="navigateTo('products.html?filter=sale')" class="text-green-600 hover:text-green-700 font-medium">
                        View Sale Items
                    </button>
                </div>
            </div>
            
            <!-- Featured Categories -->
            <div class="mt-12">
                <h3 class="text-lg font-semibold text-gray-800 mb-6">Shop by Category</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
                    <button onclick="navigateTo('products.html?category=vegetables')" class="bg-green-100 hover:bg-green-200 rounded-lg p-4 text-center transition-colors">
                        <div class="text-3xl mb-2">🥬</div>
                        <div class="text-sm font-medium">Vegetables</div>
                    </button>
                    <button onclick="navigateTo('products.html?category=fruits')" class="bg-red-100 hover:bg-red-200 rounded-lg p-4 text-center transition-colors">
                        <div class="text-3xl mb-2">🍎</div>
                        <div class="text-sm font-medium">Fruits</div>
                    </button>
                    <button onclick="navigateTo('products.html?category=dairy')" class="bg-blue-100 hover:bg-blue-200 rounded-lg p-4 text-center transition-colors">
                        <div class="text-3xl mb-2">🥛</div>
                        <div class="text-sm font-medium">Dairy</div>
                    </button>
                    <button onclick="navigateTo('products.html?category=bakery')" class="bg-yellow-100 hover:bg-yellow-200 rounded-lg p-4 text-center transition-colors">
                        <div class="text-3xl mb-2">🍞</div>
                        <div class="text-sm font-medium">Bakery</div>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    lucide.createIcons();
}

// Show cart update notification
function showCartUpdateNotification(message) {
    // Create temporary notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-600 text-white p-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300';
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <i data-lucide="check-circle" class="h-5 w-5"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
    
    lucide.createIcons();
}