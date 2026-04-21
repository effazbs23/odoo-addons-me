// Product Details Renderer - Handles all product rendering logic

// Render main product details
function renderProductDetails(product, selectedImage, quantity, selectedAttributes) {
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    const gallery = product.gallery || [product.image];
    
    return `
        <!-- Product Images Gallery -->
        <div class="space-y-4">
            <div class="relative">
                <img id="main-image" src="${gallery[selectedImage]}" alt="${product.name}" class="w-full h-96 object-cover rounded-2xl shadow-lg product-image">
                
                <!-- Badges -->
                ${product.sale && product.salePercentage ? `<div class="absolute top-4 left-4 bg-red-500 text-white px-4 py-2 rounded-full text-sm font-bold">-${product.salePercentage}% OFF</div>` : ''}
                ${product.isNew ? `<div class="absolute top-4 right-4 bg-blue-500 text-white px-4 py-2 rounded-full text-sm font-bold">NEW</div>` : ''}
            </div>
            
            <!-- Thumbnail Gallery -->
            ${gallery.length > 1 ? `
                <div class="flex gap-3 overflow-x-auto">
                    ${gallery.map((img, index) => `
                        <button onclick="changeMainImage('${img}', ${index})" class="thumbnail flex-shrink-0 rounded-lg overflow-hidden border-2 ${selectedImage === index ? 'border-green-500 active' : 'border-gray-200'}">
                            <img src="${img}" alt="${product.name} ${index + 1}" class="w-20 h-20 object-cover">
                        </button>
                    `).join('')}
                </div>
            ` : ''}
        </div>

        <!-- Product Info -->
        <div class="space-y-6">
            ${renderProductInfo(product)}
            ${renderPricing(product, savings)}
            ${renderAttributes(product, selectedAttributes)}
            ${renderQuantityAndCart(product, quantity)}
            ${renderActionButtons(product)}
            ${renderTrustIndicators()}
        </div>
    `;
}

// Render product information section
function renderProductInfo(product) {
    return `
        <div>
            <div class="flex items-center gap-2 mb-3">
                <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-semibold capitalize">${product.category}</span>
                <span class="text-gray-400">•</span>
                <span class="text-gray-600">${product.brand}</span>
            </div>
            <h1 class="text-4xl font-bold text-gray-900 mb-4">${product.name}</h1>
            <p class="text-lg text-gray-600 leading-relaxed">${product.longDescription || product.description}</p>
        </div>

        <!-- Rating -->
        <div class="flex items-center gap-4">
            <div class="flex items-center gap-2">
                <div class="flex text-yellow-400 text-xl">
                    ${Array(5).fill().map((_, i) => 
                        `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                    ).join('')}
                </div>
                <span class="text-gray-600 font-semibold">${product.rating}</span>
            </div>
            <span class="text-gray-400">•</span>
            <span class="text-gray-600">${product.reviews} reviews</span>
            <span class="text-gray-400">•</span>
            <span class="flex items-center gap-1 ${product.inStock ? 'text-green-600' : 'text-red-600'}">
                <i data-lucide="${product.inStock ? 'check-circle' : 'x-circle'}" class="h-4 w-4"></i>
                ${product.inStock ? 'In Stock' : 'Out of Stock'}
            </span>
        </div>

        ${product.weight ? `
            <div class="flex items-center gap-4 text-sm text-gray-600">
                <span>Brand: <strong>${product.brand}</strong></span>
                <span>Weight: <strong>${product.weight}</strong></span>
            </div>
        ` : ''}
    `;
}

// Render pricing section
function renderPricing(product, savings) {
    return `
        <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6">
            <div class="flex items-center justify-between">
                <div>
                    <div class="flex items-center gap-3 mb-2">
                        <span id="current-price" class="text-4xl font-bold text-green-600">$${getCurrentPrice(product).toFixed(2)}</span>
                        ${product.originalPrice ? `<span class="text-xl text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                    </div>
                    ${savings > 0 ? `
                        <div class="flex items-center gap-2">
                            <span class="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">Save $${savings.toFixed(2)}</span>
                            <span class="text-green-700 font-semibold">${Math.round((savings / product.originalPrice) * 100)}% off</span>
                        </div>
                    ` : '<span class="text-green-700 font-semibold">Premium Quality Guaranteed</span>'}
                </div>
                <div class="text-center">
                    <div class="text-3xl mb-2">🚚</div>
                    <div class="text-sm text-gray-600">Free Delivery</div>
                </div>
            </div>
        </div>
    `;
}

