// Cart functionality for the organic store

// Cart state with pre-populated items
let cartState = {
    items: JSON.parse(localStorage.getItem('cart') || JSON.stringify([
        {
            id: 1,
            name: "Organic Baby Spinach",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
            quantity: 2
        },
        {
            id: 6,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
            quantity: 1
        },
        {
            id: 11,
            name: "Organic Whole Milk",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
            quantity: 1
        }
    ])),
    total: 0,
    itemCount: 0
};

// Update cart calculations
function updateCartCalculations() {
    cartState.itemCount = cartState.items.reduce((total, item) => total + item.quantity, 0);
    cartState.total = cartState.items.reduce((total, item) => total + (item.price * item.quantity), 0);
}

// Save cart to localStorage
function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cartState.items));
    updateCartCalculations();
    updateCartDisplay();
}

// Add item to cart
function addToCart(productId) {
    const product = getAllProducts().find(p => p.id === parseInt(productId));
    if (!product) return;

    const existingItem = cartState.items.find(item => item.id === product.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cartState.items.push({
            id: product.id,
            name: product.name,
            price: product.price,
            image: product.image,
            quantity: 1
        });
    }
    
    saveCart();
    showCartAddedNotification(product);
}

// Remove item from cart
function removeFromCart(productId) {
    cartState.items = cartState.items.filter(item => item.id !== parseInt(productId));
    saveCart();
}

// Update item quantity
function updateQuantity(productId, newQuantity) {
    const item = cartState.items.find(item => item.id === parseInt(productId));
    if (item && newQuantity > 0) {
        item.quantity = newQuantity;
        saveCart();
    }
}

// Clear entire cart
function clearCart() {
    cartState.items = [];
    saveCart();
}

// Update cart display in header
function updateCartDisplay() {
    updateCartCalculations();
    
    const cartCount = document.getElementById('cart-count');
    if (cartCount) {
        if (cartState.itemCount > 0) {
            cartCount.textContent = cartState.itemCount;
            cartCount.classList.remove('hidden');
        } else {
            cartCount.classList.add('hidden');
        }
    }
}

// Toggle cart popup
function toggleCartPopup() {
    const popup = document.getElementById('cart-popup');
    if (popup.classList.contains('hidden')) {
        showCartPopup();
    } else {
        hideCartPopup();
    }
}

// Show cart popup
function showCartPopup() {
    const popup = document.getElementById('cart-popup');
    updateCartPopupContent();
    popup.classList.remove('hidden');
    
    // Hide popup when clicking outside
    setTimeout(() => {
        document.addEventListener('click', handleOutsideClick);
    }, 100);
}

// Hide cart popup
function hideCartPopup() {
    const popup = document.getElementById('cart-popup');
    popup.classList.add('hidden');
    document.removeEventListener('click', handleOutsideClick);
}

// Handle clicks outside cart popup
function handleOutsideClick(event) {
    const popup = document.getElementById('cart-popup');
    const cartButton = popup.previousElementSibling;
    
    if (!popup.contains(event.target) && !cartButton.contains(event.target)) {
        hideCartPopup();
    }
}

