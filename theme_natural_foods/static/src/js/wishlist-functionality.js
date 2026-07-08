// Wishlist Functionality

// Initialize wishlist
function initializeWishlist() {
    console.log('Initializing wishlist...');
    
    // Create wishlist in localStorage if it doesn't exist
    if (!localStorage.getItem('wishlist')) {
        localStorage.setItem('wishlist', JSON.stringify([]));
    }
    
    console.log('Wishlist initialized');
}

// Add to wishlist function
function addToWishlist(productId) {
    const product = getProductById(productId);
    if (!product) {
        showNotification('Product not found', 'error');
        return;
    }
    
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    
    // Check if product is already in wishlist
    const existingIndex = wishlist.findIndex(item => item.id === productId);
    
    if (existingIndex > -1) {
        // Remove from wishlist
        wishlist.splice(existingIndex, 1);
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
        showNotification(`${product.name} removed from wishlist`, 'info');
        
        // Update wishlist button appearance
        updateWishlistButton(productId, false);
    } else {
        // Add to wishlist
        wishlist.push({
            id: productId,
            name: product.name,
            price: product.price,
            originalPrice: product.originalPrice,
            image: product.image,
            brand: product.brand,
            rating: product.rating,
            category: product.category,
            addedAt: new Date().toISOString()
        });
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
        showNotification(`❤️ ${product.name} added to wishlist!`, 'success');
        
        // Update wishlist button appearance
        updateWishlistButton(productId, true);
    }
}

// Update wishlist button appearance
function updateWishlistButton(productId, isInWishlist) {
    const buttons = document.querySelectorAll(`[data-wishlist-id="${productId}"]`);
    buttons.forEach(button => {
        const icon = button.querySelector('i');
        if (isInWishlist) {
            button.classList.remove('text-gray-400', 'hover:text-red-500', 'bg-white/90');
            button.classList.add('text-white', 'bg-red-500');
            if (icon) {
                icon.setAttribute('data-lucide', 'heart');
                icon.classList.add('fill-current');
            }
        } else {
            button.classList.remove('text-white', 'bg-red-500');
            button.classList.add('text-gray-400', 'hover:text-red-500', 'bg-white/90');
            if (icon) {
                icon.setAttribute('data-lucide', 'heart');
                icon.classList.remove('fill-current');
            }
        }
    });
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Check if product is in wishlist
function isInWishlist(productId) {
    const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    return wishlist.some(item => item.id === productId);
}

// Get wishlist items
function getWishlistItems() {
    return JSON.parse(localStorage.getItem('wishlist') || '[]');
}

// Remove from wishlist by ID
function removeFromWishlist(productId) {
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    const product = wishlist.find(item => item.id === productId);
    
    wishlist = wishlist.filter(item => item.id !== productId);
    localStorage.setItem('wishlist', JSON.stringify(wishlist));
    
    if (product) {
        showNotification(`${product.name} removed from wishlist`, 'info');
        updateWishlistButton(productId, false);
    }
}

// Clear entire wishlist
function clearWishlist() {
    localStorage.setItem('wishlist', JSON.stringify([]));
    showNotification('Wishlist cleared', 'info');
    
    // Update all wishlist buttons
    document.querySelectorAll('[data-wishlist-id]').forEach(button => {
        const productId = parseInt(button.getAttribute('data-wishlist-id'));
        updateWishlistButton(productId, false);
    });
}

// Get wishlist count
function getWishlistCount() {
    const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    return wishlist.length;
}

// Move wishlist item to cart
function moveToCart(productId) {
    const wishlistItem = getWishlistItems().find(item => item.id === productId);
    if (!wishlistItem) {
        showNotification('Product not found in wishlist', 'error');
        return;
    }
    
    // Add to cart
    addToCartWithAjax(productId);
    
    // Remove from wishlist
    removeFromWishlist(productId);
    
    showNotification(`${wishlistItem.name} moved to cart!`, 'success');
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.initializeWishlist = initializeWishlist;
    window.addToWishlist = addToWishlist;
    window.updateWishlistButton = updateWishlistButton;
    window.isInWishlist = isInWishlist;
    window.getWishlistItems = getWishlistItems;
    window.removeFromWishlist = removeFromWishlist;
    window.clearWishlist = clearWishlist;
    window.getWishlistCount = getWishlistCount;
    window.moveToCart = moveToCart;
}