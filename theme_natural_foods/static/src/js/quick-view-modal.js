// Quick View Modal System for Natural Foods Static HTML
console.log('🔍 Loading quick-view-modal.js...');

(function() {
    'use strict';
    
    // Modal state
    let currentProduct = null;
    let modalElement = null;
    
    // Create modal HTML
    function createModalHTML() {
        return `
            <div id="quick-view-modal" class="fixed inset-0 z-50 hidden">
                <!-- Backdrop -->
                <div class="fixed inset-0 bg-black/75 backdrop-blur-sm transition-opacity" onclick="closeQuickView()"></div>
                
                <!-- Modal Content -->
                <div class="fixed inset-0 z-10 overflow-y-auto">
                    <div class="flex min-h-full items-center justify-center p-4">
                        <div class="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
                            <!-- Close Button -->
                            <button onclick="closeQuickView()" class="absolute top-4 right-4 z-20 bg-white/80 hover:bg-white text-gray-600 hover:text-gray-900 rounded-full p-2 transition-all shadow-lg">
                                <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                </svg>
                            </button>
                            
                            <!-- Modal Body -->
                            <div id="modal-content" class="grid grid-cols-1 lg:grid-cols-2 gap-8 p-8">
                                <!-- Content will be inserted here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Initialize modal
    function initializeModal() {
        if (document.getElementById('quick-view-modal')) return;
        
        const modalHTML = createModalHTML();
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        modalElement = document.getElementById('quick-view-modal');
        
        console.log('✅ Quick view modal initialized');
    }
    
    // Show quick view modal
    function showQuickView(productId) {
        console.log('🔍 Opening quick view for product:', productId);
        
        // Get product data
        const product = getProductById(productId);
        if (!product) {
            console.error('❌ Product not found:', productId);
            return;
        }
        
        currentProduct = product;
        
        // Initialize modal if not exists
        initializeModal();
        
        // Populate modal content
        populateModalContent(product);
        
        // Show modal
        modalElement.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        console.log('✅ Quick view modal opened');
    }
    
    // Close quick view modal
    function closeQuickView() {
        if (!modalElement) return;
        
        modalElement.classList.add('hidden');
        document.body.style.overflow = '';
        currentProduct = null;
        
        console.log('✅ Quick view modal closed');
    }
    
    // Populate modal with product data
    function populateModalContent(product) {
        const modalContent = document.getElementById('modal-content');
        if (!modalContent) return;
        
        const hasDiscount = product.originalPrice && product.originalPrice > product.price;
        const savings = hasDiscount ? (product.originalPrice - product.price) : 0;
        const discountPercent = hasDiscount ? Math.round((savings / product.originalPrice) * 100) : 0;
        
        modalContent.innerHTML = `
            <!-- Product Image -->
            <div class="relative">
                <div class="aspect-square bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl overflow-hidden">
                    <img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover">
                </div>
                
                <!-- Badges -->
                <div class="absolute top-4 left-4 flex flex-col gap-2">
                    ${product.sale ? '<div class="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">🔥 SALE</div>' : ''}
                    ${product.isNew ? '<div class="bg-blue-500 text-white px-3 py-1 rounded-full text-sm font-bold">✨ NEW</div>' : ''}
                </div>
            </div>
            
            <!-- Product Info -->
            <div class="space-y-6">
                <div>
                    <h2 class="text-3xl font-bold text-gray-900 mb-2">${product.name}</h2>
                    <p class="text-gray-600 leading-relaxed">${product.description}</p>
                </div>
                
                <!-- Rating -->
                <div class="flex items-center gap-2">
                    <div class="flex text-yellow-400 text-lg">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="text-gray-600 font-medium">(${product.rating})</span>
                    <span class="text-gray-400 text-sm">${Math.floor(Math.random() * 50) + 20} reviews</span>
                </div>
                
                <!-- Price -->
                <div class="space-y-2">
                    <div class="flex items-center gap-3">
                        <span class="text-3xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                        ${hasDiscount ? `<span class="text-xl text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                    </div>
                    ${hasDiscount ? `<div class="text-red-600 font-semibold">Save $${savings.toFixed(2)} (${discountPercent}% off)</div>` : ''}
                </div>
                
                <!-- Product Features -->
                <div class="space-y-3">
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        100% Organic & Natural
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        Farm Fresh & Pesticide Free
                    </div>
                    <div class="flex items-center gap-2 text-sm text-gray-600">
                        <svg class="h-4 w-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        Sustainably Sourced
                    </div>
                </div>
                
                <!-- Quantity and Actions -->
                <div class="space-y-4">
                    <div class="flex items-center gap-4">
                        <label class="text-sm font-medium text-gray-700">Quantity:</label>
                        <div class="flex items-center border border-gray-300 rounded-lg">
                            <button onclick="adjustQuantity(-1)" class="px-3 py-2 hover:bg-gray-50 text-gray-600">−</button>
                            <input type="number" id="modal-quantity" value="1" min="1" class="w-16 text-center border-0 focus:ring-0">
                            <button onclick="adjustQuantity(1)" class="px-3 py-2 hover:bg-gray-50 text-gray-600">+</button>
                        </div>
                    </div>
                    
                    <div class="flex gap-3">
                        <button onclick="addToCartFromModal()" class="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:shadow-lg flex items-center justify-center gap-2">
                            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5H19"></path>
                            </svg>
                            Add to Cart
                        </button>
                        <button onclick="addToWishlistFromModal()" class="bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-red-500 px-4 py-3 rounded-xl transition-all flex items-center justify-center">
                            <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <button onclick="viewProductDetails()" class="w-full bg-white border-2 border-green-600 text-green-600 hover:bg-green-50 px-6 py-3 rounded-xl font-semibold transition-all">
                        View Full Details
                    </button>
                </div>
            </div>
        `;
    }
    
    // Get product by ID
    function getProductById(productId) {
        // Try multiple data sources
        let products = [];
        
        // Check productsData from products-page-consistent.js
        if (typeof productsData !== 'undefined') {
            products = productsData;
        }
        // Check window.getAllProducts function
        else if (typeof window.getAllProducts === 'function') {
            products = window.getAllProducts();
        }
        // Fallback to simple-product-loader data if available
        else if (typeof window.PRODUCTS !== 'undefined') {
            products = window.PRODUCTS;
        }
        
        if (products.length > 0) {
            return products.find(p => p.id == productId);
        }
        
        console.error('❌ No product data available for ID:', productId);
        return null;
    }
    
    // Modal action handlers
    window.adjustQuantity = function(change) {
        const quantityInput = document.getElementById('modal-quantity');
        if (quantityInput) {
            const currentValue = parseInt(quantityInput.value) || 1;
            const newValue = Math.max(1, currentValue + change);
            quantityInput.value = newValue;
        }
    };
    
    window.addToCartFromModal = function() {
        if (!currentProduct) return;
        
        const quantity = parseInt(document.getElementById('modal-quantity')?.value) || 1;
        
        // Show success message
        showToast(`Added ${quantity}x ${currentProduct.name} to cart!`, 'success');
        
        // Close modal
        closeQuickView();
        
        console.log('✅ Added to cart from modal:', currentProduct.name, 'qty:', quantity);
    };
    
    window.addToWishlistFromModal = function() {
        if (!currentProduct) return;
        
        showToast(`Added ${currentProduct.name} to wishlist!`, 'success');
        console.log('✅ Added to wishlist from modal:', currentProduct.name);
    };
    
    window.viewProductDetails = function() {
        if (!currentProduct) return;
        
        closeQuickView();
        window.location.href = `product-details.html?id=${currentProduct.id}`;
    };
    
    // Toast notification system
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg text-white font-medium transform transition-all duration-300 translate-x-full`;
        
        if (type === 'success') {
            toast.classList.add('bg-green-600');
        } else if (type === 'error') {
            toast.classList.add('bg-red-600');
        } else {
            toast.classList.add('bg-blue-600');
        }
        
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // Show toast
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Hide toast
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    // Make functions globally available
    window.quickViewProduct = showQuickView;
    window.closeQuickView = closeQuickView;
    window.showQuickView = showQuickView;
    
    // ESC key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modalElement && !modalElement.classList.contains('hidden')) {
            closeQuickView();
        }
    });
    
    console.log('✅ Quick view modal system loaded');
    
})();