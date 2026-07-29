// Product Details Event Handlers - All interaction and event handling logic

let currentProduct = null;
let quantity = 1;
let selectedTab = 'description';
let selectedImage = 0;
let selectedAttributes = {};

// Initialize the page
function initializeProductDetails() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Get product ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    const productId = parseInt(urlParams.get('id')) || 1;
    
    loadProduct(productId);
    loadRelatedProducts(productId);
}

// Load product details
function loadProduct(productId) {
    currentProduct = enhancedProductsData.find(p => p.id === productId) || enhancedProductsData[0];
    
    // Update title and breadcrumb
    document.title = `${currentProduct.name} - Natural Foods Organic Store`;
    document.getElementById('breadcrumb-category').textContent = currentProduct.category.charAt(0).toUpperCase() + currentProduct.category.slice(1);
    document.getElementById('breadcrumb-product').textContent = currentProduct.name;
    
    // Render product details
    renderProduct();
    renderTabContent();
}

// Render the complete product
function renderProduct() {
    const container = document.getElementById('product-container');
    container.innerHTML = renderProductDetails(currentProduct, selectedImage, quantity, selectedAttributes);
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Handle attribute change
function handleAttributeChange(type, value, price) {
    selectedAttributes[type] = value;
    
    // Update price if it's a weight change
    if (type === 'weight' && price) {
        updatePricing();
    }
    
    // Re-render to update selection
    renderProduct();
}

// Update pricing display
function updatePricing() {
    const currentPrice = getCurrentPrice(currentProduct, selectedAttributes);
    const priceElement = document.getElementById('current-price');
    const totalPriceElement = document.getElementById('total-price');
    
    if (priceElement) {
        priceElement.textContent = `$${currentPrice.toFixed(2)}`;
    }
    
    if (totalPriceElement) {
        totalPriceElement.textContent = `$${(currentPrice * quantity).toFixed(2)}`;
    }
}

// Change main image
function changeMainImage(imageSrc, index) {
    selectedImage = index;
    document.getElementById('main-image').src = imageSrc;
    
    // Update thumbnails
    document.querySelectorAll('.thumbnail').forEach((thumb, i) => {
        if (i === index) {
            thumb.classList.add('active', 'border-green-500');
            thumb.classList.remove('border-gray-200');
        } else {
            thumb.classList.remove('active', 'border-green-500');
            thumb.classList.add('border-gray-200');
        }
    });
}

// Change quantity
function changeQuantity(change) {
    quantity = Math.max(1, quantity + change);
    document.getElementById('quantity-display').textContent = quantity;
    updatePricing();
    
    // Update decrease button state
    const decreaseBtn = document.getElementById('decrease-btn');
    if (quantity <= 1) {
        decreaseBtn.disabled = true;
        decreaseBtn.classList.add('opacity-50', 'cursor-not-allowed');
    } else {
        decreaseBtn.disabled = false;
        decreaseBtn.classList.remove('opacity-50', 'cursor-not-allowed');
    }
}

// Tab management
function setActiveTab(tabId) {
    selectedTab = tabId;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        btn.classList.add('text-gray-600', 'hover:text-green-600', 'hover:bg-green-50');
    });
    
    document.getElementById(`tab-${tabId}`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.remove('text-gray-600', 'hover:text-green-600', 'hover:bg-green-50');
    
    renderTabContent();
}

// Render tab content
function renderTabContent() {
    const container = document.getElementById('tab-content');
    const template = tabTemplates[selectedTab];
    
    if (template) {
        container.innerHTML = template(currentProduct);
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
}

// Load related products
function loadRelatedProducts(currentProductId) {
    const relatedProducts = enhancedProductsData
        .filter(p => p.id !== currentProductId && (p.category === currentProduct.category || Math.random() > 0.5))
        .slice(0, 4);
    
    const container = document.getElementById('related-products');
    container.innerHTML = relatedProducts.map(product => createRelatedProductCard(product)).join('');
    
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Action handlers
function addToCart() {
    if (!currentProduct.inStock) {
        showNotification('Product is currently out of stock', 'error');
        return;
    }
    
    showNotification(`${currentProduct.name} (${quantity}x) added to cart!`, 'success');
}

function addToWishlist() {
    showNotification(`${currentProduct.name} added to wishlist!`, 'success');
}

function buyNow() {
    if (!currentProduct.inStock) {
        showNotification('Product is currently out of stock', 'error');
        return;
    }
    
    showNotification('Redirecting to checkout...', 'info');
    setTimeout(() => {
        window.location.href = 'cart.html';
    }, 1500);
}

function shareProduct() {
    const url = window.location.href;
    if (navigator.share) {
        navigator.share({
            title: currentProduct.name,
            text: currentProduct.description,
            url: url
        });
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(url).then(() => {
            showNotification('Product link copied to clipboard!', 'success');
        });
    }
}

function quickAddToCart(productId) {
    const product = enhancedProductsData.find(p => p.id === productId);
    if (product) {
        showNotification(`${product.name} added to cart!`, 'success');
    }
}

function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    if (query.length > 0) {
        window.location.href = `products.html?search=${encodeURIComponent(query)}`;
    } else {
        showNotification('Please enter a search term', 'warning');
    }
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.initializeProductDetails = initializeProductDetails;
    window.loadProduct = loadProduct;
    window.renderProduct = renderProduct;
    window.handleAttributeChange = handleAttributeChange;
    window.updatePricing = updatePricing;
    window.changeMainImage = changeMainImage;
    window.changeQuantity = changeQuantity;
    window.setActiveTab = setActiveTab;
    window.renderTabContent = renderTabContent;
    window.loadRelatedProducts = loadRelatedProducts;
    window.addToCart = addToCart;
    window.addToWishlist = addToWishlist;
    window.buyNow = buyNow;
    window.shareProduct = shareProduct;
    window.quickAddToCart = quickAddToCart;
    window.performSearch = performSearch;
}