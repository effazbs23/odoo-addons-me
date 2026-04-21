// Enhanced Product Details Page JavaScript with Gallery Thumbnails and Improved Design

document.addEventListener('DOMContentLoaded', function() {
    console.log('Product details page loaded');
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Load product details
    loadProductDetails();
});

// Load product details based on URL parameter
function loadProductDetails() {
    const urlParams = new URLSearchParams(window.location.search);
    const productId = urlParams.get('id');
    
    if (!productId) {
        showProductNotFound();
        return;
    }
    
    // Get product data (using the same function from main.js)
    const product = getProductById(parseInt(productId));
    
    if (!product) {
        showProductNotFound();
        return;
    }
    
    // Display product details
    displayProductDetails(product);
    
    // Update breadcrumb
    updateBreadcrumb(product);
    
    // Load related products
    loadRelatedProducts(product);
}

// Get gallery images for a product (simulate multiple images)
function getProductGallery(product) {
    const categoryImages = {
        'vegetables': [
            product.image,
            "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1566385101042-1a0aa0c1268c?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1592921870789-04563d55041c?w=500&h=500&fit=crop"
        ],
        'fruits': [
            product.image,
            "https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1571836975135-8e9e459b1d31?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1559181567-c3190ca9959b?w=500&h=500&fit=crop"
        ],
        'dairy': [
            product.image,
            "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1606983340126-99ab4feaa64a?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=500&h=500&fit=crop"
        ],
        'bakery': [
            product.image,
            "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1568254183919-78a4f43a2877?w=500&h=500&fit=crop"
        ],
        'seafood': [
            product.image,
            "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1602491015122-8ab3e1c4063c?w=500&h=500&fit=crop",
            "https://images.unsplash.com/photo-1558818498-28c1e002b655?w=500&h=500&fit=crop"
        ]
    };
    
    return categoryImages[product.category] || [
        product.image,
        "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&h=500&fit=crop",
        "https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=500&h=500&fit=crop",
        "https://images.unsplash.com/photo-1488459716781-31db52582fe9?w=500&h=500&fit=crop"
    ];
}

// Change main product image
function changeMainImage(imageSrc, thumbnailElement) {
    const mainImage = document.getElementById('main-product-image');
    if (mainImage) {
        mainImage.src = imageSrc;
        
        // Update active thumbnail
        document.querySelectorAll('.gallery-thumbnail').forEach(thumb => {
            thumb.classList.remove('ring-2', 'ring-green-500', 'opacity-100');
            thumb.classList.add('opacity-70');
        });
        
        thumbnailElement.classList.remove('opacity-70');
        thumbnailElement.classList.add('ring-2', 'ring-green-500', 'opacity-100');
    }
}

