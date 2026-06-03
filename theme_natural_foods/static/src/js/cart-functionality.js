// Cart Functionality - All cart operations and ajax cart

// Initialize cart with demo items
function initializeDemoCartItems() {
    const demoCartItems = [
        {
            id: 1,
            name: "Organic Baby Spinach",
            price: 4.99,
            originalPrice: 6.99,
            quantity: 2,
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
            brand: "Fresh Farm"
        },
        {
            id: 2,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            quantity: 1,
            image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
            brand: "Orchard Fresh"
        },
        {
            id: 3,
            name: "Free Range Eggs",
            price: 4.99,
            originalPrice: 6.99,
            quantity: 1,
            image: "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&h=300&fit=crop",
            brand: "Happy Hens"
        },
        {
            id: 4,
            name: "Organic Greek Yogurt",
            price: 5.49,
            quantity: 1,
            image: "https://images.unsplash.com/photo-1571212515416-cd73c6b48529?w=300&h=300&fit=crop",
            brand: "Pure Greek"
        }
    ];
    
    // Check if cart already has items
    const existingCart = JSON.parse(localStorage.getItem('cart') || '[]');
    if (existingCart.length === 0) {
        localStorage.setItem('cart', JSON.stringify(demoCartItems));
        console.log('Added demo cart items:', demoCartItems.length);
    }
}

// Update cart display and counter
function updateCartDisplay() {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const cartCount = document.getElementById('cart-count');
    
    if (cartCount) {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        if (totalItems > 0) {
            cartCount.textContent = totalItems;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.classList.add('hidden');
        }
    }
    
    // Update cart popup if it exists
    updateCartPopup();
}

