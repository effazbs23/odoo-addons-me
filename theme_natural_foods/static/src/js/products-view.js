// Products page view management and functionality

// Current view mode
let currentView = 'grid';

// View toggle functionality
function switchToGridView() {
    currentView = 'grid';
    document.getElementById('products-grid').classList.remove('hidden');
    document.getElementById('products-list').classList.add('hidden');
    
    // Update button states
    document.getElementById('grid-view-btn').classList.add('active');
    document.getElementById('list-view-btn').classList.remove('active');
}

function switchToListView() {
    currentView = 'list';
    document.getElementById('products-grid').classList.add('hidden');
    document.getElementById('products-list').classList.remove('hidden');
    
    // Update button states
    document.getElementById('grid-view-btn').classList.remove('active');
    document.getElementById('list-view-btn').classList.add('active');
}

// Filter toggle functionality
function toggleFilter(filterId) {
    const content = document.getElementById(filterId + '-content');
    const icon = document.getElementById(filterId + '-icon');
    
    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        icon.setAttribute('data-lucide', 'chevron-up');
    } else {
        content.classList.add('collapsed');
        icon.setAttribute('data-lucide', 'chevron-down');
    }
    
    // Reinitialize icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Navigation functions
function navigateTo(url) {
    window.location.href = url;
}

function navigateToProduct(productId) {
    window.location.href = `product-details.html?id=${productId}`;
}

// Search functionality
function performSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput && searchInput.value.trim()) {
        window.location.href = `products.html?search=${encodeURIComponent(searchInput.value.trim())}`;
    }
}

// Product interactions
function addToCart(productId) {
    showNotification('🛒 Product added to cart successfully!', 'success');
}

function toggleWishlist(productId) {
    showNotification('💖 Added to your wishlist!', 'success');
}

function quickViewProduct(productId) {
    showNotification('👀 Quick view opening soon!', 'info');
}

// Cart popup functionality
function toggleCartPopup() {
    const cartPopup = document.getElementById('cart-popup');
    if (cartPopup) {
        cartPopup.classList.toggle('hidden');
    }
}

// Mega menu functionality
function showMegaMenu() {
    showNotification('🍳 Explore our delicious recipes!', 'info');
}

function hideMegaMenu() {
    // Hide mega menu logic
}

// Enhanced notification function
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-4 rounded-xl text-white font-semibold z-50 transform translate-x-full transition-all duration-500 shadow-2xl ${
        type === 'success' ? 'bg-gradient-to-r from-green-500 to-green-600' : 
        type === 'error' ? 'bg-gradient-to-r from-red-500 to-red-600' : 
        'bg-gradient-to-r from-blue-500 to-blue-600'
    }`;
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="bg-white/20 p-1 rounded-full">
                <i data-lucide="${type === 'success' ? 'check' : type === 'error' ? 'x' : 'info'}" class="h-4 w-4"></i>
            </div>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Initialize Lucide icons for notification
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 4 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 4000);
}

// Update cart display function (placeholder)
function updateCartDisplay() {
    // This would typically load from localStorage or API
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    updateCartDisplay();
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Show welcome message
    setTimeout(() => {
        showNotification('🌟 Welcome to our premium organic collection!', 'success');
    }, 1000);
});