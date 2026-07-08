/**
 * Bootstrap-compatible Products Page JavaScript
 * Handles product loading, filtering, and display with Bootstrap 5.0
 */

// Product data
const PRODUCTS_DATA = [
    // Vegetables
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
        id: 3,
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
        id: 4,
        name: "Organic Broccoli",
        price: 3.29,
        description: "Fresh organic broccoli crowns, locally grown",
        image: "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?auto=format&fit=crop&w=300&q=80",
        category: "vegetables",
        brand: "Fresh Farm",
        rating: 4.5,
        reviews: 93,
        sale: false,
        featured: false,
        new: false,
        inStock: true,
        weight: "1 lb"
    },
    // Fruits
    {
        id: 5,
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
        id: 6,
        name: "Organic Dragon Fruit",
        price: 8.99,
        description: "Exotic organic dragon fruit, sweet and refreshing",
        image: "https://images.unsplash.com/photo-1553909489-cd47e0ef937f?auto=format&fit=crop&w=300&q=80",
        category: "fruits",
        brand: "Berry Fresh",
        rating: 4.2,
        reviews: 67,
        sale: false,
        featured: false,
        new: true,
        inStock: true,
        weight: "1 piece"
    },
    {
        id: 7,
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
    // Dairy
    {
        id: 8,
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
        id: 9,
        name: "Organic Coconut Milk",
        price: 4.99,
        description: "Rich organic coconut milk, perfect for cooking",
        image: "https://images.unsplash.com/photo-1563379091339-03246963d96a?auto=format&fit=crop&w=300&q=80",
        category: "dairy",
        brand: "Pure Greek",
        rating: 4.5,
        reviews: 76,
        sale: false,
        featured: false,
        new: true,
        inStock: true,
        weight: "32 oz"
    },
    // Seafood
    {
        id: 10,
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
    // Bakery
    {
        id: 11,
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
    },
    // More products...
    {
        id: 12,
        name: "Raw Organic Almonds",
        price: 8.99,
        originalPrice: 14.99,
        description: "Premium raw organic almonds, perfect for snacking",
        image: "https://images.unsplash.com/photo-1594736797933-d0701ba2fe65?auto=format&fit=crop&w=300&q=80",
        category: "pantry",
        brand: "Nutty Delight",
        rating: 4.4,
        reviews: 167,
        sale: true,
        featured: false,
        new: false,
        inStock: true,
        weight: "1 lb"
    },
    {
        id: 13,
        name: "Raw Wildflower Honey",
        price: 11.99,
        originalPrice: 15.99,
        description: "Pure raw wildflower honey from local beekeepers",
        image: "https://images.unsplash.com/photo-1559235038-1b0faec6a9e1?auto=format&fit=crop&w=300&q=80",
        category: "pantry",
        brand: "Bee Natural",
        rating: 4.7,
        reviews: 134,
        sale: true,
        featured: false,
        new: false,
        inStock: true,
        weight: "16 oz"
    },
    {
        id: 14,
        name: "Organic Quinoa",
        price: 12.99,
        description: "Premium organic quinoa, ancient grain superfood",
        image: "https://images.unsplash.com/photo-1571069177761-4239e39cf867?auto=format&fit=crop&w=300&q=80",
        category: "pantry",
        brand: "Grain Harvest",
        rating: 4.3,
        reviews: 89,
        sale: false,
        featured: false,
        new: false,
        inStock: true,
        weight: "2 lbs"
    },
    {
        id: 15,
        name: "Extra Virgin Olive Oil",
        price: 16.99,
        description: "Premium extra virgin olive oil from Mediterranean groves",
        image: "https://images.unsplash.com/photo-1587735243615-c03f25aaff15?auto=format&fit=crop&w=300&q=80",
        category: "pantry",
        brand: "Mediterranean",
        rating: 4.9,
        reviews: 298,
        sale: false,
        featured: true,
        new: false,
        inStock: true,
        weight: "500ml"
    }
];

// Current state
let currentFilters = {
    search: '',
    category: '',
    minPrice: 0,
    maxPrice: 50,
    brands: [],
    special: [],
    sortBy: 'newest'
};

let filteredProducts = [];
let currentView = 'grid';

// Initialize products page
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛒 Bootstrap Products Page initialized');
    
    // Parse URL parameters
    parseURLParameters();
    
    // Load and display products
    loadProducts();
    
    // Set up event listeners
    setupEventListeners();
});