// Display product details with enhanced design and gallery
function displayProductDetails(product) {
    const container = document.getElementById('product-details-container');
    const inWishlist = isInWishlist(product.id);
    const galleryImages = getProductGallery(product);
    
    container.innerHTML = `
        <!-- Enhanced Product Layout -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
            
            <!-- Left: Enhanced Gallery Section -->
            <div class="space-y-6">
                <!-- Main Product Image -->
                <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-3xl p-8 border border-green-100 relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-bl from-green-200/30 to-transparent rounded-full -translate-y-16 translate-x-16"></div>
                    <div class="absolute bottom-0 left-0 w-24 h-24 bg-gradient-to-tr from-emerald-200/30 to-transparent rounded-full translate-y-12 -translate-x-12"></div>
                    
                    <div class="relative z-10 aspect-square">
                        <img id="main-product-image" src="${galleryImages[0]}" alt="${product.name}" 
                             class="w-full h-full object-cover rounded-2xl shadow-xl transform hover:scale-105 transition-transform duration-500">
                    </div>
                    
                    <!-- Floating Badges -->
                    <div class="absolute top-6 left-6 flex flex-col gap-3 z-20">
                        ${product.sale ? '<span class="bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg animate-pulse">🔥 ON SALE</span>' : ''}
                        ${product.isNew ? '<span class="bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">✨ NEW</span>' : ''}
                        <span class="bg-gradient-to-r from-green-500 to-green-600 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">🌿 ORGANIC</span>
                    </div>
                    
                    <!-- Wishlist Button -->
                    <div class="absolute top-6 right-6 z-20">
                        <button onclick="addToWishlist(${product.id})" 
                                data-wishlist-id="${product.id}"
                                class="p-4 rounded-full backdrop-blur-sm transition-all shadow-xl hover:scale-110 ${inWishlist ? 'bg-red-500 text-white' : 'bg-white/90 text-gray-400 hover:text-red-500'}"
                                title="${inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}">
                            <i data-lucide="heart" class="h-6 w-6 ${inWishlist ? 'fill-current' : ''}"></i>
                        </button>
                    </div>
                </div>
                
                <!-- Thumbnail Gallery -->
                <div class="grid grid-cols-4 gap-4">
                    ${galleryImages.map((image, index) => `
                        <div class="relative group cursor-pointer">
                            <img src="${image}" alt="${product.name} ${index + 1}" 
                                 onclick="changeMainImage('${image}', this)"
                                 class="gallery-thumbnail w-full aspect-square object-cover rounded-xl shadow-md transition-all duration-300 hover:shadow-lg hover:scale-105 ${index === 0 ? 'ring-2 ring-green-500 opacity-100' : 'opacity-70'} hover:opacity-100">
                            <div class="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"></div>
                        </div>
                    `).join('')}
                </div>
                
                <!-- Product Features Grid -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-2xl border border-green-100 text-center group hover:shadow-lg transition-all duration-300">
                        <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform duration-300">
                            <i data-lucide="truck" class="h-6 w-6 text-white"></i>
                        </div>
                        <h4 class="font-bold text-green-700 mb-1">Free Delivery</h4>
                        <p class="text-sm text-green-600">On orders over $50</p>
                    </div>
                    <div class="bg-gradient-to-br from-blue-50 to-cyan-50 p-6 rounded-2xl border border-blue-100 text-center group hover:shadow-lg transition-all duration-300">
                        <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform duration-300">
                            <i data-lucide="shield-check" class="h-6 w-6 text-white"></i>
                        </div>
                        <h4 class="font-bold text-blue-700 mb-1">Certified Organic</h4>
                        <p class="text-sm text-blue-600">100% guarantee</p>
                    </div>
                    <div class="bg-gradient-to-br from-orange-50 to-yellow-50 p-6 rounded-2xl border border-orange-100 text-center group hover:shadow-lg transition-all duration-300">
                        <div class="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform duration-300">
                            <i data-lucide="clock" class="h-6 w-6 text-white"></i>
                        </div>
                        <h4 class="font-bold text-orange-700 mb-1">Fresh Daily</h4>
                        <p class="text-sm text-orange-600">Delivered within 24h</p>
                    </div>
                    <div class="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-2xl border border-purple-100 text-center group hover:shadow-lg transition-all duration-300">
                        <div class="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform duration-300">
                            <i data-lucide="award" class="h-6 w-6 text-white"></i>
                        </div>
                        <h4 class="font-bold text-purple-700 mb-1">Premium Quality</h4>
                        <p class="text-sm text-purple-600">Hand-picked selection</p>
                    </div>
                </div>
            </div>
            
            <!-- Right: Enhanced Product Information -->
            <div class="space-y-8">
                
                <!-- Product Header -->
                <div class="bg-white rounded-3xl shadow-xl border border-gray-100 p-8">
                    <!-- Brand & Category -->
                    <div class="flex items-center gap-3 mb-6">
                        <span class="bg-gradient-to-r from-gray-100 to-gray-200 text-gray-700 px-4 py-2 rounded-full font-semibold text-sm shadow-sm">${product.brand}</span>
                        <span class="bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 px-4 py-2 rounded-full font-semibold text-sm capitalize shadow-sm">${product.category}</span>
                    </div>
                    
                    <!-- Product Name -->
                    <h1 class="text-4xl lg:text-5xl font-bold text-gray-900 leading-tight mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text">${product.name}</h1>
                    
                    <!-- Rating & Reviews -->
                    <div class="flex items-center gap-4 mb-6 p-4 bg-yellow-50 rounded-2xl border border-yellow-200">
                        <div class="flex text-yellow-400 text-2xl">
                            ${Array(5).fill().map((_, i) => 
                                `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                            ).join('')}
                        </div>
                        <span class="text-2xl font-bold text-gray-700">${product.rating}</span>
                        <span class="text-gray-500 text-lg">(${Math.floor(Math.random() * 100) + 20} reviews)</span>
                        <a href="#reviews" class="text-blue-600 hover:text-blue-700 font-medium text-sm ml-auto">Read Reviews →</a>
                    </div>
                    
                    <!-- Price Section -->
                    <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 border-2 border-green-200 mb-6">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="flex items-center gap-4 mb-3">
                                    <span class="text-5xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                                    ${product.originalPrice ? 
                                        `<span class="text-2xl text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : 
                                        ''
                                    }
                                </div>
                                ${product.originalPrice ? 
                                    `<div class="bg-red-100 text-red-700 px-4 py-2 rounded-lg inline-block">
                                        <span class="font-bold">💰 Save $${(product.originalPrice - product.price).toFixed(2)} (${Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)}% off)</span>
                                    </div>` : 
                                    '<p class="text-green-700 font-semibold text-lg">🌿 Premium organic quality</p>'
                                }
                            </div>
                            ${product.originalPrice ? 
                                `<div class="text-center">
                                    <div class="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-4 rounded-2xl font-bold shadow-lg text-xl">
                                        ${Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)}% OFF
                                    </div>
                                    <p class="text-red-600 font-medium mt-2 text-sm">Limited time!</p>
                                </div>` : 
                                ''
                            }
                        </div>
                    </div>
                    
                    <!-- Product Options -->
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                        <div>
                            <h4 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                                <i data-lucide="package" class="h-4 w-4"></i>
                                Available Sizes:
                            </h4>
                            <div class="flex flex-wrap gap-2">
                                ${product.sizes ? product.sizes.map(size => 
                                    `<button class="bg-white hover:bg-green-50 border-2 border-gray-200 hover:border-green-400 text-gray-700 hover:text-green-700 px-4 py-2 rounded-lg font-medium transition-all duration-300 hover:shadow-md">${size}</button>`
                                ).join('') : '<span class="text-gray-500">Standard size available</span>'}
                            </div>
                        </div>
                        
                        <div>
                            <h4 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                                <i data-lucide="palette" class="h-4 w-4"></i>
                                Natural Colors:
                            </h4>
                            <div class="flex flex-wrap gap-3">
                                ${product.colors ? product.colors.map(color => 
                                    `<div class="flex items-center gap-2 bg-white border-2 border-gray-200 hover:border-gray-300 px-3 py-2 rounded-lg transition-all duration-300 cursor-pointer">
                                        <div class="w-4 h-4 rounded-full border-2 border-gray-300 shadow-sm" style="background-color: ${getColorCode(color)}"></div>
                                        <span class="text-gray-700 font-medium text-sm">${color}</span>
                                    </div>`
                                ).join('') : '<span class="text-gray-500">Natural color</span>'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="space-y-4">
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <button onclick="addToCartWithAjax(${product.id})" 
                                    class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-8 py-4 rounded-2xl font-bold text-lg transition-all duration-300 flex items-center justify-center gap-3 shadow-xl hover:shadow-2xl transform hover:scale-105">
                                <i data-lucide="shopping-cart" class="h-6 w-6"></i>
                                ADD TO CART
                            </button>
                            <button onclick="addToWishlist(${product.id})" 
                                    data-wishlist-id="${product.id}"
                                    class="px-8 py-4 rounded-2xl font-bold text-lg transition-all duration-300 shadow-xl hover:shadow-2xl transform hover:scale-105 ${inWishlist ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-white hover:bg-gray-50 text-gray-700 hover:text-red-500 border-2 border-gray-200 hover:border-red-300'} flex items-center justify-center gap-3"
                                    title="${inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}">
                                <i data-lucide="heart" class="h-6 w-6 ${inWishlist ? 'fill-current' : ''}"></i>
                                ${inWishlist ? 'SAVED' : 'SAVE'}
                            </button>
                        </div>
                        
                        <button onclick="window.location.href='products.html'" 
                                class="w-full bg-white hover:bg-gray-50 text-gray-700 hover:text-green-600 px-8 py-4 rounded-2xl font-semibold text-lg transition-all border-2 border-gray-200 hover:border-green-300 flex items-center justify-center gap-3 shadow-lg hover:shadow-xl">
                            <i data-lucide="arrow-left" class="h-5 w-5"></i>
                            Continue Shopping
                        </button>
                    </div>
                </div>
                
                <!-- Quick Product Info Cards -->
                <div class="grid grid-cols-2 gap-4">
                    <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 text-center group hover:shadow-xl transition-all duration-300">
                        <div class="text-3xl mb-3">🚚</div>
                        <h4 class="font-bold text-gray-800 mb-2">Fast Shipping</h4>
                        <p class="text-gray-600 text-sm">Same day delivery available</p>
                    </div>
                    <div class="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 text-center group hover:shadow-xl transition-all duration-300">
                        <div class="text-3xl mb-3">♻️</div>
                        <h4 class="font-bold text-gray-800 mb-2">Eco-Friendly</h4>
                        <p class="text-gray-600 text-sm">Sustainable packaging</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Enhanced Product Details Tabs -->
        <div class="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
            <!-- Tab Navigation -->
            <div class="border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
                <nav class="flex">
                    <button onclick="switchTab('description')" id="tab-description" class="px-8 py-6 font-bold text-gray-700 border-b-4 border-green-500 text-green-600 bg-white">
                        <div class="flex items-center gap-2">
                            <i data-lucide="file-text" class="h-5 w-5"></i>
                            Description
                        </div>
                    </button>
                    <button onclick="switchTab('details')" id="tab-details" class="px-8 py-6 font-bold text-gray-500 hover:text-gray-700 border-b-4 border-transparent hover:border-gray-300 transition-all duration-300">
                        <div class="flex items-center gap-2">
                            <i data-lucide="list" class="h-5 w-5"></i>
                            Details
                        </div>
                    </button>
                    <button onclick="switchTab('reviews')" id="tab-reviews" class="px-8 py-6 font-bold text-gray-500 hover:text-gray-700 border-b-4 border-transparent hover:border-gray-300 transition-all duration-300">
                        <div class="flex items-center gap-2">
                            <i data-lucide="star" class="h-5 w-5"></i>
                            Reviews
                        </div>
                    </button>
                </nav>
            </div>
            
            <!-- Tab Content -->
            <div class="p-8">
                <!-- Description Tab -->
                <div id="content-description" class="tab-content">
                    <div class="max-w-4xl">
                        <h3 class="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
                            <div class="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                                <i data-lucide="leaf" class="h-5 w-5 text-white"></i>
                            </div>
                            Product Description
                        </h3>
                        <p class="text-gray-700 leading-relaxed text-lg mb-8">${product.description}</p>
                        
                        <!-- Benefits Section -->
                        <div class="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-8">
                            <h4 class="font-bold text-green-800 mb-6 flex items-center gap-3 text-xl">
                                <div class="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
                                    <i data-lucide="check" class="h-4 w-4 text-white"></i>
                                </div>
                                Organic Benefits
                            </h4>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="flex items-center gap-3 text-green-700">
                                    <i data-lucide="shield-check" class="h-5 w-5 text-green-600"></i>
                                    <span class="font-medium">Certified organic by USDA standards</span>
                                </div>
                                <div class="flex items-center gap-3 text-green-700">
                                    <i data-lucide="leaf" class="h-5 w-5 text-green-600"></i>
                                    <span class="font-medium">No pesticides, herbicides, or chemicals</span>
                                </div>
                                <div class="flex items-center gap-3 text-green-700">
                                    <i data-lucide="heart" class="h-5 w-5 text-green-600"></i>
                                    <span class="font-medium">Supporting sustainable farming practices</span>
                                </div>
                                <div class="flex items-center gap-3 text-green-700">
                                    <i data-lucide="truck" class="h-5 w-5 text-green-600"></i>
                                    <span class="font-medium">Fresh delivery from local farms</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Details Tab -->
                <div id="content-details" class="tab-content hidden">
                    <h3 class="text-3xl font-bold text-gray-900 mb-8 flex items-center gap-3">
                        <div class="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                            <i data-lucide="info" class="h-5 w-5 text-white"></i>
                        </div>
                        Product Specifications
                    </h3>
                    
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        <!-- Product Info Table -->
                        <div class="bg-gray-50 rounded-2xl p-6">
                            <h4 class="font-bold text-gray-800 mb-4 text-xl">Product Information</h4>
                            <div class="space-y-4">
                                <div class="flex justify-between items-center py-3 border-b border-gray-200">
                                    <span class="font-medium text-gray-600">Brand:</span>
                                    <span class="font-bold text-gray-900">${product.brand}</span>
                                </div>
                                <div class="flex justify-between items-center py-3 border-b border-gray-200">
                                    <span class="font-medium text-gray-600">Category:</span>
                                    <span class="font-bold text-gray-900 capitalize">${product.category}</span>
                                </div>
                                <div class="flex justify-between items-center py-3 border-b border-gray-200">
                                    <span class="font-medium text-gray-600">Rating:</span>
                                    <span class="font-bold text-gray-900">${product.rating}/5.0 ⭐</span>
                                </div>
                                <div class="flex justify-between items-center py-3 border-b border-gray-200">
                                    <span class="font-medium text-gray-600">Organic Certified:</span>
                                    <span class="font-bold text-green-600">✓ Yes</span>
                                </div>
                                <div class="flex justify-between items-center py-3">
                                    <span class="font-medium text-gray-600">Origin:</span>
                                    <span class="font-bold text-gray-900">Local Farms</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Size & Color Options -->
                        <div class="bg-gray-50 rounded-2xl p-6">
                            <h4 class="font-bold text-gray-800 mb-4 text-xl">Available Options</h4>
                            
                            <div class="mb-6">
                                <h5 class="font-semibold text-gray-700 mb-3">Sizes Available:</h5>
                                <div class="flex flex-wrap gap-2">
                                    ${product.sizes ? product.sizes.map(size => 
                                        `<span class="bg-white border-2 border-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium shadow-sm">${size}</span>`
                                    ).join('') : '<span class="text-gray-500">Standard size</span>'}
                                </div>
                            </div>
                            
                            <div>
                                <h5 class="font-semibold text-gray-700 mb-3">Natural Colors:</h5>
                                <div class="flex flex-wrap gap-3">
                                    ${product.colors ? product.colors.map(color => 
                                        `<div class="flex items-center gap-2 bg-white border-2 border-gray-200 px-3 py-2 rounded-lg shadow-sm">
                                            <div class="w-5 h-5 rounded-full border-2 border-gray-300" style="background-color: ${getColorCode(color)}"></div>
                                            <span class="text-gray-700 font-medium">${color}</span>
                                        </div>`
                                    ).join('') : '<span class="text-gray-500">Natural color</span>'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Reviews Tab -->
                <div id="content-reviews" class="tab-content hidden">
                    <h3 class="text-3xl font-bold text-gray-900 mb-8 flex items-center gap-3">
                        <div class="w-10 h-10 bg-yellow-500 rounded-full flex items-center justify-center">
                            <i data-lucide="star" class="h-5 w-5 text-white"></i>
                        </div>
                        Customer Reviews
                    </h3>
                    
                    <!-- Rating Summary -->
                    <div class="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-2xl p-8 mb-8 border-2 border-yellow-200">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                            <div class="text-center">
                                <div class="text-6xl font-bold text-gray-900 mb-2">${product.rating}</div>
                                <div class="flex text-yellow-400 text-2xl justify-center mb-3">
                                    ${Array(5).fill().map((_, i) => 
                                        `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                    ).join('')}
                                </div>
                                <p class="text-gray-600 font-medium">${Math.floor(Math.random() * 100) + 20} verified reviews</p>
                            </div>
                            <div class="space-y-3">
                                ${Array(5).fill().map((_, i) => {
                                    const stars = 5 - i;
                                    const percentage = stars <= Math.floor(product.rating) ? Math.random() * 40 + 40 : Math.random() * 20;
                                    return `<div class="flex items-center gap-4">
                                        <span class="text-sm font-medium text-gray-600 w-12">${stars} star</span>
                                        <div class="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                                            <div class="bg-gradient-to-r from-yellow-400 to-orange-400 h-3 rounded-full transition-all duration-1000" style="width: ${percentage}%"></div>
                                        </div>
                                        <span class="text-sm font-medium text-gray-600 w-12">${percentage.toFixed(0)}%</span>
                                    </div>`;
                                }).join('')}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Sample Reviews -->
                    <div class="space-y-6">
                        <div class="bg-white border-2 border-gray-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300">
                            <div class="flex items-center gap-4 mb-4">
                                <div class="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">SM</div>
                                <div>
                                    <div class="font-bold text-gray-900 text-lg">Sarah M.</div>
                                    <div class="flex text-yellow-400 text-sm">★★★★★</div>
                                </div>
                                <div class="ml-auto text-sm text-gray-500">2 days ago</div>
                            </div>
                            <p class="text-gray-700 leading-relaxed text-lg">"Excellent quality and freshness. The organic certification gives me peace of mind. Will definitely order again!"</p>
                            <div class="mt-4 flex items-center gap-2 text-sm text-green-600">
                                <i data-lucide="check-circle" class="h-4 w-4"></i>
                                <span class="font-medium">Verified Purchase</span>
                            </div>
                        </div>
                        
                        <div class="bg-white border-2 border-gray-100 rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all duration-300">
                            <div class="flex items-center gap-4 mb-4">
                                <div class="w-12 h-12 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">JD</div>
                                <div>
                                    <div class="font-bold text-gray-900 text-lg">John D.</div>
                                    <div class="flex text-yellow-400 text-sm">★★★★★</div>
                                </div>
                                <div class="ml-auto text-sm text-gray-500">1 week ago</div>
                            </div>
                            <p class="text-gray-700 leading-relaxed text-lg">"Love the taste and quality. Fast delivery and great packaging. Highly recommended for anyone looking for premium organic products."</p>
                            <div class="mt-4 flex items-center gap-2 text-sm text-green-600">
                                <i data-lucide="check-circle" class="h-4 w-4"></i>
                                <span class="font-medium">Verified Purchase</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Tab switching functionality
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    
    // Reset all tab buttons
    document.querySelectorAll('[id^="tab-"]').forEach(tab => {
        tab.classList.remove('text-green-600', 'border-green-500', 'bg-white');
        tab.classList.add('text-gray-500', 'border-transparent');
    });
    
    // Show selected tab content
    document.getElementById(`content-${tabName}`).classList.remove('hidden');
    
    // Activate selected tab button
    const activeTab = document.getElementById(`tab-${tabName}`);
    activeTab.classList.remove('text-gray-500', 'border-transparent');
    activeTab.classList.add('text-green-600', 'border-green-500', 'bg-white');
}

