// Enhanced Quick View Functionality
class QuickView {
    constructor() {
        this.modal = null;
        this.content = null;
        this.currentQuantity = 1;
        this.init();
    }

    init() {
        this.createModal();
        console.log('✅ Quick View initialized');
    }

    createModal() {
        // Remove existing modal if any
        const existingModal = document.getElementById('quick-view-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // Create modal
        this.modal = document.createElement('div');
        this.modal.id = 'quick-view-modal';
        this.modal.className = 'fixed inset-0 quick-view-backdrop hidden flex items-center justify-center p-4 z-50';
        this.modal.onclick = (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        };

        // Create content container
        this.content = document.createElement('div');
        this.content.id = 'quick-view-content';
        this.content.className = 'quick-view-modal rounded-3xl max-w-6xl w-full max-h-[90vh] overflow-y-auto modal-animate-in';
        this.content.onclick = (e) => e.stopPropagation();

        this.modal.appendChild(this.content);
        document.body.appendChild(this.modal);
    }

    getProductData(productId) {
        const id = parseInt(productId);

        // Try multiple sources for product data
        const sources = [
            () => typeof getAllProducts === 'function' ? getAllProducts().find(p => p.id === id) : null,
            () => typeof window.products !== 'undefined' ? window.products.find(p => p.id === id) : null,
            () => typeof window.enhancedProducts !== 'undefined' ? window.enhancedProducts.find(p => p.id === id) : null
        ];

        for (const source of sources) {
            const product = source();
            if (product) return product;
        }

        // Fallback mock data
        const mockProducts = {
            1: {
                id: 1,
                name: "Organic Roma Tomatoes",
                price: 2.99,
                originalPrice: 4.99,
                rating: 4.8,
                description: "Fresh, vine-ripened organic tomatoes bursting with flavor. Perfect for salads, cooking, or eating fresh.",
                image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=600&h=600&fit=crop",
                category: "vegetables",
                brand: "Fresh Farm",
                sale: true
            },
            2: {
                id: 2,
                name: "Organic Honey Crisp Apples",
                price: 5.99,
                rating: 4.9,
                description: "Sweet and crispy organic apples, perfect for snacking or baking.",
                image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=600&h=600&fit=crop",
                category: "fruits",
                brand: "Orchard Fresh",
                isNew: true
            },
            3: {
                id: 3,
                name: "Organic Baby Spinach",
                price: 3.49,
                rating: 4.7,
                description: "Fresh organic baby spinach leaves, perfect for salads and smoothies.",
                image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&h=600&fit=crop",
                category: "vegetables",
                brand: "Green Leaf"
            }
        };

        return mockProducts[id] || mockProducts[1];
    }

    show(productId) {
        console.log('🔍 Quick View triggered for product:', productId);

        const product = this.getProductData(productId);
        if (!product) {
            console.error('❌ Product not found:', productId);
            return;
        }

        console.log('✅ Product found:', product.name);

        const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
        const salePercentage = savings > 0 ? Math.round((savings / product.originalPrice) * 100) : 0;

        this.content.innerHTML = `
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
        this.modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';

        // Re-initialize Lucide icons
        setTimeout(() => {
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }, 100);

        // Reset quantity
        this.currentQuantity = 1;
    }

    close() {
        if (this.modal) {
            this.modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
        this.currentQuantity = 1;
    }

    increaseQuantity() {
        this.currentQuantity++;
        const quantityEl = document.getElementById('quick-view-quantity');
        if (quantityEl) {
            quantityEl.textContent = this.currentQuantity;
        }
    }

    decreaseQuantity() {
        if (this.currentQuantity > 1) {
            this.currentQuantity--;
            const quantityEl = document.getElementById('quick-view-quantity');
            if (quantityEl) {
                quantityEl.textContent = this.currentQuantity;
            }
        }
    }

    addToCart(productId) {
        // Add multiple items based on quantity
        for (let i = 0; i < this.currentQuantity; i++) {
            if (typeof addToCart === 'function') {
                addToCart(productId);
            }
        }

        // Show notification
        const product = this.getProductData(productId);
        const message = `Added ${this.currentQuantity} x ${product.name} to cart!`;
        
        if (typeof showNotification === 'function') {
            showNotification(message, 'success');
        } else {
            alert(message);
        }

        // Reset quantity
        this.currentQuantity = 1;
    }
}

// Global instance
let quickViewInstance = null;

// Global functions for HTML onclick handlers
function quickViewProduct(productId) {
    if (!quickViewInstance) {
        quickViewInstance = new QuickView();
    }
    quickViewInstance.show(productId);
}

function closeQuickView() {
    if (quickViewInstance) {
        quickViewInstance.close();
    }
}

function quickViewIncreaseQuantity() {
    if (quickViewInstance) {
        quickViewInstance.increaseQuantity();
    }
}

function quickViewDecreaseQuantity() {
    if (quickViewInstance) {
        quickViewInstance.decreaseQuantity();
    }
}

function quickViewAddToCart(productId) {
    if (quickViewInstance) {
        quickViewInstance.addToCart(productId);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    quickViewInstance = new QuickView();
});

// Make functions globally available
window.quickViewProduct = quickViewProduct;
window.closeQuickView = closeQuickView;
window.quickViewIncreaseQuantity = quickViewIncreaseQuantity;
window.quickViewDecreaseQuantity = quickViewDecreaseQuantity;
window.quickViewAddToCart = quickViewAddToCart;

console.log('✅ Quick View module loaded');