// Parse URL parameters
function parseURLParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Set category filter from URL
    if (urlParams.get('category')) {
        currentFilters.category = urlParams.get('category');
        // Check the corresponding checkbox
        const categoryCheckbox = document.querySelector(`input[value="${currentFilters.category}"]`);
        if (categoryCheckbox) {
            categoryCheckbox.checked = true;
        }
    }
    
    // Set special filters from URL
    if (urlParams.get('filter') === 'new') {
        currentFilters.special.push('new');
        const newCheckbox = document.getElementById('new-arrivals');
        if (newCheckbox) newCheckbox.checked = true;
    }
    
    if (urlParams.get('filter') === 'featured') {
        currentFilters.special.push('featured');
        const featuredCheckbox = document.getElementById('featured-items');
        if (featuredCheckbox) featuredCheckbox.checked = true;
    }
    
    if (urlParams.get('filter') === 'sale') {
        currentFilters.special.push('sale');
        const saleCheckbox = document.getElementById('sale-items');
        if (saleCheckbox) saleCheckbox.checked = true;
    }
}

// Setup event listeners
function setupEventListeners() {
    // Search input with debounce
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                currentFilters.search = this.value.toLowerCase().trim();
                loadProducts();
            }, 300);
        });
    }
    
    // Price range slider
    const priceSlider = document.getElementById('price-slider');
    if (priceSlider) {
        priceSlider.addEventListener('input', function() {
            currentFilters.maxPrice = parseInt(this.value);
            document.getElementById('max-price-display').textContent = this.value;
            document.getElementById('current-max-price').textContent = this.value;
        });
        
        priceSlider.addEventListener('change', function() {
            loadProducts();
        });
    }
    
    // Price input fields
    const minPriceInput = document.getElementById('min-price-input');
    const maxPriceInput = document.getElementById('max-price-input');
    
    if (minPriceInput) {
        minPriceInput.addEventListener('change', function() {
            currentFilters.minPrice = parseInt(this.value) || 0;
            loadProducts();
        });
    }
    
    if (maxPriceInput) {
        maxPriceInput.addEventListener('change', function() {
            currentFilters.maxPrice = parseInt(this.value) || 50;
            if (priceSlider) priceSlider.value = currentFilters.maxPrice;
            document.getElementById('max-price-display').textContent = currentFilters.maxPrice;
            document.getElementById('current-max-price').textContent = currentFilters.maxPrice;
            loadProducts();
        });
    }
}

// Apply filters function (called by checkboxes)
function applyFilters() {
    // Get category filters
    const categoryInputs = document.querySelectorAll('input[name="category"]:checked');
    currentFilters.category = categoryInputs.length > 0 ? categoryInputs[0].value : '';
    
    // Get brand filters
    const brandInputs = document.querySelectorAll('input[name="brand"]:checked');
    currentFilters.brands = Array.from(brandInputs).map(input => input.value);
    
    // Get special filters
    const specialInputs = document.querySelectorAll('input[name="special"]:checked');
    currentFilters.special = Array.from(specialInputs).map(input => input.value);
    
    loadProducts();
}

// Update price range
function updatePriceRange() {
    const priceSlider = document.getElementById('price-slider');
    const maxPriceDisplay = document.getElementById('max-price-display');
    const currentMaxPrice = document.getElementById('current-max-price');
    
    if (priceSlider && maxPriceDisplay && currentMaxPrice) {
        const value = priceSlider.value;
        maxPriceDisplay.textContent = value;
        currentMaxPrice.textContent = value;
        currentFilters.maxPrice = parseInt(value);
    }
}

// Sort products
function sortProducts() {
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        currentFilters.sortBy = sortSelect.value;
        loadProducts();
    }
}

// Toggle view
function toggleView(view) {
    currentView = view;
    
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    
    if (gridBtn && listBtn) {
        if (view === 'grid') {
            gridBtn.className = 'btn btn-success';
            listBtn.className = 'btn btn-outline-secondary';
        } else {
            gridBtn.className = 'btn btn-outline-secondary';
            listBtn.className = 'btn btn-success';
        }
    }
    
    renderProducts();
}

