// Ultra-Modern Product Details Renderers - Advanced design system

// Render complete product details layout
function renderProductDetails(product, selectedImage, quantity, selectedAttributes) {
    const gallery = product.gallery || [product.image, product.image, product.image, product.image];
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    
    // Update hero section
    updateHeroSection(product);
    
    return `
        <!-- Premium Product Gallery -->
        <div class="premium-gallery">
            ${renderUltraModernGallery(product, gallery, selectedImage)}
        </div>

        <!-- Premium Product Information -->
        <div class="space-y-8">
            ${renderUltraModernProductInfo(product)}
            ${renderPremiumPricing(product, savings)}
            ${renderModernAttributes(product, selectedAttributes)}
            ${renderPremiumActions(product, quantity)}
        </div>
    `;
}

// Update hero section with product info
function updateHeroSection(product) {
    const heroTitle = document.getElementById('hero-title');
    const heroDescription = document.getElementById('hero-description');
    const breadcrumbCategory = document.getElementById('breadcrumb-category');
    
    if (heroTitle) {
        heroTitle.innerHTML = `Premium <br><span class="text-green-200">${product.name}</span>`;
    }
    
    if (heroDescription) {
        heroDescription.textContent = product.longDescription || product.description;
    }
    
    if (breadcrumbCategory) {
        breadcrumbCategory.textContent = product.category.charAt(0).toUpperCase() + product.category.slice(1);
    }
}

// Render ultra-modern gallery section
function renderUltraModernGallery(product, gallery, selectedImage) {
    return `
        <div class="main-product-image">
            <img id="main-image" src="${gallery[selectedImage]}" alt="${product.name}" class="w-full h-full object-cover">
            
            <!-- Premium Badges -->
            ${product.sale && product.salePercentage ? `
                <div class="absolute top-8 left-8 glass-morphism px-6 py-3 rounded-2xl">
                    <div class="flex items-center gap-2 text-red-600 font-bold">
                        <i data-lucide="flame" class="h-5 w-5"></i>
                        <span>-${product.salePercentage}% OFF</span>
                    </div>
                </div>
            ` : ''}
            ${product.isNew ? `
                <div class="absolute top-8 right-8 glass-morphism px-6 py-3 rounded-2xl">
                    <div class="flex items-center gap-2 text-blue-600 font-bold">
                        <i data-lucide="sparkles" class="h-5 w-5"></i>
                        <span>NEW ARRIVAL</span>
                    </div>
                </div>
            ` : ''}
            
            <!-- Organic Certification Badge -->
            <div class="absolute bottom-8 left-8 glass-morphism px-6 py-3 rounded-2xl">
                <div class="flex items-center gap-2 text-green-600 font-bold">
                    <i data-lucide="leaf" class="h-5 w-5"></i>
                    <span>100% ORGANIC</span>
                </div>
            </div>
            
            <!-- Image Navigation -->
            ${gallery.length > 1 ? `
                <button onclick="navigateImage(-1)" class="absolute left-4 top-1/2 transform -translate-y-1/2 glass-morphism p-4 rounded-2xl hover:scale-110 transition-all">
                    <i data-lucide="chevron-left" class="h-6 w-6 text-gray-700"></i>
                </button>
                <button onclick="navigateImage(1)" class="absolute right-4 top-1/2 transform -translate-y-1/2 glass-morphism p-4 rounded-2xl hover:scale-110 transition-all">
                    <i data-lucide="chevron-right" class="h-6 w-6 text-gray-700"></i>
                </button>
            ` : ''}
        </div>
        
        <!-- Thumbnail Gallery -->
        ${gallery.slice(1, 5).map((img, index) => `
            <div class="gallery-thumb ${selectedImage === index + 1 ? 'active' : ''}" onclick="changeMainImage('${img}', ${index + 1})">
                <img src="${img}" alt="${product.name} ${index + 2}" class="w-full h-full object-cover">
            </div>
        `).join('')}
    `;
}

