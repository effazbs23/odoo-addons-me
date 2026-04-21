/**
 * Home Page Products with Quick View functionality
 * Bootstrap version
 */

// Sample products data for home page
const HOME_PRODUCTS_DATA = [
    {
        id: 1,
        name: "Organic Rainbow Carrots",
        price: 3.99,
        originalPrice: 4.99,
        description: "Fresh & crisp organic carrots in beautiful rainbow colors",
        image: "https://images.unsplash.com/photo-1574457342635-b96fe21dba37?auto=format&fit=crop&w=300&q=80",
        category: "vegetables",
        brand: "Fresh Farm",
        rating: 4.7,
        reviews: 124,
        sale: true,
        featured: true,
        new: false,
        inStock: true,
        weight: "1 lb"
    },
    {
        id: 2,
        name: "Organic Blueberries",
        price: 6.99,
        description: "Sweet organic blueberries, perfect for snacking",
        image: "https://images.unsplash.com/photo-1464740595110-df5dc638c050?auto=format&fit=crop&w=300&q=80",
        category: "fruits",
        brand: "Berry Fresh",
        rating: 4.9,
        reviews: 203,
        sale: false,
        featured: true,
        new: false,
        inStock: true,
        weight: "6 oz"
    },
    {
        id: 3,
        name: "Baby Spinach",
        price: 4.49,
        description: "Tender organic baby spinach leaves, perfect for salads",
        image: "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=300&q=80",
        category: "vegetables",
        brand: "Green Valley",
        rating: 4.3,
        reviews: 87,
        sale: false,
        featured: true,
        new: false,
        inStock: true,
        weight: "5 oz"
    },
    {
        id: 4,
        name: "Organic Baby Kale",
        price: 5.49,
        description: "Fresh organic baby kale, nutrient-rich and delicious",
        image: "https://images.unsplash.com/photo-1587132137056-bfbf0166836e?auto=format&fit=crop&w=300&q=80",
        category: "vegetables",
        brand: "Fresh Farm",
        rating: 4.9,
        reviews: 156,
        sale: false,
        featured: false,
        new: true,
        inStock: true,
        weight: "5 oz"
    },
    {
        id: 5,
        name: "Organic Strawberries",
        price: 5.99,
        description: "Juicy organic strawberries, locally grown",
        image: "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?auto=format&fit=crop&w=300&q=80",
        category: "fruits",
        brand: "Berry Fresh",
        rating: 4.8,
        reviews: 189,
        sale: false,
        featured: false,
        new: false,
        inStock: true,
        weight: "1 lb"
    },
    {
        id: 6,
        name: "Greek Yogurt",
        price: 8.99,
        originalPrice: 10.99,
        description: "Creamy organic Greek yogurt, high in protein",
        image: "https://images.unsplash.com/photo-1517982049499-6d5b0d83162b?auto=format&fit=crop&w=300&q=80",
        category: "dairy",
        brand: "Pure Greek",
        rating: 4.6,
        reviews: 142,
        sale: true,
        featured: true,
        new: false,
        inStock: true,
        weight: "32 oz"
    },
    {
        id: 7,
        name: "Wild-Caught Salmon",
        price: 13.99,
        originalPrice: 19.99,
        description: "Premium wild-caught salmon fillets",
        image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=300&q=80",
        category: "seafood",
        brand: "Ocean Fresh",
        rating: 4.9,
        reviews: 234,
        sale: true,
        featured: false,
        new: false,
        inStock: true,
        weight: "1 lb"
    },
    {
        id: 8,
        name: "Quinoa Sourdough Bread",
        price: 7.99,
        description: "Artisan quinoa sourdough bread, freshly baked",
        image: "https://images.unsplash.com/photo-1569185276932-6275582dbc81?auto=format&fit=crop&w=300&q=80",
        category: "bakery",
        brand: "Artisan Bakery",
        rating: 4.8,
        reviews: 98,
        sale: false,
        featured: false,
        new: true,
        inStock: true,
        weight: "1 loaf"
    }
];