// Load products
function loadProducts() {
    console.log('Loading products with filters:', currentFilters);
    
    // Show loading state
    showLoadingState();
    
    // Simulate loading delay
    setTimeout(() => {
        // Filter products
        filteredProducts = filterProducts(PRODUCTS_DATA);
        
        // Sort products
        filteredProducts = sortProductsArray(filteredProducts);
        
        console.log('Filtered products:', filteredProducts);
        
        // Update counts
        updateProductCounts();
        
        // Render products
        renderProducts();
        
        // Hide loading state
        hideLoadingState();
        
    }, 300);
}

// Filter products
function filterProducts(products) {
    let filtered = [...products];
    
    // Search filter
    if (currentFilters.search) {
        filtered = filtered.filter(product => 
            product.name.toLowerCase().includes(currentFilters.search) ||
            product.description.toLowerCase().includes(currentFilters.search) ||
            product.brand.toLowerCase().includes(currentFilters.search)
        );
    }
    
    // Category filter
    if (currentFilters.category) {
        filtered = filtered.filter(product => product.category === currentFilters.category);
    }
    
    // Price range filter
    filtered = filtered.filter(product => 
        product.price >= currentFilters.minPrice && 
        product.price <= currentFilters.maxPrice
    );
    
    // Brand filter
    if (currentFilters.brands.length > 0) {
        filtered = filtered.filter(product => 
            currentFilters.brands.includes(product.brand)
        );
    }
    
    // Special filters
    if (currentFilters.special.includes('sale')) {
        filtered = filtered.filter(product => product.sale);
    }
    
    if (currentFilters.special.includes('new')) {
        filtered = filtered.filter(product => product.new);
    }
    
    if (currentFilters.special.includes('featured')) {
        filtered = filtered.filter(product => product.featured);
    }
    
    return filtered;
}

// Sort products array
function sortProductsArray(products) {
    const sorted = [...products];
    
    switch (currentFilters.sortBy) {
        case 'price-low':
            return sorted.sort((a, b) => a.price - b.price);
        case 'price-high':
            return sorted.sort((a, b) => b.price - a.price);
        case 'name':
            return sorted.sort((a, b) => a.name.localeCompare(b.name));
        case 'rating':
            return sorted.sort((a, b) => b.rating - a.rating);
        case 'sale':
            return sorted.sort((a, b) => (b.sale ? 1 : 0) - (a.sale ? 1 : 0));
        case 'popular':
            return sorted.sort((a, b) => b.reviews - a.reviews);
        case 'newest':
        default:
            return sorted.sort((a, b) => (b.new ? 1 : 0) - (a.new ? 1 : 0));
    }
}

// Update product counts
function updateProductCounts() {
    const productsCountElement = document.getElementById('products-count');
    const filteredCountElement = document.getElementById('filtered-count');
    
    if (productsCountElement) {
        productsCountElement.textContent = `${PRODUCTS_DATA.length} products`;
    }
    
    if (filteredCountElement) {
        filteredCountElement.textContent = filteredProducts.length;
    }
}

// Show loading state
function showLoadingState() {
    const productsGrid = document.getElementById('products-grid');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    
    if (productsGrid) productsGrid.innerHTML = '';
    if (loadingState) loadingState.classList.remove('d-none');
    if (emptyState) emptyState.classList.add('d-none');
}

// Hide loading state
function hideLoadingState() {
    const loadingState = document.getElementById('loading-state');
    if (loadingState) loadingState.classList.add('d-none');
}

// Render products
function renderProducts() {
    const productsGrid = document.getElementById('products-grid');
    const emptyState = document.getElementById('empty-state');
    
    if (!productsGrid) {
        console.error('Products grid container not found');
        return;
    }
    
    if (filteredProducts.length === 0) {
        productsGrid.innerHTML = '';
        if (emptyState) emptyState.classList.remove('d-none');
        return;
    }
    
    if (emptyState) emptyState.classList.add('d-none');
    
    if (currentView === 'grid') {
        productsGrid.className = 'row g-4';
        productsGrid.innerHTML = filteredProducts.map(product => createProductCard(product)).join('');
    } else {
        productsGrid.className = 'row g-4';
        productsGrid.innerHTML = filteredProducts.map(product => createProductListItem(product)).join('');
    }
}