// Render ultra-modern product information
function renderUltraModernProductInfo(product) {
    return `
        <div class="space-y-8">
            <!-- Product Badges -->
            <div class="flex items-center gap-4 flex-wrap">
                <span class="modern-badge">
                    <span class="text-xl">${getCategoryIcon(product.category)}</span>
                    ${product.category}
                </span>
                <span class="modern-badge">
                    <i data-lucide="award" class="h-5 w-5"></i>
                    ${product.brand}
                </span>
                <span class="modern-badge">
                    <i data-lucide="check-circle" class="h-5 w-5"></i>
                    ${product.inStock ? 'In Stock' : 'Out of Stock'}
                </span>
            </div>
            
            <!-- Product Title -->
            <div>
                <h1 class="text-4xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">${product.name}</h1>
                <p class="text-xl text-gray-600 leading-relaxed max-w-2xl">${product.longDescription || product.description}</p>
            </div>
            
            <!-- Premium Rating Card -->
            <div class="ultra-modern-card p-8">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-6">
                        <div class="text-center">
                            <div class="text-5xl font-bold gradient-text mb-2">${product.rating}</div>
                            <div class="flex text-yellow-400 text-xl mb-2">
                                ${Array(5).fill().map((_, i) => 
                                    `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                ).join('')}
                            </div>
                            <p class="text-gray-600">Outstanding Rating</p>
                        </div>
                        <div class="h-16 w-px bg-gray-200"></div>
                        <div class="text-center">
                            <div class="text-3xl font-bold text-gray-900 mb-2">${product.reviews}</div>
                            <p class="text-gray-600">Customer Reviews</p>
                        </div>
                        <div class="h-16 w-px bg-gray-200"></div>
                        <div class="text-center">
                            <div class="text-3xl mb-2">🏆</div>
                            <p class="text-gray-600">Top Rated</p>
                        </div>
                    </div>
                    <button class="neon-button px-8 py-4">
                        <i data-lucide="edit-3" class="h-5 w-5 mr-2"></i>
                        Write Review
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Render premium pricing section
function renderPremiumPricing(product, savings) {
    return `
        <div class="premium-pricing">
            <div class="relative z-10 text-center">
                <h3 class="text-2xl font-bold text-gray-800 mb-6">Premium Pricing</h3>
                <div class="flex items-center justify-center gap-6 mb-8 flex-wrap">
                    <span id="current-price" class="text-6xl lg:text-7xl font-bold text-green-600">${getCurrentPrice(product).toFixed(2)}</span>
                    ${product.originalPrice ? `<span class="text-3xl text-gray-500 line-through">${product.originalPrice.toFixed(2)}</span>` : ''}
                    ${savings > 0 ? `
                        <span class="bg-gradient-to-r from-red-500 to-red-600 text-white px-6 py-3 rounded-2xl text-lg font-bold shadow-lg">
                            💰 Save ${savings.toFixed(2)} (${Math.round((savings / product.originalPrice) * 100)}% OFF)
                        </span>
                    ` : ''}
                </div>
                ${savings <= 0 ? '<div class="text-green-700 font-bold text-xl mb-8">🌟 Premium Quality Guaranteed</div>' : ''}
                
                <div class="grid grid-cols-3 gap-6">
                    <div class="ultra-modern-card p-6 text-center">
                        <div class="text-4xl mb-3">🚚</div>
                        <div class="text-sm font-bold text-gray-700">Free Delivery</div>
                    </div>
                    <div class="ultra-modern-card p-6 text-center">
                        <div class="text-4xl mb-3">🌱</div>
                        <div class="text-sm font-bold text-gray-700">100% Organic</div>
                    </div>
                    <div class="ultra-modern-card p-6 text-center">
                        <div class="text-4xl mb-3">⭐</div>
                        <div class="text-sm font-bold text-gray-700">${product.rating} Rating</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Render modern attributes
function renderModernAttributes(product, selectedAttributes) {
    if (!product.attributes) return '';
    
    let attributesHtml = '<div class="space-y-8">';
    
    // Weight/Size options
    if (product.attributes.weight) {
        attributesHtml += `
            <div class="ultra-modern-card p-8">
                <label class="flex items-center gap-3 text-xl font-bold text-gray-700 mb-6">
                    <i data-lucide="package" class="h-6 w-6 text-green-600"></i>
                    Weight & Size Options
                </label>
                <div class="attribute-selector">
                    ${product.attributes.weight.map(option => `
                        <button onclick="handleAttributeChange('weight', '${option.value}', ${option.price})" 
                                class="attribute-option ${selectedAttributes.weight === option.value ? 'selected' : ''} ${!option.available ? 'opacity-50 cursor-not-allowed' : ''}"
                                ${!option.available ? 'disabled' : ''}>
                            <div class="text-lg font-bold">${option.label}</div>
                            <div class="text-green-600 font-semibold">$${option.price.toFixed(2)}</div>
                            ${!option.available ? '<div class="text-red-500 text-sm">Unavailable</div>' : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    attributesHtml += '</div>';
    return attributesHtml;
}

// Render premium actions section
function renderPremiumActions(product, quantity) {
    return `
        <div class="space-y-8">
            <!-- Quantity Control -->
            <div class="ultra-modern-card p-8">
                <div class="grid grid-cols-2 gap-8">
                    <div>
                        <div class="quantity-control">
                            <button id="decrease-btn" class="quantity-btn" onclick="changeQuantity(-1)">
                                <i data-lucide="minus" class="h-5 w-5"></i>
                            </button>
                            <span id="quantity-display" class="text-3xl font-bold text-gray-900 min-w-[5rem] text-center">${quantity}</span>
                            <button class="quantity-btn" onclick="changeQuantity(1)">
                                <i data-lucide="plus" class="h-5 w-5"></i>
                            </button>
                        </div>
                    </div>
                    <div>
                        <label class="flex items-center gap-3 text-xl font-bold text-gray-700 mb-6">
                            <i data-lucide="calculator" class="h-6 w-6 text-green-600"></i>
                            Total Price
                        </label>
                        <div id="total-price" class="text-4xl font-bold gradient-text">$${(getCurrentPrice(product) * quantity).toFixed(2)}</div>
                    </div>
                </div>
            </div>

            <!-- Primary Action Buttons -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <button onclick="addToCart()" class="neon-button flex items-center justify-center gap-3 w-full pulse-glow" ${!product.inStock ? 'disabled' : ''}>
                    <i data-lucide="shopping-cart" class="h-6 w-6"></i>
                    <span>Add to Cart</span>
                </button>
                <button onclick="buyNow()" class="bg-gradient-to-r from-orange-500 to-red-500 text-white px-8 py-5 rounded-2xl font-bold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-3 hover:scale-105" ${!product.inStock ? 'disabled' : ''}>
                    <i data-lucide="zap" class="h-6 w-6"></i>
                    <span>Buy Instantly</span>
                </button>
            </div>

            <!-- Secondary Actions Grid -->
            <div class="grid grid-cols-3 gap-6">
                <button onclick="addToWishlist()" class="ultra-modern-card p-6 flex flex-col items-center gap-3 hover:shadow-lg transition-all group">
                    <div class="w-12 h-12 bg-gradient-to-br from-red-100 to-pink-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                        <i data-lucide="heart" class="h-6 w-6 text-red-500"></i>
                    </div>
                    <span class="font-bold text-gray-700">Add to Wishlist</span>
                </button>
                <button onclick="shareProduct()" class="ultra-modern-card p-6 flex flex-col items-center gap-3 hover:shadow-lg transition-all group">
                    <div class="w-12 h-12 bg-gradient-to-br from-blue-100 to-sky-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                        <i data-lucide="share-2" class="h-6 w-6 text-blue-500"></i>
                    </div>
                    <span class="font-bold text-gray-700">Share Product</span>
                </button>
                <button onclick="compareProduct()" class="ultra-modern-card p-6 flex flex-col items-center gap-3 hover:shadow-lg transition-all group">
                    <div class="w-12 h-12 bg-gradient-to-br from-purple-100 to-violet-100 rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform">
                        <i data-lucide="scale" class="h-6 w-6 text-purple-500"></i>
                    </div>
                    <span class="font-bold text-gray-700">Compare</span>
                </button>
            </div>
            
            <!-- Product Specifications -->
            <div class="ultra-modern-card p-8">
                <h4 class="text-xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <i data-lucide="clipboard-list" class="h-6 w-6 text-green-600"></i>
                    Product Specifications
                </h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div class="flex justify-between py-3 border-b border-gray-100">
                        <span class="text-gray-600">SKU:</span>
                        <span class="font-semibold">${product.sku || 'NF-' + product.id.toString().padStart(3, '0')}</span>
                    </div>
                    <div class="flex justify-between py-3 border-b border-gray-100">
                        <span class="text-gray-600">Weight:</span>
                        <span class="font-semibold">${product.weight}</span>
                    </div>
                    <div class="flex justify-between py-3 border-b border-gray-100">
                        <span class="text-gray-600">Brand:</span>
                        <span class="font-semibold">${product.brand}</span>
                    </div>
                    <div class="flex justify-between py-3 border-b border-gray-100">
                        <span class="text-gray-600">Category:</span>
                        <span class="font-semibold capitalize">${product.category}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Render related product card
function renderRelatedProductCard(product) {
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    
    return `
        <div class="related-product p-6">
            <div class="relative mb-6">
                <img src="${product.image}" alt="${product.name}" class="w-full h-48 object-cover rounded-2xl">
                ${product.sale ? '<div class="absolute top-3 left-3 bg-red-500 text-white px-3 py-1 rounded-xl text-xs font-bold">SALE</div>' : ''}
                ${product.isNew ? '<div class="absolute top-3 right-3 bg-blue-500 text-white px-3 py-1 rounded-xl text-xs font-bold">NEW</div>' : ''}
            </div>
            
            <div class="space-y-4">
                <h3 class="text-lg font-bold text-gray-900 cursor-pointer hover:text-green-600 transition-colors" onclick="window.location.href='product-details.html?id=${product.id}'">${product.name}</h3>
                
                <div class="flex items-center gap-2">
                    <div class="flex text-yellow-400 text-sm">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="text-gray-600 text-sm">(${product.rating})</span>
                </div>
                
                <div class="flex items-center justify-between">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                            ${product.originalPrice ? `<span class="text-sm text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${savings > 0 ? `<span class="text-xs text-red-600 font-semibold">Save $${savings.toFixed(2)}</span>` : ''}
                    </div>
                    <button onclick="quickAddToCart(${product.id})" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-bold transition-all shadow-lg hover:shadow-xl hover:scale-105 flex items-center gap-2">
                        <i data-lucide="plus" class="h-4 w-4"></i>
                        Add
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Get category icon
function getCategoryIcon(category) {
    const icons = {
        vegetables: '🥬',
        fruits: '🍎', 
        dairy: '🥛',
        seafood: '🐟',
        bakery: '🍞'
    };
    return icons[category] || '🌿';
}

// Get current price based on selected attributes
function getCurrentPrice(product, selectedAttributes = {}) {
    if (selectedAttributes.weight && product.attributes?.weight) {
        const weightOption = product.attributes.weight.find(w => w.value === selectedAttributes.weight);
        return weightOption?.price || product.price;
    }
    return product.price;
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.renderProductDetails = renderProductDetails;
    window.updateHeroSection = updateHeroSection;
    window.renderUltraModernGallery = renderUltraModernGallery;
    window.renderUltraModernProductInfo = renderUltraModernProductInfo;
    window.renderPremiumPricing = renderPremiumPricing;
    window.renderModernAttributes = renderModernAttributes;
    window.renderPremiumActions = renderPremiumActions;
    window.renderRelatedProductCard = renderRelatedProductCard;
    window.getCurrentPrice = getCurrentPrice;
    window.getCategoryIcon = getCategoryIcon;
}