// Function to add Quick View buttons to existing product cards
function addQuickViewButtons() {
    console.log('🏠 Adding Quick View buttons to home page products...');
    
    // Find all product cards and add quick view buttons
    const productCards = document.querySelectorAll('.card');
    
    productCards.forEach((card, index) => {
        // Skip if already has quick view button
        if (card.querySelector('.quick-view-btn')) {
            return;
        }
        
        // Find the image container
        const imageContainer = card.querySelector('.product-image-container') || card.querySelector('img')?.parentElement;
        
        if (imageContainer) {
            // Make sure container is positioned relative
            if (!imageContainer.classList.contains('product-image-container')) {
                imageContainer.classList.add('product-image-container');
            }
            
            // Create quick view button
            const quickViewBtn = document.createElement('button');
            quickViewBtn.className = 'quick-view-btn';
            quickViewBtn.setAttribute('onclick', `quickViewProduct(${index + 1})`);
            quickViewBtn.setAttribute('title', 'Quick View');
            quickViewBtn.innerHTML = '<i class="bi bi-eye"></i>';
            
            // Create wishlist button
            const wishlistBtn = document.createElement('button');
            wishlistBtn.className = 'wishlist-btn';
            wishlistBtn.setAttribute('onclick', `toggleWishlist(${index + 1})`);
            wishlistBtn.setAttribute('title', 'Add to Wishlist');
            wishlistBtn.innerHTML = '<i class="bi bi-heart"></i>';
            
            // Add buttons to container
            imageContainer.appendChild(quickViewBtn);
            imageContainer.appendChild(wishlistBtn);
        }
    });
}

// Home page specific cart and wishlist functions
function addToCartHome(productId) {
    console.log('🛒 Adding product to cart:', productId);
    
    const product = HOME_PRODUCTS_DATA.find(p => p.id === productId);
    if (!product) {
        console.error('Product not found:', productId);
        return;
    }
    
    // Show success toast
    showHomeToast(`${product.name} added to cart!`, 'success');
}

function toggleWishlist(productId) {
    console.log('❤️ Toggling wishlist for product:', productId);
    
    const product = HOME_PRODUCTS_DATA.find(p => p.id === productId);
    if (!product) {
        console.error('Product not found:', productId);
        return;
    }
    
    // Find the wishlist button
    const wishlistBtns = document.querySelectorAll(`[onclick="toggleWishlist(${productId})"]`);
    
    wishlistBtns.forEach(btn => {
        const icon = btn.querySelector('i');
        if (btn.classList.contains('active')) {
            // Remove from wishlist
            btn.classList.remove('active');
            if (icon) icon.className = 'bi bi-heart';
            showHomeToast(`${product.name} removed from wishlist!`, 'info');
        } else {
            // Add to wishlist
            btn.classList.add('active');
            if (icon) icon.className = 'bi bi-heart-fill';
            showHomeToast(`${product.name} added to wishlist!`, 'success');
        }
    });
}

// Home page toast function
function showHomeToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = 'toast';
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-primary';
    const iconClass = type === 'success' ? 'bi-check-circle' : type === 'error' ? 'bi-x-circle' : 'bi-info-circle';
    
    toastEl.innerHTML = `
        <div class="toast-body ${bgClass} text-white fw-medium d-flex align-items-center gap-2">
            <i class="bi ${iconClass}"></i>
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toastEl);
    
    // Initialize and show Bootstrap toast
    const bsToast = new bootstrap.Toast(toastEl, { delay: 3000 });
    bsToast.show();
    
    // Remove toast element after it's hidden
    toastEl.addEventListener('hidden.bs.toast', () => {
        toastContainer.removeChild(toastEl);
    });
}

// Make HOME_PRODUCTS_DATA available globally for quick view
window.PRODUCTS_DATA = HOME_PRODUCTS_DATA;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏠 Home products JavaScript loaded');
    
    // Add quick view buttons after a short delay to ensure page is rendered
    setTimeout(addQuickViewButtons, 500);
});