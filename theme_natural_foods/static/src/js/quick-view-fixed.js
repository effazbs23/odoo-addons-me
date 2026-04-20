// Bootstrap Quick View System for Natural Foods
console.log('🔍 Loading Bootstrap quick-view system...');

(function() {
    'use strict';
    
    // Quick view state
    let isQuickViewOpen = false;
    let currentProductData = null;
    
    // Get product data from the main products array
    function getProductDataSource() {
        // Try multiple sources for product data
        if (typeof PRODUCTS_DATA !== 'undefined' && Array.isArray(PRODUCTS_DATA)) {
            return PRODUCTS_DATA;
        }
        if (typeof window.productsData !== 'undefined' && Array.isArray(window.productsData)) {
            return window.productsData;
        }
        if (typeof window.PRODUCTS !== 'undefined' && Array.isArray(window.PRODUCTS)) {
            return window.PRODUCTS;
        }
        // Fallback mock data for testing
        return [
            {
                id: 1,
                name: "Organic Roma Tomatoes",
                price: 2.99,
                originalPrice: 4.99,
                rating: 4.8,
                description: "Fresh, vine-ripened organic tomatoes bursting with flavor. Perfect for salads, cooking, or eating fresh. These premium tomatoes are grown without pesticides and are certified organic.",
                image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=600&h=600&fit=crop",
                category: "vegetables",
                brand: "Fresh Farm",
                sale: true,
                inStock: true,
                weight: "1 lb"
            },
            {
                id: 2,
                name: "Organic Honey Crisp Apples",
                price: 5.99,
                rating: 4.9,
                description: "Sweet and crispy organic apples, perfect for snacking or baking. These premium apples are hand-picked at peak ripeness for maximum flavor and nutrition.",
                image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=600&h=600&fit=crop",
                category: "fruits",
                brand: "Orchard Fresh",
                new: true,
                inStock: true,
                weight: "2 lbs"
            }
        ];
    }
    
    // Create Bootstrap quick view modal HTML
    function createQuickViewModal() {
        // Remove existing modal if any
        const existing = document.getElementById('quick-view-modal');
        if (existing) {
            existing.remove();
        }
        
        const modal = document.createElement('div');
        modal.id = 'quick-view-modal';
        modal.className = 'modal fade';
        modal.setAttribute('tabindex', '-1');
        modal.setAttribute('aria-labelledby', 'quickViewModalLabel');
        modal.setAttribute('aria-hidden', 'true');
        modal.innerHTML = `
            <div class="modal-dialog modal-xl modal-dialog-centered">
                <div class="modal-content border-0 shadow-lg" style="border-radius: 15px;">
                    <!-- Modal Header -->
                    <div class="modal-header border-0 pb-0">
                        <h5 class="modal-title fw-bold text-dark" id="quickViewModalLabel">
                            <i class="bi bi-eye text-success me-2"></i>Quick View
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    
                    <!-- Modal Body -->
                    <div class="modal-body p-4">
                        <div id="quick-view-content">
                            <!-- Content will be inserted here -->
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }
    
    // Get product data
    function getProductData(productId) {
        const id = parseInt(productId);
        const productsSource = getProductDataSource();
        
        // Find product in the data source
        const product = productsSource.find(p => p.id === id);
        
        if (!product) {
            console.warn('Product not found with ID:', id);
            // Return first product as fallback
            return productsSource[0] || null;
        }
        
        return product;
    }
    
    // Show quick view modal
    function showQuickView(productId) {
        console.log('🔍 Opening quick view for product:', productId);
        
        const product = getProductData(productId);
        if (!product) {
            console.error('❌ Product not found:', productId);
            return;
        }
        
        currentProductData = product;
        
        // Create modal if it doesn't exist
        let modal = document.getElementById('quick-view-modal');
        if (!modal) {
            modal = createQuickViewModal();
        }
        
        // Populate content
        populateQuickViewContent(product);
        
        // Show Bootstrap modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        isQuickViewOpen = true;
        
        console.log('✅ Quick view opened for:', product.name);
    }
    
    // Close quick view modal
    function closeQuickView() {
        const modal = document.getElementById('quick-view-modal');
        if (modal) {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
            isQuickViewOpen = false;
            currentProductData = null;
            console.log('✅ Quick view closed');
        }
    }
    
    // Populate Bootstrap modal content
    function populateQuickViewContent(product) {
        const content = document.getElementById('quick-view-content');
        if (!content) return;
        
        const hasDiscount = product.originalPrice && product.originalPrice > product.price;
        const savings = hasDiscount ? (product.originalPrice - product.price) : 0;
        const discountPercent = hasDiscount ? Math.round((savings / product.originalPrice) * 100) : 0;
        
        // Generate stars for rating
        const fullStars = Math.floor(product.rating);
        const hasHalfStar = product.rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let starsHtml = '';
        for (let i = 0; i < fullStars; i++) {
            starsHtml += '<i class="bi bi-star-fill text-warning"></i>';
        }
        if (hasHalfStar) {
            starsHtml += '<i class="bi bi-star-half text-warning"></i>';
        }
        for (let i = 0; i < emptyStars; i++) {
            starsHtml += '<i class="bi bi-star text-muted"></i>';
        }
        
        content.innerHTML = `
            <div class="row g-4">
                <!-- Product Image -->
                <div class="col-md-6">
                    <div class="position-relative">
                        <div class="bg-light rounded-3 overflow-hidden" style="aspect-ratio: 1;">
                            <img src="${product.image}" alt="${product.name}" class="w-100 h-100" style="object-fit: cover;">
                        </div>
                        
                        <!-- Badges -->
                        <div class="position-absolute top-0 start-0 p-3">
                            ${product.sale ? '<span class="badge bg-danger mb-2 d-block">🔥 SALE</span>' : ''}
                            ${product.new ? '<span class="badge bg-primary mb-2 d-block">✨ NEW</span>' : ''}
                            <span class="badge bg-success">🌱 ORGANIC</span>
                        </div>
                        
                        <!-- Trust Indicators -->
                        <div class="position-absolute bottom-0 start-0 end-0 p-3">
                            <div class="row g-2">
                                <div class="col-6">
                                    <div class="bg-white bg-opacity-90 rounded-2 p-2 text-center small">
                                        <div class="text-success fw-bold">✓ CERTIFIED</div>
                                        <div class="text-muted" style="font-size: 0.75rem;">USDA Organic</div>
                                    </div>
                                </div>
                                <div class="col-6">
                                    <div class="bg-white bg-opacity-90 rounded-2 p-2 text-center small">
                                        <div class="text-primary fw-bold">🚚 FREE SHIP</div>
                                        <div class="text-muted" style="font-size: 0.75rem;">Orders $50+</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Product Info -->
                <div class="col-md-6">
                    <!-- Header -->
                    <div class="mb-3">
                        <div class="d-flex align-items-center gap-2 mb-2">
                            <span class="badge bg-success-subtle text-success fw-semibold">${product.category}</span>
                            <span class="text-muted">•</span>
                            <span class="text-muted fw-medium">${product.brand || 'Fresh Farm'}</span>
                        </div>
                        <h3 class="fw-bold text-dark mb-2">${product.name}</h3>
                        <p class="text-muted">${product.description}</p>
                    </div>
                    
                    <!-- Rating -->
                    <div class="bg-warning-subtle border border-warning-subtle rounded-3 p-3 mb-3">
                        <div class="d-flex align-items-center gap-3">
                            <div class="d-flex">${starsHtml}</div>
                            <span class="fw-medium">(${product.rating})</span>
                            <span class="text-muted small">${product.reviews || Math.floor(Math.random() * 50) + 20} reviews</span>
                            <div class="ms-auto d-flex align-items-center gap-2 text-success fw-bold">
                                <div class="bg-success rounded-circle" style="width: 8px; height: 8px;"></div>
                                ${product.inStock ? 'In Stock' : 'Out of Stock'}
                            </div>
                        </div>
                    </div>
                    
                    <!-- Price -->
                    <div class="bg-success-subtle border border-success rounded-3 p-4 mb-3">
                        <div class="text-center">
                            <div class="d-flex align-items-center justify-content-center gap-3 mb-2">
                                <span class="display-6 fw-bold text-success">${product.price.toFixed(2)}</span>
                                ${hasDiscount ? `<span class="h5 text-muted text-decoration-line-through">${product.originalPrice.toFixed(2)}</span>` : ''}
                            </div>
                            ${hasDiscount ? `
                                <div class="d-flex align-items-center justify-content-center gap-2">
                                    <span class="badge bg-danger">Save ${savings.toFixed(2)}</span>
                                    <span class="text-success fw-bold">${discountPercent}% off</span>
                                </div>
                            ` : '<div class="text-success fw-bold">🌟 Premium Quality Guaranteed</div>'}
                        </div>
                    </div>
                    
                    <!-- Product Features -->
                    <div class="mb-4">
                        <div class="d-flex align-items-center gap-2 mb-2 small">
                            <i class="bi bi-check-circle text-success"></i>
                            <span>100% Organic & Natural</span>
                        </div>
                        <div class="d-flex align-items-center gap-2 mb-2 small">
                            <i class="bi bi-check-circle text-success"></i>
                            <span>Farm Fresh & Pesticide Free</span>
                        </div>
                        <div class="d-flex align-items-center gap-2 small">
                            <i class="bi bi-check-circle text-success"></i>
                            <span>Sustainably Sourced</span>
                        </div>
                    </div>
                    
                    <!-- Quantity and Actions -->
                    <div>
                        <div class="d-flex align-items-center gap-3 mb-3">
                            <label class="small fw-medium text-dark">Quantity:</label>
                            <div class="input-group" style="width: 120px;">
                                <button class="btn btn-outline-secondary" type="button" onclick="adjustModalQuantity(-1)">
                                    <i class="bi bi-dash"></i>
                                </button>
                                <input type="number" id="modal-quantity" value="1" min="1" max="10" class="form-control text-center">
                                <button class="btn btn-outline-secondary" type="button" onclick="adjustModalQuantity(1)">
                                    <i class="bi bi-plus"></i>
                                </button>
                            </div>
                        </div>
                        
                        <div class="d-flex gap-2 mb-3">
                            <button onclick="addToCartFromModal()" class="btn btn-success flex-fill d-flex align-items-center justify-content-center gap-2">
                                <i class="bi bi-cart-plus"></i>
                                Add to Cart
                            </button>
                            <button onclick="addToWishlistFromModal()" class="btn btn-outline-secondary d-flex align-items-center justify-content-center" style="width: 50px;">
                                <i class="bi bi-heart"></i>
                            </button>
                        </div>
                        
                        <button onclick="viewProductDetails()" class="btn btn-outline-success w-100">
                            <i class="bi bi-eye me-2"></i>
                            View Full Details
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Modal action handlers
    window.adjustModalQuantity = function(change) {
        const quantityInput = document.getElementById('modal-quantity');
        if (quantityInput) {
            const currentValue = parseInt(quantityInput.value) || 1;
            const newValue = Math.max(1, Math.min(10, currentValue + change));
            quantityInput.value = newValue;
        }
    };
    
    window.addToCartFromModal = function() {
        if (!currentProductData) return;
        
        const quantity = parseInt(document.getElementById('modal-quantity')?.value) || 1;
        
        // Try to use existing cart function
        if (typeof addToCart === 'function') {
            for (let i = 0; i < quantity; i++) {
                addToCart(currentProductData.id);
            }
        }
        
        showToast(`Added ${quantity}x ${currentProductData.name} to cart!`, 'success');
        closeQuickView();
        
        console.log('✅ Added to cart from modal:', currentProductData.name, 'qty:', quantity);
    };
    
    window.addToWishlistFromModal = function() {
        if (!currentProductData) return;
        
        showToast(`Added ${currentProductData.name} to wishlist!`, 'success');
        console.log('✅ Added to wishlist from modal:', currentProductData.name);
    };
    
    window.viewProductDetails = function() {
        if (!currentProductData) return;
        
        closeQuickView();
        window.location.href = `product-details.html?id=${currentProductData.id}`;
    };
    
    // Bootstrap toast notification
    function showToast(message, type = 'success') {
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
        
        toastEl.innerHTML = `
            <div class="toast-body ${bgClass} text-white fw-medium d-flex align-items-center gap-2">
                <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
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
    
    // ESC key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && isQuickViewOpen) {
            closeQuickView();
        }
    });
    
    // Make functions globally available
    window.quickViewProduct = showQuickView;
    window.showQuickView = showQuickView;
    window.closeQuickView = closeQuickView;
    
    console.log('✅ Fixed quick view system loaded');
    
})();