// Render product attributes
function renderAttributes(product, selectedAttributes) {
    if (!product.attributes) return '';
    
    let attributesHtml = '<div class="space-y-4">';
    
    // Weight/Size options
    if (product.attributes.weight) {
        attributesHtml += `
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">Weight/Size:</label>
                <div class="flex flex-wrap gap-2">
                    ${product.attributes.weight.map(option => `
                        <button onclick="handleAttributeChange('weight', '${option.value}', ${option.price})" 
                                class="attribute-option px-3 py-2 border rounded-lg text-sm transition-all ${!option.available ? 'disabled' : ''} ${selectedAttributes.weight === option.value ? 'selected' : 'border-gray-200 hover:border-gray-300'}"
                                ${!option.available ? 'disabled' : ''}>
                            ${option.label} - $${option.price.toFixed(2)}
                            ${!option.available ? ' (Unavailable)' : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Size options
    if (product.attributes.size) {
        attributesHtml += `
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">Size:</label>
                <div class="flex flex-wrap gap-2">
                    ${product.attributes.size.map(option => `
                        <button onclick="handleAttributeChange('size', '${option.value}')" 
                                class="attribute-option px-3 py-2 border rounded-lg text-sm transition-all ${!option.available ? 'disabled' : ''} ${selectedAttributes.size === option.value ? 'selected' : 'border-gray-200 hover:border-gray-300'}"
                                ${!option.available ? 'disabled' : ''}>
                            ${option.label}
                            ${!option.available ? ' (Unavailable)' : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Color options
    if (product.attributes.color) {
        attributesHtml += `
            <div>
                <label class="block text-sm font-semibold text-gray-700 mb-2">Color:</label>
                <div class="flex flex-wrap gap-2">
                    ${product.attributes.color.map(option => `
                        <button onclick="handleAttributeChange('color', '${option.value}')" 
                                class="attribute-option px-3 py-2 border rounded-lg text-sm transition-all ${!option.available ? 'disabled' : ''} ${selectedAttributes.color === option.value ? 'selected' : 'border-gray-200 hover:border-gray-300'}"
                                ${!option.available ? 'disabled' : ''}>
                            ${option.label}
                            ${!option.available ? ' (Unavailable)' : ''}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    attributesHtml += '</div>';
    return attributesHtml;
}

// Render quantity and cart section
function renderQuantityAndCart(product, quantity) {
    return `
        <div class="space-y-6">
            <div class="flex items-center gap-6">
                <div>
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Quantity</label>
                    <div class="quantity-controls flex items-center gap-3">
                        <button id="decrease-btn" class="quantity-btn" onclick="changeQuantity(-1)">
                            <i data-lucide="minus" class="h-5 w-5"></i>
                        </button>
                        <span id="quantity-display" class="text-xl font-bold text-gray-900 w-12 text-center">${quantity}</span>
                        <button class="quantity-btn" onclick="changeQuantity(1)">
                            <i data-lucide="plus" class="h-5 w-5"></i>
                        </button>
                    </div>
                </div>
                <div class="flex-1">
                    <label class="block text-sm font-semibold text-gray-700 mb-2">Total Price</label>
                    <div id="total-price" class="text-3xl font-bold text-green-600">$${(getCurrentPrice(product) * quantity).toFixed(2)}</div>
                </div>
            </div>

            <div class="flex gap-4">
                <button onclick="addToCart()" class="add-to-cart-btn flex-1 flex items-center justify-center gap-3" ${!product.inStock ? 'disabled' : ''}>
                    <i data-lucide="shopping-cart" class="h-6 w-6"></i>
                    ${product.inStock ? 'Add to Cart' : 'Out of Stock'}
                </button>
                <button onclick="addToWishlist()" class="p-4 border-2 border-gray-300 rounded-xl hover:border-red-500 hover:bg-red-50 transition-colors">
                    <i data-lucide="heart" class="h-6 w-6 text-gray-600 hover:text-red-500"></i>
                </button>
            </div>

            <button onclick="buyNow()" class="w-full bg-orange-600 hover:bg-orange-700 text-white px-8 py-4 rounded-xl font-bold text-lg transition-colors" ${!product.inStock ? 'disabled' : ''}>
                ${product.inStock ? 'Buy Now - Express Checkout' : 'Currently Unavailable'}
            </button>
        </div>
    `;
}

// Render action buttons
function renderActionButtons(product) {
    return `
        <div class="flex gap-4">
            <button onclick="shareProduct()" class="flex-1 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-200 hover:border-gray-300 px-6 py-3 rounded-xl font-semibold transition-colors flex items-center justify-center gap-2">
                <i data-lucide="share-2" class="h-4 w-4"></i>
                Share Product
            </button>
        </div>
    `;
}

// Render trust indicators
function renderTrustIndicators() {
    return `
        <div class="border-t border-gray-200 pt-6">
            <div class="grid grid-cols-3 gap-6 text-center">
                <div class="space-y-2">
                    <div class="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                        <i data-lucide="shield-check" class="h-6 w-6 text-green-600"></i>
                    </div>
                    <div class="text-sm font-semibold text-gray-900">Certified Organic</div>
                </div>
                <div class="space-y-2">
                    <div class="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                        <i data-lucide="truck" class="h-6 w-6 text-blue-600"></i>
                    </div>
                    <div class="text-sm font-semibold text-gray-900">Free Delivery</div>
                </div>
                <div class="space-y-2">
                    <div class="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto">
                        <i data-lucide="rotate-ccw" class="h-6 w-6 text-orange-600"></i>
                    </div>
                    <div class="text-sm font-semibold text-gray-900">30-Day Returns</div>
                </div>
            </div>
        </div>
    `;
}

// Render related product card
function createRelatedProductCard(product) {
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    
    return `
        <div class="related-product-card bg-white border border-gray-200 rounded-xl p-4 hover:shadow-lg transition-all">
            <div class="relative mb-4">
                <img src="${product.image}" alt="${product.name}" class="w-full h-40 object-cover rounded-lg">
                ${product.sale ? '<div class="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">SALE</div>' : ''}
            </div>
            <h3 class="font-bold text-gray-900 mb-2 cursor-pointer hover:text-green-600" onclick="window.location.href='product-details.html?id=${product.id}'">${product.name}</h3>
            <div class="flex items-center gap-2 mb-3">
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
                        <span class="text-lg font-bold text-green-600">$${product.price.toFixed(2)}</span>
                        ${product.originalPrice ? `<span class="text-sm text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                    </div>
                    ${savings > 0 ? `<span class="text-xs text-red-600 font-semibold">Save $${savings.toFixed(2)}</span>` : ''}
                </div>
                <button onclick="quickAddToCart(${product.id})" class="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg text-sm font-semibold transition-colors">
                    Add
                </button>
            </div>
        </div>
    `;
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
    window.renderProductInfo = renderProductInfo;
    window.renderPricing = renderPricing;
    window.renderAttributes = renderAttributes;
    window.renderQuantityAndCart = renderQuantityAndCart;
    window.renderActionButtons = renderActionButtons;
    window.renderTrustIndicators = renderTrustIndicators;
    window.createRelatedProductCard = createRelatedProductCard;
    window.getCurrentPrice = getCurrentPrice;
}