// Reusable component templates - Enhanced with working quick view

// Enhanced Create product card HTML - matching products page design
function createProductCard(product) {
    const salePrice = product.originalPrice ? product.price : null;
    const originalPrice = product.originalPrice;
    
    return `
        <div class="enhanced-product-card group bg-white border border-gray-200 rounded-2xl overflow-hidden transition-all duration-400 hover:shadow-xl hover:-translate-y-2 relative">
            <div class="relative overflow-hidden rounded-t-2xl">
                <img src="${product.image}" alt="${product.name}" class="w-full h-56 object-cover group-hover:scale-110 transition-transform duration-500">
                
                ${product.sale ? '<div class="absolute top-4 left-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">🔥 SALE</div>' : ''}
                ${product.isNew ? '<div class="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">✨ NEW</div>' : ''}
                
                <!-- Enhanced Action Buttons Overlay -->
                <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end justify-center pb-6">
                    <div class="flex gap-3">
                        <button onclick="toggleWishlist(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-red-500 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Add to Wishlist">
                            <i data-lucide="heart" class="h-5 w-5"></i>
                        </button>
                        <button onclick="event.stopPropagation(); quickViewProduct(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-green-600 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Quick View">
                            <i data-lucide="eye" class="h-5 w-5"></i>
                        </button>
                        <button onclick="navigateToProduct(${product.id})" class="bg-green-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-green-700 transition-all shadow-lg">
                            View Details
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="p-6 space-y-4">
                <div>
                    <h3 class="text-xl font-bold text-gray-900 group-hover:text-green-600 transition-colors line-clamp-2">${product.name}</h3>
                    <p class="text-gray-600 text-sm mt-1">Farm fresh • Pesticide free</p>
                </div>
                
                <div class="flex items-center gap-2">
                    <div class="flex text-yellow-400 text-lg">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="text-gray-600 font-medium">(${product.rating})</span>
                    <span class="text-gray-400 text-sm">${Math.floor(Math.random() * 50) + 20} reviews</span>
                </div>
                
                <div class="flex items-center justify-between">
                    <div class="space-y-1">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                            ${originalPrice ? `<span class="text-lg text-gray-500 line-through">$${originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${originalPrice ? `<span class="text-sm text-red-600 font-semibold">Save $${(originalPrice - product.price).toFixed(2)} (${Math.round(((originalPrice - product.price) / originalPrice) * 100)}% off)</span>` : '<span class="text-sm text-green-600 font-semibold">Premium quality</span>'}
                    </div>
                    <button onclick="addToCart(${product.id})" class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:shadow-lg flex items-center gap-2">
                        <i data-lucide="shopping-cart" class="h-4 w-4"></i>
                        ADD
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Navigate to product details
function navigateToProduct(productId) {
    window.location.href = `product-details.html?id=${productId}`;
}

// Toggle wishlist
function toggleWishlist(productId) {
    const product = getProductById(productId);
    if (!product) return;
    
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    const existingIndex = wishlist.findIndex(item => item.id === productId);
    
    if (existingIndex > -1) {
        // Remove from wishlist
        wishlist.splice(existingIndex, 1);
        showNotification(`${product.name} removed from wishlist`, 'info');
    } else {
        // Add to wishlist
        wishlist.push(product);
        showNotification(`${product.name} added to wishlist`, 'success');
    }
    
    localStorage.setItem('wishlist', JSON.stringify(wishlist));
    updateWishlistDisplay();
}

// ENHANCED QUICK VIEW FUNCTIONALITY - FIXED VERSION
function quickViewProduct(productId) {
    console.log('🔍 Quick View triggered for product ID:', productId);
    
    // Get product data from multiple sources
    let product = getProductFromAnySources(productId);
    
    if (!product) {
        console.error('❌ Product not found:', productId);
        showNotification('Product not found', 'error');
        return;
    }
    
    console.log('✅ Product found:', product.name);
    
    // Create or get modal
    let modal = document.getElementById('quick-view-modal');
    if (!modal) {
        createQuickViewModal();
        modal = document.getElementById('quick-view-modal');
    }
    
    const content = document.getElementById('quick-view-content');
    if (!content) return;
    
    // Calculate savings
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    const salePercentage = savings > 0 ? Math.round((savings / product.originalPrice) * 100) : 0;
    
    // Render enhanced modal content
    content.innerHTML = `
        <div class="relative bg-white rounded-3xl overflow-hidden">
            <!-- Close button -->
            <button onclick="closeQuickView()" class="absolute top-6 right-6 z-20 p-3 text-gray-400 hover:text-gray-600 bg-white/90 backdrop-blur-sm rounded-full shadow-lg hover:shadow-xl transition-all">
                <i data-lucide="x" class="h-6 w-6"></i>
            </button>
            
            <!-- Header -->
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 px-8 py-6 border-b border-green-100">
                <div class="flex items-center gap-4">
                    <div class="bg-green-100 p-3 rounded-2xl">
                        <i data-lucide="eye" class="h-6 w-6 text-green-600"></i>
                    </div>
                    <div>
                        <h2 class="text-2xl font-bold text-gray-800">Quick View</h2>
                        <p class="text-green-600">Premium organic product preview</p>
                    </div>
                </div>
            </div>
            
            <!-- Content -->
            <div class="p-8">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
                    <!-- Product Image Section -->
                    <div class="space-y-6">
                        <div class="relative rounded-2xl overflow-hidden bg-gray-50 aspect-square">
                            <img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover hover:scale-105 transition-transform duration-500">
                            
                            <!-- Badges -->
                            <div class="absolute top-4 left-4 flex flex-col gap-2">
                                ${product.sale && salePercentage > 0 ? `<div class="bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 rounded-xl font-bold text-sm shadow-lg">-${salePercentage}% OFF</div>` : ''}
                                ${product.isNew ? `<div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-xl font-bold text-sm shadow-lg">NEW</div>` : ''}
                            </div>
                            
                            <div class="absolute bottom-4 left-4 bg-green-500 text-white px-4 py-2 rounded-xl font-bold text-sm shadow-lg">
                                <i data-lucide="leaf" class="h-4 w-4 mr-1 inline"></i>
                                100% ORGANIC
                            </div>
                        </div>
                        
                        <!-- Trust Indicators -->
                        <div class="grid grid-cols-2 gap-4">
                            <div class="bg-gradient-to-br from-green-50 to-emerald-50 p-4 rounded-xl border border-green-100">
                                <div class="flex items-center gap-2 text-green-600 mb-2">
                                    <i data-lucide="truck" class="h-5 w-5"></i>
                                    <span class="font-bold">Free Delivery</span>
                                </div>
                                <p class="text-xs text-gray-600">On orders over $50</p>
                            </div>
                            <div class="bg-gradient-to-br from-blue-50 to-sky-50 p-4 rounded-xl border border-blue-100">
                                <div class="flex items-center gap-2 text-blue-600 mb-2">
                                    <i data-lucide="shield-check" class="h-5 w-5"></i>
                                    <span class="font-bold">Certified</span>
                                </div>
                                <p class="text-xs text-gray-600">USDA Organic</p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Product Info Section -->
                    <div class="space-y-6">
                        <!-- Product Header -->
                        <div>
                            <div class="flex items-center gap-3 mb-3">
                                <span class="bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 px-4 py-2 rounded-xl font-bold capitalize border border-green-200">${product.category}</span>
                                <span class="text-gray-400">•</span>
                                <span class="text-gray-600 font-medium">${product.brand || 'Fresh Farm'}</span>
                            </div>
                            <h3 class="text-3xl font-bold text-gray-900 leading-tight mb-4">${product.name}</h3>
                            <p class="text-gray-600 leading-relaxed text-lg">${product.description}</p>
                        </div>
                        
                        <!-- Rating -->
                        <div class="bg-amber-50 border border-amber-200 rounded-xl p-6">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center gap-4">
                                    <div class="text-3xl font-bold text-amber-600">${product.rating}</div>
                                    <div>
                                        <div class="flex text-yellow-400 text-lg mb-1">
                                            ${Array(5).fill().map((_, i) => 
                                                `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                            ).join('')}
                                        </div>
                                        <p class="text-gray-600 font-medium">${Math.floor(Math.random() * 50) + 20} reviews</p>
                                    </div>
                                </div>
                                <span class="flex items-center gap-2 text-green-600 font-bold">
                                    <div class="w-3 h-3 bg-green-500 rounded-full"></div>
                                    In Stock
                                </span>
                            </div>
                        </div>
                        
                        <!-- Price Section -->
                        <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-8">
                            <div class="text-center">
                                <div class="flex items-center justify-center gap-4 mb-4">
                                    <span class="text-4xl lg:text-5xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                                    ${product.originalPrice && product.originalPrice > product.price ? `<span class="text-2xl text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                                </div>
                                ${savings > 0 ? `
                                    <div class="flex items-center justify-center gap-3 mb-4">
                                        <span class="bg-red-500 text-white px-4 py-2 rounded-xl font-bold">Save $${savings.toFixed(2)}</span>
                                        <span class="text-green-700 font-bold text-xl">${salePercentage}% off</span>
                                    </div>
                                ` : '<div class="text-green-700 font-bold text-lg mb-4">🌟 Premium Quality Guaranteed</div>'}
                            </div>
                        </div>
                        
                        <!-- Quantity Selector -->
                        <div class="flex items-center gap-4">
                            <span class="text-gray-700 font-semibold">Quantity:</span>
                            <div class="flex items-center border-2 border-gray-200 rounded-xl overflow-hidden">
                                <button onclick="quickViewDecreaseQuantity()" class="px-4 py-3 hover:bg-gray-50 transition-colors">
                                    <i data-lucide="minus" class="h-4 w-4"></i>
                                </button>
                                <span id="quick-view-quantity" class="px-6 py-3 font-bold text-lg min-w-[4rem] text-center">1</span>
                                <button onclick="quickViewIncreaseQuantity()" class="px-4 py-3 hover:bg-gray-50 transition-colors">
                                    <i data-lucide="plus" class="h-4 w-4"></i>
                                </button>
                            </div>
                        </div>
                        
                        <!-- Action Buttons -->
                        <div class="space-y-4">
                            <div class="flex gap-4">
                                <button onclick="quickViewAddToCart(${product.id}); closeQuickView();" class="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3">
                                    <i data-lucide="shopping-cart" class="h-6 w-6"></i>
                                    Add to Cart
                                </button>
                                <button onclick="toggleWishlist(${product.id})" class="p-4 border-2 border-gray-300 rounded-2xl hover:border-red-500 hover:bg-red-50 transition-all">
                                    <i data-lucide="heart" class="h-6 w-6 text-gray-600 hover:text-red-500"></i>
                                </button>
                            </div>
                            
                            <button onclick="window.location.href='product-details.html?id=${product.id}'" class="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-8 py-4 rounded-2xl font-bold transition-all">
                                View Complete Details
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Show modal
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Re-initialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

// Create quick view modal if it doesn't exist
function createQuickViewModal() {
    const modal = document.createElement('div');
    modal.id = 'quick-view-modal';
    modal.className = 'fixed inset-0 quick-view-backdrop hidden flex items-center justify-center p-4 z-50';
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeQuickView();
        }
    };
    
    const content = document.createElement('div');
    content.id = 'quick-view-content';
    content.className = 'quick-view-modal rounded-3xl max-w-6xl w-full max-h-[90vh] overflow-y-auto modal-animate-in';
    content.onclick = (e) => e.stopPropagation();
    
    modal.appendChild(content);
    document.body.appendChild(modal);
}

// Get product from any available source
function getProductFromAnySources(productId) {
    const id = parseInt(productId);
    
    // Try getAllProducts function
    if (typeof getAllProducts === 'function') {
        const products = getAllProducts();
        const product = products.find(p => p.id === id);
        if (product) return product;
    }
    
    // Try global products array
    if (typeof window.products !== 'undefined') {
        const product = window.products.find(p => p.id === id);
        if (product) return product;
    }
    
    // Try enhancedProducts if available
    if (typeof window.enhancedProducts !== 'undefined') {
        const product = window.enhancedProducts.find(p => p.id === id);
        if (product) return product;
    }
    
    // Fallback to mock data for demo
    const mockProducts = [
        {
            id: 1,
            name: "Organic Roma Tomatoes",
            price: 2.99,
            originalPrice: 4.99,
            rating: 4.8,
            description: "Fresh, vine-ripened organic tomatoes bursting with flavor. Perfect for salads, cooking, or eating fresh.",
            image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=600&h=600&fit=crop",
            category: "vegetables",
            brand: "Fresh Farm",
            sale: true,
            isNew: false
        },
        {
            id: 2,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            rating: 4.8,
            description: "Sweet and crispy organic apples, perfect for snacking or baking. Grown without pesticides.",
            image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=600&h=600&fit=crop",
            category: "fruits",
            brand: "Orchard Fresh",
            sale: false,
            isNew: true
        },
        {
            id: 3,
            name: "Organic Baby Spinach",
            price: 3.49,
            rating: 4.7,
            description: "Fresh organic baby spinach leaves, perfect for salads and smoothies. Rich in nutrients.",
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&h=600&fit=crop",
            category: "vegetables",
            brand: "Green Leaf",
            sale: false,
            isNew: false
        }
    ];
    
    return mockProducts.find(p => p.id === id) || mockProducts[0];
}

// Quick view quantity controls
let quickViewQuantity = 1;

function quickViewIncreaseQuantity() {
    quickViewQuantity++;
    document.getElementById('quick-view-quantity').textContent = quickViewQuantity;
}

function quickViewDecreaseQuantity() {
    if (quickViewQuantity > 1) {
        quickViewQuantity--;
        document.getElementById('quick-view-quantity').textContent = quickViewQuantity;
    }
}

function quickViewAddToCart(productId) {
    // Add multiple items based on quantity
    for (let i = 0; i < quickViewQuantity; i++) {
        if (typeof addToCart === 'function') {
            addToCart(productId);
        }
    }
    
    // Show notification
    const product = getProductFromAnySources(productId);
    if (typeof showNotification === 'function') {
        showNotification(`Added ${quickViewQuantity} x ${product.name} to cart!`, 'success');
    } else {
        alert(`Added ${quickViewQuantity} x ${product.name} to cart!`);
    }
    
    // Reset quantity
    quickViewQuantity = 1;
}

// Close quick view modal
function closeQuickView() {
    const modal = document.getElementById('quick-view-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
    
    // Reset quantity
    quickViewQuantity = 1;
}

// Enhanced mega menu functionality with modern design
function showMegaMenu() {
    const megaMenu = document.getElementById('mega-menu');
    if (!megaMenu) return;
    
    const categories = getCategories();
    const featuredProducts = getFeaturedProducts();
    
    megaMenu.innerHTML = `
        <div class="bg-white border border-gray-100 rounded-3xl shadow-2xl overflow-hidden">
            <div class="bg-gradient-to-r from-green-50 via-blue-50 to-purple-50 px-8 py-6 border-b border-gray-100">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-2xl font-bold text-gray-800 mb-1">Explore Categories</h3>
                        <p class="text-gray-600">Discover our premium organic collection</p>
                    </div>
                    <div class="text-4xl opacity-50">🌱</div>
                </div>
            </div>
            
            <div class="p-8">
                <div class="grid grid-cols-12 gap-8">
                    <!-- Categories Grid -->
                    <div class="col-span-8">
                        <div class="grid grid-cols-3 gap-4">
                            ${categories.map(category => `
                                <a href="products.html?category=${category.id}" 
                                   class="group relative bg-gradient-to-br from-white to-gray-50 rounded-2xl p-6 border border-gray-100 hover:border-green-200 transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                                    
                                    <!-- Category Icon Background -->
                                    <div class="absolute top-4 right-4 text-3xl opacity-20 group-hover:opacity-40 transition-opacity">
                                        ${category.icon}
                                    </div>
                                    
                                    <!-- Category Content -->
                                    <div class="relative z-10">
                                        <div class="flex items-center gap-3 mb-3">
                                            <div class="bg-green-100 group-hover:bg-green-200 rounded-xl p-2 transition-colors">
                                                <span class="text-lg">${category.icon}</span>
                                            </div>
                                            <div>
                                                <h4 class="font-semibold text-gray-800 group-hover:text-green-600 transition-colors">
                                                    ${category.name}
                                                </h4>
                                                <p class="text-xs text-gray-500">
                                                    ${getCategoryProductCount(category.id)} products
                                                </p>
                                            </div>
                                        </div>
                                        
                                        <p class="text-sm text-gray-600 group-hover:text-gray-700 transition-colors">
                                            ${category.description}
                                        </p>
                                        
                                        <!-- Hover Arrow -->
                                        <div class="flex items-center justify-end mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <span class="text-green-600 text-sm font-medium">Explore</span>
                                            <i data-lucide="arrow-right" class="h-4 w-4 text-green-600 ml-1"></i>
                                        </div>
                                    </div>
                                    
                                    <!-- Gradient Overlay -->
                                    <div class="absolute inset-0 bg-gradient-to-br from-green-500/0 to-blue-500/0 group-hover:from-green-500/5 group-hover:to-blue-500/5 rounded-2xl transition-all duration-300"></div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Featured Products Sidebar -->
                    <div class="col-span-4">
                        <div class="bg-gradient-to-b from-green-50 to-green-100 rounded-2xl p-6 border border-green-200">
                            <div class="flex items-center gap-2 mb-6">
                                <div class="bg-green-200 rounded-lg p-2">
                                    <span class="text-lg">⭐</span>
                                </div>
                                <div>
                                    <h4 class="font-bold text-gray-800">Featured Products</h4>
                                    <p class="text-sm text-green-700">Handpicked for you</p>
                                </div>
                            </div>
                            
                            <div class="space-y-4">
                                ${featuredProducts.slice(0, 4).map(product => `
                                    <a href="product-details.html?id=${product.id}" class="group block">
                                        <div class="bg-white rounded-xl p-4 hover:shadow-md transition-all duration-300 border border-green-100 hover:border-green-200">
                                            <div class="flex gap-3">
                                                <div class="relative">
                                                    <img src="${product.image}" alt="${product.name}" 
                                                         class="w-16 h-16 object-cover rounded-lg group-hover:scale-105 transition-transform">
                                                    ${product.sale ? '<div class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full text-xs w-4 h-4 flex items-center justify-center">%</div>' : ''}
                                                </div>
                                                <div class="flex-1 min-w-0">
                                                    <h5 class="font-medium text-gray-800 group-hover:text-green-600 transition-colors text-sm line-clamp-2">
                                                        ${product.name}
                                                    </h5>
                                                    <div class="flex items-center gap-2 mt-1">
                                                        <span class="text-green-600 font-bold text-sm">$${product.price.toFixed(2)}</span>
                                                        ${product.originalPrice ? `<span class="text-xs text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                                                    </div>
                                                    <div class="flex items-center gap-1 mt-1">
                                                        <div class="flex text-yellow-400 text-xs">
                                                            ${Array(5).fill().map((_, i) => 
                                                                `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                                            ).join('')}
                                                        </div>
                                                        <span class="text-xs text-gray-500">(${product.rating})</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </a>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    megaMenu.classList.remove('hidden');
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function hideMegaMenu() {
    const megaMenu = document.getElementById('mega-menu');
    if (megaMenu) {
        megaMenu.classList.add('hidden');
    }
}

// Get categories
function getCategories() {
    return [
        { id: 'vegetables', name: 'Vegetables', icon: '🥬', description: 'Fresh organic vegetables' },
        { id: 'fruits', name: 'Fruits', icon: '🍎', description: 'Sweet organic fruits' },
        { id: 'dairy', name: 'Dairy', icon: '🥛', description: 'Fresh dairy products' },
        { id: 'bakery', name: 'Bakery', icon: '🍞', description: 'Artisan baked goods' },
        { id: 'seafood', name: 'Seafood', icon: '🐟', description: 'Fresh caught seafood' },
        { id: 'pantry', name: 'Pantry', icon: '🌾', description: 'Pantry essentials' }
    ];
}

// Get category product count
function getCategoryProductCount(categoryId) {
    if (typeof getAllProducts === 'function') {
        return getAllProducts().filter(product => product.category === categoryId).length;
    }
    return Math.floor(Math.random() * 20) + 5; // Mock count
}

// Get featured products
function getFeaturedProducts() {
    if (typeof getAllProducts === 'function') {
        return getAllProducts().filter(product => product.rating >= 4.5).slice(0, 6);
    }
    
    // Mock featured products
    return [
        {
            id: 1,
            name: "Organic Roma Tomatoes",
            price: 2.99,
            originalPrice: 4.99,
            rating: 4.8,
            image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=150&h=150&fit=crop",
            sale: true
        },
        {
            id: 2,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            rating: 4.8,
            image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=150&h=150&fit=crop"
        },
        {
            id: 3,
            name: "Organic Baby Spinach",
            price: 3.49,
            rating: 4.7,
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=150&h=150&fit=crop"
        }
    ];
}

// Update wishlist display
function updateWishlistDisplay() {
    const wishlistCount = document.getElementById('wishlist-count');
    if (wishlistCount) {
        const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
        if (wishlist.length > 0) {
            wishlistCount.textContent = wishlist.length;
            wishlistCount.classList.remove('hidden');
        } else {
            wishlistCount.classList.add('hidden');
        }
    }
}

// Get product by ID
function getProductById(id) {
    return getProductFromAnySources(id);
}

// Enhanced Cart Dropdown functionality
function showCartDropdown() {
    const cartPopup = document.getElementById('cart-dropdown');
    if (!cartPopup) return;
    
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    
    if (cart.length === 0) {
        cartPopup.innerHTML = `
            <div class="p-8 text-center">
                <div class="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i data-lucide="shopping-cart" class="h-8 w-8 text-gray-400"></i>
                </div>
                <h3 class="font-semibold text-gray-900 mb-2">Your cart is empty</h3>
                <p class="text-gray-600 text-sm mb-4">Add some delicious organic products to get started!</p>
                <a href="products.html" class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold transition-colors inline-block">
                    Start Shopping
                </a>
            </div>
        `;
    } else {
        const cartItems = cart.slice(0, 3); // Show only first 3 items
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        const totalPrice = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        
        cartPopup.innerHTML = `
            <div class="p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="font-semibold text-gray-900">Shopping Cart</h3>
                    <span class="text-sm text-gray-600">${totalItems} items</span>
                </div>
                
                <div class="space-y-4 mb-4">
                    ${cartItems.map(item => {
                        const product = getProductById(item.id);
                        return `
                            <div class="flex items-center gap-3">
                                <img src="${product?.image || 'https://via.placeholder.com/50x50'}" alt="${product?.name || 'Product'}" class="w-12 h-12 object-cover rounded-lg">
                                <div class="flex-1 min-w-0">
                                    <h4 class="font-medium text-gray-900 text-sm truncate">${product?.name || 'Product'}</h4>
                                    <div class="flex items-center gap-2 text-xs text-gray-600">
                                        <span>Qty: ${item.quantity}</span>
                                        <span>•</span>
                                        <span class="font-medium text-green-600">$${(item.price * item.quantity).toFixed(2)}</span>
                                    </div>
                                </div>
                                <button onclick="removeFromCart(${item.id})" class="text-red-500 hover:text-red-700 p-1">
                                    <i data-lucide="trash-2" class="h-4 w-4"></i>
                                </button>
                            </div>
                        `;
                    }).join('')}
                    
                    ${cart.length > 3 ? `
                        <div class="text-center text-sm text-gray-500 py-2 border-t border-gray-100">
                            ... and ${cart.length - 3} more items
                        </div>
                    ` : ''}
                </div>
                
                <div class="border-t border-gray-100 pt-4">
                    <div class="flex items-center justify-between mb-4">
                        <span class="font-semibold text-gray-900">Total:</span>
                        <span class="text-xl font-bold text-green-600">$${totalPrice.toFixed(2)}</span>
                    </div>
                    
                    <div class="flex gap-2">
                        <a href="cart.html" class="flex-1 bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition-colors text-center">
                            View Cart
                        </a>
                        <a href="checkout.html" class="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors text-center">
                            Checkout
                        </a>
                    </div>
                </div>
            </div>
        `;
    }
    
    cartPopup.classList.remove('hidden');
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

function hideCartDropdown() {
    const cartPopup = document.getElementById('cart-dropdown');
    if (cartPopup) {
        cartPopup.classList.add('hidden');
    }
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.createProductCard = createProductCard;
    window.navigateToProduct = navigateToProduct;
    window.toggleWishlist = toggleWishlist;
    window.quickViewProduct = quickViewProduct;
    window.closeQuickView = closeQuickView;
    window.getProductFromAnySources = getProductFromAnySources;
    window.quickViewIncreaseQuantity = quickViewIncreaseQuantity;
    window.quickViewDecreaseQuantity = quickViewDecreaseQuantity;
    window.quickViewAddToCart = quickViewAddToCart;
    window.showMegaMenu = showMegaMenu;
    window.hideMegaMenu = hideMegaMenu;
    window.getCategories = getCategories;
    window.getCategoryProductCount = getCategoryProductCount;
    window.getFeaturedProducts = getFeaturedProducts;
    window.updateWishlistDisplay = updateWishlistDisplay;
    window.getProductById = getProductById;
    window.showCartDropdown = showCartDropdown;
    window.hideCartDropdown = hideCartDropdown;
}

console.log('✅ Enhanced components.js loaded with fixed quick view functionality');