// Create product card
function createProductCard(product) {
    const badge = product.sale ? '<div class="product-badge badge-sale">Sale</div>' :
                 product.new ? '<div class="product-badge badge-new">New</div>' :
                 product.featured ? '<div class="product-badge badge-organic">Featured</div>' : '';
    
    const originalPrice = product.originalPrice ? 
        `<small class="text-muted text-decoration-line-through ms-1">${product.originalPrice.toFixed(2)}</small>` : '';
    
    const stars = '★'.repeat(Math.floor(product.rating)) + '☆'.repeat(5 - Math.floor(product.rating));
    
    return `
        <div class="col-6 col-md-4 col-lg-3">
            <div class="card h-100 enhanced-product-card position-relative">
                <div class="product-image-container position-relative">
                    <img src="${product.image}" alt="${product.name}" class="card-img-top" style="height: 200px; object-fit: cover;">
                    ${badge}
                    
                    <!-- Quick View Button - Hidden by default, shown on hover -->
                    <button class="quick-view-btn" onclick="quickViewProduct(${product.id})" title="Quick View">
                        <i class="bi bi-eye"></i>
                    </button>
                    
                    <!-- Wishlist Button - Hidden by default, shown on hover -->
                    <button class="wishlist-btn" onclick="toggleWishlist(${product.id})" title="Add to Wishlist">
                        <i class="bi bi-heart"></i>
                    </button>
                </div>
                
                <div class="card-body">
                    <h6 class="card-title fw-semibold text-dark mb-1">${product.name}</h6>
                    
                    <!-- Star Rating - Only shown in All Products section -->
                    <div class="product-rating d-flex align-items-center gap-1 mb-2" data-section="all-products">
                        <div class="d-flex">${stars}</div>
                        <span class="rating-text">(${product.rating})</span>
                    </div>
                    
                    <p class="text-muted small mb-2">${product.brand} • ${product.weight}</p>
                    
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <span class="h6 text-success fw-bold">${product.price.toFixed(2)}</span>
                            ${originalPrice}
                        </div>
                        <button class="btn product-add-btn d-flex align-items-center" onclick="addToCart(${product.id})">
                            <i class="bi bi-cart-plus"></i>
                            <span class="btn-text">Add</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Create product list item
function createProductListItem(product) {
    const badge = product.sale ? '<span class="badge bg-danger me-2">Sale</span>' :
                 product.new ? '<span class="badge bg-primary me-2">New</span>' :
                 product.featured ? '<span class="badge bg-success me-2">Featured</span>' : '';
    
    const originalPrice = product.originalPrice ? 
        `<small class="text-muted text-decoration-line-through ms-2">$${product.originalPrice.toFixed(2)}</small>` : '';
    
    const stars = '★'.repeat(Math.floor(product.rating)) + '☆'.repeat(5 - Math.floor(product.rating));
    
    return `
        <div class="col-12">
            <div class="organic-card p-4">
                <div class="row align-items-center">
                    <div class="col-md-3">
                        <img src="${product.image}" alt="${product.name}" class="w-100 rounded" style="height: 150px; object-fit: cover;">
                    </div>
                    <div class="col-md-6">
                        <div class="mt-3 mt-md-0">
                            <h5 class="fw-bold text-dark mb-2">
                                ${badge}${product.name}
                            </h5>
                            <p class="text-muted mb-2">${product.description}</p>
                            <div class="d-flex align-items-center gap-3 mb-2">
                                <div class="rating">
                                    <span class="text-warning">${stars}</span>
                                    <span class="small text-muted ms-1">(${product.rating})</span>
                                </div>
                                <span class="small text-muted">${product.reviews} reviews</span>
                                <span class="small text-muted">${product.brand}</span>
                            </div>
                            <span class="small text-muted">${product.weight}</span>
                        </div>
                    </div>
                    <div class="col-md-3 text-md-end">
                        <div class="mt-3 mt-md-0">
                            <div class="mb-3">
                                <span class="h4 text-success fw-bold">$${product.price.toFixed(2)}</span>
                                ${originalPrice}
                            </div>
                            <div class="d-flex flex-column gap-2">
                                <button class="btn btn-success" onclick="addToCart(${product.id})">
                                    <i class="bi bi-cart-plus me-2"></i>
                                    Add to Cart
                                </button>
                                <button class="btn btn-outline-secondary btn-sm" onclick="viewProduct(${product.id})">
                                    <i class="bi bi-eye me-2"></i>
                                    Quick View
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Clear all filters
function clearAllFilters() {
    currentFilters = {
        search: '',
        category: '',
        minPrice: 0,
        maxPrice: 50,
        brands: [],
        special: [],
        sortBy: 'newest'
    };
    
    // Clear form inputs
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    
    // Clear checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = false;
    });
    
    // Reset price slider
    const priceSlider = document.getElementById('price-slider');
    const minPriceInput = document.getElementById('min-price-input');
    const maxPriceInput = document.getElementById('max-price-input');
    
    if (priceSlider) {
        priceSlider.value = 50;
        updatePriceRange();
    }
    if (minPriceInput) minPriceInput.value = 0;
    if (maxPriceInput) maxPriceInput.value = 50;
    
    // Reset sort
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) sortSelect.value = 'newest';
    
    loadProducts();
}