// Update cart popup content
function updateCartPopupContent() {
    const popup = document.getElementById('cart-popup');
    
    if (cartState.items.length === 0) {
        popup.innerHTML = `
            <div class="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4 text-white">
                <h4 class="font-semibold text-lg flex items-center gap-2">
                    <i data-lucide="shopping-cart" class="h-5 w-5"></i>
                    Shopping Cart
                </h4>
                <p class="text-green-100 text-sm">0 items • $0.00</p>
            </div>
            <div class="px-6 py-12 text-center">
                <div class="bg-gray-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <i data-lucide="shopping-cart" class="h-8 w-8 text-gray-400"></i>
                </div>
                <p class="text-gray-600 font-medium">Your cart is empty</p>
                <p class="text-sm text-gray-500 mt-1">Start shopping to add items!</p>
                <button onclick="navigateTo('products.html')" class="mt-4 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    Start Shopping
                </button>
            </div>
        `;
    } else {
        const itemsHtml = cartState.items.slice(0, 4).map((item, index) => `
            <div class="px-6 py-4 flex items-center gap-4 hover:bg-gray-50 transition-colors ${index !== 0 ? 'border-t border-gray-100' : ''}">
                <div class="relative">
                    <img src="${item.image}" alt="${item.name}" class="w-14 h-14 object-cover rounded-xl shadow-md">
                    <div class="absolute -top-2 -right-2 bg-green-500 text-white rounded-full text-xs w-5 h-5 flex items-center justify-center font-semibold">
                        ${item.quantity}
                    </div>
                </div>
                <div class="flex-1 min-w-0">
                    <h5 class="font-semibold text-gray-800 truncate text-sm">${item.name}</h5>
                    <p class="text-green-600 font-medium text-sm">$${item.price.toFixed(2)} each</p>
                    <p class="text-xs text-gray-500">Total: $${(item.price * item.quantity).toFixed(2)}</p>
                </div>
                <div class="flex items-center gap-1">
                    <button onclick="updateQuantity(${item.id}, ${item.quantity - 1})" class="h-7 w-7 rounded-full hover:bg-gray-200 flex items-center justify-center">
                        <i data-lucide="minus" class="h-3 w-3"></i>
                    </button>
                    <span class="text-sm w-8 text-center font-medium">${item.quantity}</span>
                    <button onclick="updateQuantity(${item.id}, ${item.quantity + 1})" class="h-7 w-7 rounded-full hover:bg-gray-200 flex items-center justify-center">
                        <i data-lucide="plus" class="h-3 w-3"></i>
                    </button>
                    <button onclick="removeFromCart(${item.id})" class="h-7 w-7 rounded-full text-red-500 hover:text-red-700 hover:bg-red-50 ml-1 flex items-center justify-center">
                        <i data-lucide="x" class="h-3 w-3"></i>
                    </button>
                </div>
            </div>
        `).join('');
        
        const moreItemsHtml = cartState.items.length > 4 ? `
            <div class="px-6 py-3 text-center text-sm text-gray-500 bg-gray-50">
                <span class="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                    +${cartState.items.length - 4} more items
                </span>
            </div>
        ` : '';

        popup.innerHTML = `
            <div class="bg-gradient-to-r from-green-600 to-green-700 px-6 py-4 text-white">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-semibold text-lg flex items-center gap-2">
                            <i data-lucide="shopping-cart" class="h-5 w-5"></i>
                            Shopping Cart
                        </h4>
                        <p class="text-green-100 text-sm">${cartState.itemCount} items • $${cartState.total.toFixed(2)}</p>
                    </div>
                    <div class="bg-white/20 backdrop-blur-sm rounded-full px-3 py-1">
                        <span class="text-sm font-medium">${cartState.itemCount}</span>
                    </div>
                </div>
            </div>
            <div class="max-h-80 overflow-y-auto">
                ${itemsHtml}
                ${moreItemsHtml}
            </div>
            <div class="border-t border-gray-200 bg-white px-6 py-5">
                <div class="bg-green-50 rounded-lg p-3 mb-4">
                    <p class="text-xs text-green-700 font-medium flex items-center gap-1">
                        🚚 ${cartState.total >= 50 ? 'Free shipping included!' : `Add $${(50 - cartState.total).toFixed(2)} more for free shipping`}
                    </p>
                </div>
                
                <div class="flex justify-between items-center mb-4">
                    <span class="text-gray-700 font-medium">Subtotal:</span>
                    <span class="text-xl font-bold text-green-600">$${cartState.total.toFixed(2)}</span>
                </div>
                
                <div class="space-y-3">
                    <button onclick="navigateTo('cart.html')" class="w-full border border-green-600 text-green-600 hover:bg-green-50 py-3 rounded-lg font-medium transition-colors">
                        View Full Cart
                    </button>
                    <button onclick="navigateTo('checkout.html')" class="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white py-3 rounded-lg font-semibold transition-all duration-300">
                        Secure Checkout →
                    </button>
                </div>
            </div>
        `;
    }
    
    // Re-initialize Lucide icons
    lucide.createIcons();
}

// Show cart added notification
function showCartAddedNotification(product) {
    // Create temporary notification
    const notification = document.createElement('div');
    notification.className = 'fixed top-4 right-4 bg-green-600 text-white p-4 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300';
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-white rounded-lg overflow-hidden">
                <img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover">
            </div>
            <div>
                <p class="font-semibold">Added to Cart!</p>
                <p class="text-sm opacity-90">${product.name}</p>
            </div>
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
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Get cart summary for other pages
function getCartSummary() {
    updateCartCalculations();
    return {
        itemCount: cartState.itemCount,
        total: cartState.total,
        items: cartState.items
    };
}

// Initialize cart with sample data if empty
function initializeCartWithSampleData() {
    if (cartState.items.length === 0) {
        // Add some sample items to the cart
        const sampleItems = [
            {
                id: 1,
                name: "Organic Baby Spinach",
                price: 4.99,
                image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
                quantity: 2
            },
            {
                id: 6,
                name: "Organic Honey Crisp Apples",
                price: 5.99,
                image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
                quantity: 1
            },
            {
                id: 11,
                name: "Organic Whole Milk",
                price: 3.49,
                image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
                quantity: 1
            }
        ];
        
        cartState.items = sampleItems;
        saveCart();
    }
}

// Initialize cart on page load
updateCartCalculations();

// Add sample data if cart is empty (for demo purposes)
if (cartState.items.length === 0) {
    initializeCartWithSampleData();
}