// Update cart popup content
function updateCartPopup() {
    const cartPopup = document.getElementById('cart-popup');
    if (!cartPopup) return;
    
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    
    if (cart.length === 0) {
        cartPopup.innerHTML = `
            <div class="w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
                <div class="p-8 text-center bg-gradient-to-br from-gray-50 to-white">
                    <div class="w-20 h-20 bg-gradient-to-br from-green-100 to-green-200 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
                        <i data-lucide="shopping-cart" class="h-10 w-10 text-green-600"></i>
                    </div>
                    <h3 class="text-xl font-bold text-gray-900 mb-3">Your cart is empty</h3>
                    <p class="text-gray-600 mb-6 max-w-xs mx-auto">Discover our fresh organic products and start your healthy journey!</p>
                    <a href="products.html" class="inline-flex items-center gap-2 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl">
                        <i data-lucide="leaf" class="h-4 w-4"></i>
                        Shop Fresh Products
                    </a>
                </div>
            </div>
        `;
    } else {
        const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const totalSavings = cart.reduce((sum, item) => {
            if (item.originalPrice) {
                return sum + ((item.originalPrice - item.price) * item.quantity);
            }
            return sum;
        }, 0);
        
        cartPopup.innerHTML = `
            <div class="w-96 bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
                <!-- Enhanced Header -->
                <div class="bg-gradient-to-r from-green-600 via-green-700 to-emerald-700 text-white p-6 relative overflow-hidden">
                    <div class="absolute inset-0 bg-gradient-to-r from-green-400/20 to-emerald-400/20"></div>
                    <div class="relative z-10">
                        <div class="flex items-center justify-between mb-4">
                            <div>
                                <h3 class="text-xl font-bold flex items-center gap-3">
                                    <div class="bg-white/20 rounded-full p-2">
                                        <i data-lucide="shopping-cart" class="h-5 w-5"></i>
                                    </div>
                                    Shopping Cart
                                </h3>
                                <p class="text-green-100 text-sm mt-1">
                                    ${cart.reduce((sum, item) => sum + item.quantity, 0)} items • Ready for checkout
                                </p>
                            </div>
                            ${totalSavings > 0 ? `
                                <div class="text-right">
                                    <div class="bg-white/20 rounded-lg px-3 py-1 text-xs font-semibold">
                                        💰 Save $${totalSavings.toFixed(2)}
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                <!-- Cart Items -->
                <div class="max-h-80 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-gray-50 to-white">
                    ${cart.map((item, index) => `
                        <div class="group bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300 hover:border-green-200">
                            <div class="flex items-center gap-4">
                                <!-- Product Image -->
                                <div class="relative">
                                    <img src="${item.image}" alt="${item.name}" class="w-16 h-16 object-cover rounded-lg shadow-sm group-hover:scale-105 transition-transform duration-300">
                                    ${item.originalPrice ? `
                                        <div class="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg">
                                            SALE
                                        </div>
                                    ` : ''}
                                </div>
                                
                                <!-- Product Info -->
                                <div class="flex-1 min-w-0">
                                    <h4 class="font-bold text-gray-900 text-sm line-clamp-1 group-hover:text-green-600 transition-colors">${item.name}</h4>
                                    <p class="text-xs text-gray-600 mt-1 flex items-center gap-1">
                                        <span class="w-2 h-2 bg-green-400 rounded-full"></span>
                                        ${item.brand} • Organic
                                    </p>
                                    
                                    <!-- Quantity Controls -->
                                    <div class="flex items-center justify-between mt-3">
                                        <div class="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
                                            <button onclick="updateCartItemQuantity(${item.id}, ${item.quantity - 1})" 
                                                    class="w-7 h-7 bg-white hover:bg-red-50 rounded-md flex items-center justify-center text-red-600 hover:text-red-700 transition-colors shadow-sm font-bold">
                                                -
                                            </button>
                                            <span class="font-bold text-gray-900 min-w-[24px] text-center">${item.quantity}</span>
                                            <button onclick="updateCartItemQuantity(${item.id}, ${item.quantity + 1})" 
                                                    class="w-7 h-7 bg-white hover:bg-green-50 rounded-md flex items-center justify-center text-green-600 hover:text-green-700 transition-colors shadow-sm font-bold">
                                                +
                                            </button>
                                        </div>
                                        
                                        <!-- Price & Remove -->
                                        <div class="flex items-center gap-3">
                                            <div class="text-right">
                                                <div class="font-bold text-green-600">$${(item.price * item.quantity).toFixed(2)}</div>
                                                ${item.originalPrice ? `
                                                    <div class="text-xs text-gray-500 line-through">$${(item.originalPrice * item.quantity).toFixed(2)}</div>
                                                ` : ''}
                                            </div>
                                            <button onclick="removeFromCart(${item.id})" 
                                                    class="text-red-500 hover:text-red-700 p-2 hover:bg-red-50 rounded-lg transition-colors group"
                                                    title="Remove item">
                                                <i data-lucide="trash-2" class="h-4 w-4 group-hover:scale-110 transition-transform"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <!-- Enhanced Footer -->
                <div class="border-t border-gray-200 bg-gradient-to-r from-gray-50 to-white p-6">
                    <!-- Savings Display -->
                    ${totalSavings > 0 ? `
                        <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-3 mb-4">
                            <div class="flex items-center justify-center gap-2 text-green-700">
                                <i data-lucide="gift" class="h-4 w-4"></i>
                                <span class="font-semibold text-sm">You're saving $${totalSavings.toFixed(2)} today!</span>
                            </div>
                        </div>
                    ` : ''}
                    
                    <!-- Total -->
                    <div class="flex items-center justify-between mb-6 bg-white rounded-lg p-4 shadow-sm border border-gray-100">
                        <div class="flex items-center gap-2">
                            <i data-lucide="calculator" class="h-5 w-5 text-gray-600"></i>
                            <span class="font-bold text-gray-900 text-lg">Total:</span>
                        </div>
                        <div class="text-right">
                            <div class="text-2xl font-bold text-green-600">$${totalPrice.toFixed(2)}</div>
                            <div class="text-xs text-gray-500">Including all savings</div>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="space-y-3">
                        <div class="grid grid-cols-2 gap-3">
                            <a href="cart.html" class="flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-gray-700 hover:text-green-600 px-4 py-3 rounded-xl font-semibold border-2 border-gray-200 hover:border-green-300 transition-all">
                                <i data-lucide="shopping-bag" class="h-4 w-4"></i>
                                View Cart
                            </a>
                            <button onclick="showNotification('🚀 Checkout coming soon!', 'info')" class="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-4 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl">
                                <i data-lucide="credit-card" class="h-4 w-4"></i>
                                Quick Pay
                            </button>
                        </div>
                        
                        <button onclick="showNotification('🛒 Proceeding to secure checkout...', 'success')" class="w-full bg-gradient-to-r from-green-600 via-green-700 to-emerald-700 hover:from-green-700 hover:via-green-800 hover:to-emerald-800 text-white px-4 py-4 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3">
                            <i data-lucide="lock" class="h-5 w-5"></i>
                            Secure Checkout
                            <i data-lucide="arrow-right" class="h-5 w-5"></i>
                        </button>
                    </div>
                    
                    <!-- Trust Indicators -->
                    <div class="flex items-center justify-center gap-4 mt-4 text-xs text-gray-500">
                        <div class="flex items-center gap-1">
                            <i data-lucide="shield-check" class="h-3 w-3 text-green-600"></i>
                            <span>Secure</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <i data-lucide="truck" class="h-3 w-3 text-blue-600"></i>
                            <span>Free Delivery</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <i data-lucide="leaf" class="h-3 w-3 text-green-600"></i>
                            <span>100% Organic</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Cart item quantity update
function updateCartItemQuantity(productId, newQuantity) {
    if (newQuantity <= 0) {
        removeFromCart(productId);
        return;
    }

    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const itemIndex = cart.findIndex(item => item.id === productId);
    
    if (itemIndex > -1) {
        cart[itemIndex].quantity = newQuantity;
        localStorage.setItem('cart', JSON.stringify(cart));
        updateCartDisplay();
    }
}

// Remove from cart
function removeFromCart(productId) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const product = cart.find(item => item.id === productId);
    
    cart = cart.filter(item => item.id !== productId);
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
    
    if (product) {
        showNotification(`${product.name} removed from cart`, 'info');
    }
}

// Add to cart with Ajax popup
function addToCartWithAjax(productId) {
    console.log('Adding to cart with Ajax:', productId);
    
    const product = getProductById(productId);
    if (!product) {
        console.error('Product not found:', productId);
        showNotification('Product not found', 'error');
        return;
    }
    
    // Add to cart
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: productId,
            name: product.name,
            price: product.price,
            originalPrice: product.originalPrice,
            quantity: 1,
            image: product.image,
            brand: product.brand
        });
    }
    
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartDisplay();
    
    // Show Ajax popup
    showAjaxCartPopup(product);
    
    console.log('Product added to cart:', product.name);
}

// Show Enhanced Ajax Cart Popup
function showAjaxCartPopup(product) {
    // Remove existing ajax cart popup
    const existingPopup = document.querySelector('.ajax-cart-modal');
    if (existingPopup) {
        existingPopup.remove();
    }
    
    // Create popup container
    const popup = document.createElement('div');
    popup.className = 'ajax-cart-modal fixed top-0 right-0 h-full w-full max-w-md bg-white shadow-2xl transform translate-x-full transition-all duration-500 ease-out z-50 overflow-hidden';
    
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const totalSavings = cart.reduce((sum, item) => {
        if (item.originalPrice) {
            return sum + ((item.originalPrice - item.price) * item.quantity);
        }
        return sum;
    }, 0);
    
    popup.innerHTML = `
        <div class="h-full flex flex-col bg-gradient-to-b from-white to-gray-50">
            <!-- Enhanced Header with Animation -->
            <div class="bg-gradient-to-r from-green-600 via-green-700 to-emerald-700 text-white p-6 relative overflow-hidden">
                <!-- Background Pattern -->
                <div class="absolute inset-0 opacity-20">
                    <div class="absolute inset-0 bg-gradient-to-r from-green-400/30 to-emerald-400/30"></div>
                    <div class="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-full -translate-x-16 -translate-y-16"></div>
                    <div class="absolute bottom-0 right-0 w-24 h-24 bg-white/10 rounded-full translate-x-12 translate-y-12"></div>
                </div>
                
                <div class="relative z-10">
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-4">
                            <div class="bg-white/20 backdrop-blur-sm rounded-full p-3 animate-bounce">
                                <i data-lucide="check-circle" class="h-6 w-6"></i>
                            </div>
                            <div>
                                <h3 class="text-xl font-bold">Added to Cart!</h3>
                                <p class="text-green-100 text-sm">${product.name}</p>
                            </div>
                        </div>
                        <button onclick="hideAjaxCartPopup()" 
                                class="text-white/80 hover:text-white p-2 hover:bg-white/10 rounded-lg transition-all">
                            <i data-lucide="x" class="h-6 w-6"></i>
                        </button>
                    </div>
                    
                    <!-- Cart Stats -->
                    <div class="flex items-center justify-between text-sm">
                        <div class="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-2">
                            <span class="font-semibold">${cart.reduce((sum, item) => sum + item.quantity, 0)} items in cart</span>
                        </div>
                        ${totalSavings > 0 ? `
                            <div class="bg-white/20 backdrop-blur-sm rounded-lg px-3 py-2">
                                <span class="font-semibold">💰 Save $${totalSavings.toFixed(2)}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>

            <!-- Cart Items with Enhanced Styling -->
            <div class="flex-1 overflow-y-auto p-6">
                <div class="space-y-4">
                    ${cart.map((item, index) => `
                        <div class="group bg-white rounded-2xl p-5 shadow-sm border border-gray-100 hover:shadow-lg transition-all duration-300 hover:border-green-200 ${item.id === product.id ? 'ring-2 ring-green-500 ring-opacity-50 bg-green-50/50' : ''}">
                            <div class="flex items-center gap-4">
                                <!-- Enhanced Product Image -->
                                <div class="relative">
                                    <div class="w-20 h-20 rounded-xl overflow-hidden shadow-md">
                                        <img src="${item.image}" alt="${item.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300">
                                    </div>
                                    ${item.originalPrice ? `
                                        <div class="absolute -top-2 -right-2 bg-gradient-to-r from-red-500 to-red-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg animate-pulse">
                                            SALE
                                        </div>
                                    ` : ''}
                                    ${item.id === product.id ? `
                                        <div class="absolute -top-2 -left-2 bg-gradient-to-r from-green-500 to-green-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow-lg">
                                            NEW
                                        </div>
                                    ` : ''}
                                </div>
                                
                                <!-- Enhanced Product Info -->
                                <div class="flex-1 min-w-0">
                                    <h4 class="font-bold text-gray-900 line-clamp-1 group-hover:text-green-600 transition-colors">${item.name}</h4>
                                    <div class="flex items-center gap-2 mt-1">
                                        <span class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                                        <p class="text-xs text-gray-600">${item.brand} • Organic Certified</p>
                                    </div>
                                    
                                    <!-- Enhanced Quantity Controls -->
                                    <div class="flex items-center justify-between mt-4">
                                        <div class="flex items-center gap-2 bg-gradient-to-r from-gray-100 to-gray-200 rounded-xl p-1 shadow-inner">
                                            <button onclick="updateAjaxCartQuantity(${item.id}, ${item.quantity - 1})" 
                                                    class="w-8 h-8 bg-white hover:bg-red-50 rounded-lg flex items-center justify-center text-red-600 hover:text-red-700 transition-all shadow-sm font-bold hover:scale-110">
                                                -
                                            </button>
                                            <span class="font-bold text-gray-900 min-w-[28px] text-center bg-white rounded-lg px-2 py-1 shadow-sm">${item.quantity}</span>
                                            <button onclick="updateAjaxCartQuantity(${item.id}, ${item.quantity + 1})" 
                                                    class="w-8 h-8 bg-white hover:bg-green-50 rounded-lg flex items-center justify-center text-green-600 hover:text-green-700 transition-all shadow-sm font-bold hover:scale-110">
                                                +
                                            </button>
                                        </div>
                                        
                                        <!-- Enhanced Price & Remove -->
                                        <div class="flex items-center gap-3">
                                            <div class="text-right">
                                                <div class="font-bold text-green-600 text-lg">$${(item.price * item.quantity).toFixed(2)}</div>
                                                ${item.originalPrice ? `
                                                    <div class="text-xs text-gray-500 line-through">$${(item.originalPrice * item.quantity).toFixed(2)}</div>
                                                ` : ''}
                                            </div>
                                            <button onclick="removeFromAjaxCart(${item.id})" 
                                                    class="text-red-500 hover:text-red-700 p-2 hover:bg-red-50 rounded-xl transition-all group/btn"
                                                    title="Remove item">
                                                <i data-lucide="trash-2" class="h-4 w-4 group-hover/btn:scale-110 transition-transform"></i>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Enhanced Footer -->
            <div class="border-t border-gray-200 bg-gradient-to-b from-white to-gray-50 p-6 shadow-lg">
                <!-- Savings Banner -->
                ${totalSavings > 0 ? `
                    <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-xl p-4 mb-6 shadow-sm">
                        <div class="flex items-center justify-center gap-3 text-green-700">
                            <div class="bg-green-500 rounded-full p-2">
                                <i data-lucide="gift" class="h-4 w-4 text-white"></i>
                            </div>
                            <span class="font-bold">🎉 You're saving $${totalSavings.toFixed(2)} today!</span>
                        </div>
                    </div>
                ` : ''}
                
                <!-- Enhanced Total -->
                <div class="bg-white rounded-2xl p-6 shadow-md border border-gray-100 mb-6">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-3">
                            <div class="bg-gradient-to-r from-green-600 to-emerald-600 rounded-full p-2">
                                <i data-lucide="calculator" class="h-5 w-5 text-white"></i>
                            </div>
                            <span class="font-bold text-gray-900 text-xl">Total:</span>
                        </div>
                        <div class="text-right">
                            <div class="text-3xl font-bold text-green-600">$${totalPrice.toFixed(2)}</div>
                            <div class="text-xs text-gray-500">Tax included • Free delivery</div>
                        </div>
                    </div>
                </div>
                
                <!-- Enhanced Action Buttons -->
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <button onclick="hideAjaxCartPopup()" 
                                class="flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-gray-700 hover:text-green-600 px-4 py-3 rounded-xl font-semibold border-2 border-gray-200 hover:border-green-300 transition-all shadow-md">
                            <i data-lucide="arrow-left" class="h-4 w-4"></i>
                            Continue
                        </button>
                        <a href="cart.html" 
                           class="flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-4 py-3 rounded-xl font-semibold transition-all shadow-lg hover:shadow-xl">
                            <i data-lucide="shopping-bag" class="h-4 w-4"></i>
                            View Cart
                        </a>
                    </div>
                    
                    <button onclick="showNotification('🛒 Proceeding to secure checkout...', 'success')" 
                            class="w-full bg-gradient-to-r from-green-600 via-green-700 to-emerald-700 hover:from-green-700 hover:via-green-800 hover:to-emerald-800 text-white px-4 py-5 rounded-2xl font-bold text-lg transition-all shadow-xl hover:shadow-2xl flex items-center justify-center gap-3 group">
                        <i data-lucide="lock" class="h-5 w-5 group-hover:scale-110 transition-transform"></i>
                        Secure Checkout ($${totalPrice.toFixed(2)})
                        <i data-lucide="arrow-right" class="h-5 w-5 group-hover:translate-x-1 transition-transform"></i>
                    </button>
                </div>
                
                <!-- Enhanced Trust Indicators -->
                <div class="flex items-center justify-center gap-6 mt-6 text-xs text-gray-500">
                    <div class="flex items-center gap-2">
                        <i data-lucide="shield-check" class="h-4 w-4 text-green-600"></i>
                        <span>SSL Secure</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i data-lucide="truck" class="h-4 w-4 text-blue-600"></i>
                        <span>Free Delivery</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <i data-lucide="leaf" class="h-4 w-4 text-green-600"></i>
                        <span>100% Organic</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'ajax-cart-backdrop fixed inset-0 bg-black/50 backdrop-blur-sm opacity-0 pointer-events-none transition-all duration-500 z-40';
    backdrop.onclick = hideAjaxCartPopup;
    
    document.body.appendChild(backdrop);
    document.body.appendChild(popup);
    
    // Show with enhanced animation
    setTimeout(() => {
        popup.classList.remove('translate-x-full');
        popup.classList.add('translate-x-0');
        backdrop.classList.remove('pointer-events-none', 'opacity-0');
    }, 50);
    
    // Auto-hide after 8 seconds
    setTimeout(() => {
        if (document.querySelector('.ajax-cart-modal')) {
            hideAjaxCartPopup();
        }
    }, 8000);
    
    // Initialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    showNotification(`🛒 ${product.name} added to cart!`, 'success');
}

// Hide Ajax Cart Popup
function hideAjaxCartPopup() {
    const popup = document.querySelector('.ajax-cart-modal');
    const backdrop = document.querySelector('.ajax-cart-backdrop');
    
    if (popup) {
        popup.classList.remove('translate-x-0');
        popup.classList.add('translate-x-full');
    }
    
    if (backdrop) {
        backdrop.classList.add('pointer-events-none', 'opacity-0');
    }
    
    setTimeout(() => {
        if (popup) popup.remove();
        if (backdrop) backdrop.remove();
    }, 500);
}

// Update Ajax Cart Quantity
function updateAjaxCartQuantity(productId, newQuantity) {
    if (newQuantity <= 0) {
        removeFromAjaxCart(productId);
        return;
    }

    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const itemIndex = cart.findIndex(item => item.id === productId);
    
    if (itemIndex > -1) {
        cart[itemIndex].quantity = newQuantity;
        localStorage.setItem('cart', JSON.stringify(cart));
        
        // Update both displays
        updateCartDisplay();
        
        // Refresh ajax popup content
        const popup = document.querySelector('.ajax-cart-modal');
        if (popup) {
            const product = getProductById(productId);
            showAjaxCartPopup(product);
        }
    }
}

// Remove from Ajax Cart
function removeFromAjaxCart(productId) {
    let cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const product = cart.find(item => item.id === productId);
    
    cart = cart.filter(item => item.id !== productId);
    localStorage.setItem('cart', JSON.stringify(cart));
    
    updateCartDisplay();
    
    if (product) {
        showNotification(`${product.name} removed from cart`, 'info');
    }
    
    // Refresh ajax popup if open
    const popup = document.querySelector('.ajax-cart-modal');
    if (popup) {
        if (cart.length > 0) {
            showAjaxCartPopup(cart[0]);
        } else {
            hideAjaxCartPopup();
        }
    }
}

// Cart dropdown functions
function showCartDropdown() {
    updateCartPopup();
    const cartPopup = document.getElementById('cart-popup');
    if (cartPopup) {
        cartPopup.classList.remove('hidden');
        cartPopup.style.display = 'block';
    }
}

function hideCartDropdown() {
    const cartPopup = document.getElementById('cart-popup');
    if (cartPopup) {
        cartPopup.classList.add('hidden');
        cartPopup.style.display = 'none';
    }
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.initializeDemoCartItems = initializeDemoCartItems;
    window.updateCartDisplay = updateCartDisplay;
    window.updateCartPopup = updateCartPopup;
    window.updateCartItemQuantity = updateCartItemQuantity;
    window.removeFromCart = removeFromCart;
    window.addToCartWithAjax = addToCartWithAjax;
    window.showAjaxCartPopup = showAjaxCartPopup;
    window.hideAjaxCartPopup = hideAjaxCartPopup;
    window.updateAjaxCartQuantity = updateAjaxCartQuantity;
    window.removeFromAjaxCart = removeFromAjaxCart;
    window.showCartDropdown = showCartDropdown;
    window.hideCartDropdown = hideCartDropdown;
}