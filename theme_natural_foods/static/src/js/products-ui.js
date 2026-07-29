/**
 * Products Page UI Interactions
 * Handles view toggles, mobile filters, quick view, and other UI interactions
 */

class ProductsUI {
    constructor() {
        this.currentView = 'grid';
        this.initialize();
    }

    initialize() {
        console.log('🎨 Initializing products UI...');
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeQuickView();
                if (window.ajaxCart) {
                    window.ajaxCart.hide();
                }
                this.closeMobileFilters();
            }
        });
    }

    // View toggle functionality
    toggleView(view) {
        this.currentView = view;
        
        // Update global currentView if it exists
        if (typeof currentView !== 'undefined') {
            window.currentView = view;
        }
        
        const gridBtn = document.getElementById('grid-view-btn');
        const listBtn = document.getElementById('list-view-btn');
        
        if (!gridBtn || !listBtn) return;
        
        if (view === 'grid') {
            gridBtn.classList.add('bg-green-600', 'text-white');
            gridBtn.classList.remove('bg-gray-200', 'text-gray-600');
            listBtn.classList.add('bg-gray-200', 'text-gray-600');
            listBtn.classList.remove('bg-green-600', 'text-white');
        } else {
            listBtn.classList.add('bg-green-600', 'text-white');
            listBtn.classList.remove('bg-gray-200', 'text-gray-600');
            gridBtn.classList.add('bg-gray-200', 'text-gray-600');
            gridBtn.classList.remove('bg-green-600', 'text-white');
        }
        
        // Update products display
        this.updateProductsView();
    }
    
    // Update products with current view
    updateProductsView() {
        const productsGrid = document.getElementById('products-grid');
        if (!productsGrid) return;
        
        // Update grid layout classes based on view
        if (this.currentView === 'list') {
            productsGrid.className = 'space-y-4';
        } else {
            productsGrid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6';
        }
        
        // Re-render products with new view if products exist
        const existingProducts = productsGrid.children;
        if (existingProducts.length > 0 && typeof filteredProducts !== 'undefined' && typeof createProductCard === 'function') {
            // Get sorted products
            let sortedProducts = [...filteredProducts];
            if (typeof applySorting === 'function') {
                sortedProducts = applySorting(sortedProducts);
            }
            
            // Generate product cards HTML with current view
            const productsHTML = sortedProducts.map(product => createProductCard(product, this.currentView)).join('');
            productsGrid.innerHTML = productsHTML;
            
            // Re-initialize icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            
            console.log(`✅ Updated view to ${this.currentView} with ${sortedProducts.length} products`);
        } else if (typeof updateProductsDisplay === 'function') {
            // Fallback to global update function
            updateProductsDisplay();
        }
    }

    // Mobile filters toggle
    toggleMobileFilters() {
        const sidebar = document.getElementById('filters-sidebar');
        if (!sidebar) return;
        
        const isVisible = !sidebar.classList.contains('hidden');
        
        if (isVisible) {
            this.closeMobileFilters();
        } else {
            this.openMobileFilters();
        }
    }

    openMobileFilters() {
        const sidebar = document.getElementById('filters-sidebar');
        if (!sidebar) return;
        
        sidebar.classList.remove('hidden');
        // Position sidebar as overlay on mobile
        sidebar.classList.add('fixed', 'top-0', 'left-0', 'w-full', 'h-full', 'bg-white', 'z-50', 'overflow-y-auto');
        
        // Add close button for mobile
        if (!document.getElementById('mobile-close-filters')) {
            const closeBtn = document.createElement('button');
            closeBtn.id = 'mobile-close-filters';
            closeBtn.className = 'absolute top-4 right-4 p-2 bg-gray-100 rounded-lg z-60';
            closeBtn.innerHTML = '<i data-lucide="x" class="h-5 w-5"></i>';
            closeBtn.onclick = () => this.toggleMobileFilters();
            sidebar.insertBefore(closeBtn, sidebar.firstChild);
            
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }

    closeMobileFilters() {
        const sidebar = document.getElementById('filters-sidebar');
        const closeBtn = document.getElementById('mobile-close-filters');
        
        if (sidebar && sidebar.classList.contains('fixed')) {
            sidebar.classList.add('hidden');
            sidebar.classList.remove('fixed', 'top-0', 'left-0', 'w-full', 'h-full', 'bg-white', 'z-50', 'overflow-y-auto');
        }
        
        if (closeBtn) {
            closeBtn.remove();
        }
    }

    // Quick view functionality
    showQuickView(productId) {
        console.log('🔍 Showing quick view for product:', productId);
        
        // Get product data
        const product = typeof productsData !== 'undefined' ? 
                       productsData.find(p => p.id == productId) : null;
        
        if (!product) {
            if (window.ajaxCart) {
                window.ajaxCart.showToast('Product not found', 'error');
            }
            return;
        }
        
        // Populate quick view content
        const content = document.getElementById('quick-view-content');
        if (!content) return;
        
        const hasDiscount = product.originalPrice && product.originalPrice > product.price;
        
        content.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <img src="${product.image}" alt="${product.name}" class="w-full h-80 object-cover rounded-lg">
                </div>
                <div class="space-y-6">
                    <div>
                        <h2 class="text-3xl font-bold text-gray-900 mb-2">${product.name}</h2>
                        <p class="text-gray-600">${product.description || 'Fresh organic product'}</p>
                    </div>
                    
                    <div class="flex items-center gap-2">
                        <div class="flex text-yellow-400">
                            ${Array(5).fill().map((_, i) => 
                                `<span class="${i < Math.floor(product.rating || 4.5) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                            ).join('')}
                        </div>
                        <span class="text-gray-600">(${product.rating || 4.5})</span>
                        <span class="text-gray-400 text-sm">${product.reviews || 25} reviews</span>
                    </div>
                    
                    <div class="space-y-2">
                        <div class="flex items-center gap-3">
                            <span class="text-3xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                            ${hasDiscount ? `<span class="text-xl text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${hasDiscount ? `<p class="text-red-600 font-semibold">Save $${(product.originalPrice - product.price).toFixed(2)} (${Math.round(((product.originalPrice - product.price) / product.originalPrice) * 100)}% off)</p>` : ''}
                    </div>
                    
                    <div class="space-y-4">
                        <button onclick="addToCart(${product.id}, {name: '${product.name}', price: ${product.price}, image: '${product.image}', description: '${(product.description || 'Fresh organic product').replace(/'/g, "\\'")}'}); window.productsUI.closeQuickView();" class="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:shadow-lg flex items-center justify-center gap-2">
                            <i data-lucide="shopping-cart" class="h-5 w-5"></i>
                            Add to Cart
                        </button>
                        <button onclick="window.productsUI.addToWishlist(${product.id})" class="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-semibold transition-all flex items-center justify-center gap-2">
                            <i data-lucide="heart" class="h-5 w-5"></i>
                            Add to Wishlist
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Show modal
        const modal = document.getElementById('quick-view-modal');
        if (modal) {
            modal.classList.remove('hidden');
            modal.classList.add('flex');
            document.body.style.overflow = 'hidden';
        }
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    closeQuickView() {
        const modal = document.getElementById('quick-view-modal');
        if (modal) {
            modal.classList.add('hidden');
            modal.classList.remove('flex');
            document.body.style.overflow = '';
        }
    }

    // Wishlist functionality
    addToWishlist(productId) {
        console.log('❤️ Adding product to wishlist:', productId);
        
        // Update wishlist count
        const wishlistCount = document.getElementById('wishlist-count');
        if (wishlistCount) {
            const currentCount = parseInt(wishlistCount.textContent) || 0;
            wishlistCount.textContent = currentCount + 1;
        }
        
        if (window.ajaxCart) {
            window.ajaxCart.showToast('Product added to wishlist!', 'success');
        }
    }

    // Search functionality
    performSearch() {
        const searchInput = document.getElementById('search-input');
        const query = searchInput ? searchInput.value.trim() : '';
        
        if (query) {
            console.log('🔍 Searching for:', query);
            if (window.ajaxCart) {
                window.ajaxCart.showToast(`Searching for "${query}"...`, 'info');
            }
            // In a real app, this would trigger the search
        }
    }

    // Get current view
    getCurrentView() {
        return this.currentView;
    }

    // Set view programmatically
    setView(view) {
        this.toggleView(view);
    }
}

// Global functions for backward compatibility
function toggleView(view) {
    if (window.productsUI) {
        window.productsUI.toggleView(view);
    }
}

function toggleMobileFilters() {
    if (window.productsUI) {
        window.productsUI.toggleMobileFilters();
    }
}

function showQuickView(productId) {
    if (window.productsUI) {
        window.productsUI.showQuickView(productId);
    }
}

function closeQuickView() {
    if (window.productsUI) {
        window.productsUI.closeQuickView();
    }
}

function addToWishlist(productId) {
    if (window.productsUI) {
        window.productsUI.addToWishlist(productId);
    }
}

function performSearch() {
    if (window.productsUI) {
        window.productsUI.performSearch();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.productsUI = new ProductsUI();
    console.log('✅ Products UI initialized');
});