// Load more products (for pagination)
function loadMoreProducts() {
    // For now, just scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// View product function
function viewProduct(productId) {
    window.location.href = `product-details.html?id=${productId}`;
}

// Add to cart function
function addToCart(productId) {
    console.log('Adding product to cart:', productId);
    
    // Find the product
    const product = PRODUCTS_DATA.find(p => p.id === productId);
    if (!product) {
        console.error('Product not found:', productId);
        return;
    }
    
    // Show success toast
    const toast = document.createElement('div');
    toast.className = 'toast position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast-body bg-success text-white fw-medium rounded d-flex align-items-center gap-2">
            <i class="bi bi-check-circle"></i>
            ${product.name} added to cart!
        </div>
    `;
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
    
    // Trigger cart popup if available
    if (typeof window.ajaxCart !== 'undefined' && window.ajaxCart.show) {
        window.ajaxCart.addToCart({
            id: product.id,
            name: product.name,
            price: product.price,
            image: product.image,
            description: `${product.brand} • ${product.weight}`
        });
    }
}

// Toggle wishlist function
function toggleWishlist(productId) {
    console.log('Toggling wishlist for product:', productId);
    
    // Find the product
    const product = PRODUCTS_DATA.find(p => p.id === productId);
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
            showWishlistToast(`${product.name} removed from wishlist!`, 'info');
        } else {
            // Add to wishlist
            btn.classList.add('active');
            if (icon) icon.className = 'bi bi-heart-fill';
            showWishlistToast(`${product.name} added to wishlist!`, 'success');
        }
    });
}

// Wishlist toast function
function showWishlistToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = 'toast position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '9999';
    
    const bgClass = type === 'success' ? 'bg-success' : 'bg-info';
    const iconClass = type === 'success' ? 'bi-heart-fill' : 'bi-heart';
    
    toast.innerHTML = `
        <div class="toast-body ${bgClass} text-white fw-medium rounded d-flex align-items-center gap-2">
            <i class="bi ${iconClass}"></i>
            ${message}
        </div>
    `;
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}

// Search function for header search
function performSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        currentFilters.search = searchInput.value.toLowerCase().trim();
        loadProducts();
    }
}

// Mobile filter toggle
function toggleMobileFilters() {
    const sidebar = document.getElementById('filters-sidebar');
    if (sidebar) {
        sidebar.classList.toggle('d-block');
        sidebar.classList.toggle('d-md-block');
    }
}

// Export functions for global access
window.applyFilters = applyFilters;
window.updatePriceRange = updatePriceRange;
window.sortProducts = sortProducts;
window.toggleView = toggleView;
window.clearAllFilters = clearAllFilters;
window.loadMoreProducts = loadMoreProducts;
window.performSearch = performSearch;
window.toggleMobileFilters = toggleMobileFilters;
window.addToCart = addToCart;
window.viewProduct = viewProduct;