// Load related products
function loadRelatedProducts(currentProduct) {
    const relatedContainer = document.getElementById('related-products');
    if (!relatedContainer) return;
    
    // Get all products except current one
    const allProducts = getAllProducts ? getAllProducts() : [];
    const relatedProducts = allProducts
        .filter(p => p.id !== currentProduct.id && p.category === currentProduct.category)
        .slice(0, 4);
    
    if (relatedProducts.length === 0) {
        // If no products in same category, get random products
        relatedProducts.push(...allProducts.filter(p => p.id !== currentProduct.id).slice(0, 4));
    }
    
    relatedContainer.innerHTML = relatedProducts.map(product => createProductCard(product)).join('');
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Update breadcrumb with product name
function updateBreadcrumb(product) {
    const breadcrumbElement = document.getElementById('breadcrumb-product-name');
    if (breadcrumbElement) {
        breadcrumbElement.textContent = product.name;
    }
    
    // Update page title
    document.title = `${product.name} - Natural Foods Organic Store`;
}

// Show product not found message
function showProductNotFound() {
    const container = document.getElementById('product-details-container');
    
    container.innerHTML = `
        <div class="min-h-[60vh] flex items-center justify-center">
            <div class="text-center max-w-md mx-auto bg-white rounded-3xl shadow-xl p-12 border border-gray-200">
                <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <i data-lucide="package-x" class="h-10 w-10 text-gray-400"></i>
                </div>
                <h1 class="text-3xl font-bold text-gray-900 mb-4">Product Not Found</h1>
                <p class="text-gray-600 mb-8">Sorry, we couldn't find the product you're looking for. It may have been removed or doesn't exist.</p>
                <div class="space-y-4">
                    <a href="products.html" class="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors shadow-lg hover:shadow-xl">
                        <i data-lucide="grid-3x3" class="h-4 w-4"></i>
                        Browse All Products
                    </a>
                    <br>
                    <a href="index.html" class="inline-flex items-center gap-2 text-green-600 hover:text-green-700 font-medium">
                        <i data-lucide="home" class="h-4 w-4"></i>
                        Back to Home
                    </a>
                </div>
            </div>
        </div>
    `;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Helper function to get color codes
function getColorCode(colorName) {
    const colorMap = {
        'Red': '#ef4444',
        'Green': '#22c55e',
        'Blue': '#3b82f6',
        'Yellow': '#eab308',
        'Orange': '#f97316',
        'Purple': '#a855f7',
        'Pink': '#ec4899',
        'Brown': '#a16207',
        'White': '#ffffff',
        'Black': '#000000',
        'Gray': '#6b7280',
        'Dark Green': '#166534'
    };
    
    return colorMap[colorName] || '#6b7280';
}

// Check if we need to include the product database functions here
// (These functions should already be available from main.js, but including fallbacks)
if (typeof getProductById === 'undefined') {
    console.warn('getProductById function not found. Loading fallback.');
    
    // Fallback product data
    window.getProductById = function(id) {
        // Basic fallback - in a real implementation, this would fetch from an API
        return {
            id: id,
            name: "Product " + id,
            price: 9.99,
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
            category: "organic",
            brand: "Natural Foods",
            description: "This is a sample product description. The actual product data should be loaded from the main.js file.",
            rating: 4.5,
            sale: false,
            isNew: false,
            sizes: ["Standard"],
            colors: ["Natural"]
        };
    };
}

if (typeof isInWishlist === 'undefined') {
    window.isInWishlist = function(productId) {
        const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
        return wishlist.some(item => item.id === productId);
    };
}

// Make functions global
window.switchTab = switchTab;
window.changeMainImage = changeMainImage;

console.log('Enhanced product details page JavaScript loaded');