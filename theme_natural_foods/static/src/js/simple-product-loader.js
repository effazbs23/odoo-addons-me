// Simple, reliable product loader for Natural Foods
console.log('🌱 Loading simple-product-loader.js...');

// Ensure this runs immediately when script loads
(function() {
    'use strict';
    
    // Product data - embedded directly for reliability
    const PRODUCTS = [
        // Vegetables
        {
            id: 1,
            name: "Organic Roma Tomatoes",
            price: 2.99,
            originalPrice: 4.99,
            rating: 4.8,
            description: "Fresh, vine-ripened organic tomatoes bursting with flavor.",
            image: "https://images.unsplash.com/photo-1546470427-e212b059c413?w=300&h=300&fit=crop",
            category: "vegetables",
            sale: true,
            isNew: false
        },
        {
            id: 2,
            name: "Organic Baby Spinach",
            price: 3.49,
            rating: 4.7,
            description: "Fresh organic baby spinach leaves, perfect for salads.",
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
            category: "vegetables",
            sale: false,
            isNew: true
        },
        {
            id: 3,
            name: "Organic Kale",
            price: 2.79,
            originalPrice: 3.99,
            rating: 4.6,
            description: "Nutrient-rich organic kale, perfect for smoothies.",
            image: "https://images.unsplash.com/photo-1515363578674-99baa5dee65b?w=300&h=300&fit=crop",
            category: "vegetables",
            sale: true,
            isNew: false
        },
        {
            id: 4,
            name: "Organic Carrots",
            price: 1.99,
            rating: 4.5,
            description: "Sweet, crunchy organic carrots grown with care.",
            image: "https://images.unsplash.com/photo-1447175008436-054170c2e979?w=300&h=300&fit=crop",
            category: "vegetables",
            sale: false,
            isNew: false
        },

        // Fruits
        {
            id: 5,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            rating: 4.9,
            description: "Sweet and crispy organic apples, perfect for snacking.",
            image: "https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=300&h=300&fit=crop",
            category: "fruits",
            sale: false,
            isNew: true
        },
        {
            id: 6,
            name: "Organic Blueberries",
            price: 6.99,
            originalPrice: 8.99,
            rating: 4.8,
            description: "Antioxidant-rich organic blueberries, bursting with flavor.",
            image: "https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=300&h=300&fit=crop",
            category: "fruits",
            sale: true,
            isNew: false
        },
        {
            id: 7,
            name: "Organic Bananas",
            price: 2.49,
            rating: 4.4,
            description: "Perfectly ripe organic bananas, great for breakfast.",
            image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop",
            category: "fruits",
            sale: false,
            isNew: false
        },
        {
            id: 8,
            name: "Organic Strawberries",
            price: 4.99,
            rating: 4.7,
            description: "Sweet, juicy organic strawberries picked at peak ripeness.",
            image: "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=300&h=300&fit=crop",
            category: "fruits",
            sale: false,
            isNew: true
        },

        // Dairy
        {
            id: 9,
            name: "Organic Whole Milk",
            price: 4.49,
            rating: 4.6,
            description: "Fresh organic whole milk from grass-fed cows.",
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
            category: "dairy",
            sale: false,
            isNew: false
        },
        {
            id: 10,
            name: "Organic Greek Yogurt",
            price: 5.99,
            originalPrice: 7.49,
            rating: 4.8,
            description: "Creamy organic Greek yogurt packed with protein.",
            image: "https://images.unsplash.com/photo-1488477181946-6428a0291777?w=300&h=300&fit=crop",
            category: "dairy",
            sale: true,
            isNew: false
        },
        {
            id: 11,
            name: "Organic Cheese Selection",
            price: 8.99,
            rating: 4.7,
            description: "Artisan organic cheese made from the finest milk.",
            image: "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=300&h=300&fit=crop",
            category: "dairy",
            sale: false,
            isNew: true
        },
        {
            id: 12,
            name: "Organic Butter",
            price: 6.49,
            rating: 4.5,
            description: "Rich, creamy organic butter from pasture-raised cows.",
            image: "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=300&h=300&fit=crop",
            category: "dairy",
            sale: false,
            isNew: false
        },

        // Bakery
        {
            id: 13,
            name: "Artisan Sourdough Bread",
            price: 4.99,
            rating: 4.8,
            description: "Handcrafted sourdough bread with a perfect crust.",
            image: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=300&h=300&fit=crop",
            category: "bakery",
            sale: false,
            isNew: false
        },
        {
            id: 14,
            name: "Organic Whole Grain Bread",
            price: 3.99,
            originalPrice: 5.49,
            rating: 4.6,
            description: "Nutritious whole grain bread made with organic flour.",
            image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
            category: "bakery",
            sale: true,
            isNew: false
        },
        {
            id: 15,
            name: "Organic Croissants",
            price: 6.99,
            rating: 4.7,
            description: "Buttery, flaky organic croissants baked fresh daily.",
            image: "https://images.unsplash.com/photo-1555507036-ab794f4cc849?w=300&h=300&fit=crop",
            category: "bakery",
            sale: false,
            isNew: true
        },
        {
            id: 16,
            name: "Organic Muffins",
            price: 2.99,
            rating: 4.4,
            description: "Delicious organic muffins made with fresh ingredients.",
            image: "https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=300&h=300&fit=crop",
            category: "bakery",
            sale: false,
            isNew: false
        }
    ];

    // Recipe data
    const RECIPES = [
        {
            id: 1,
            title: "Fresh Garden Salad",
            description: "A vibrant mix of organic greens, tomatoes, and vegetables tossed in a light vinaigrette.",
            image: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
            cookTime: "15 mins",
            difficulty: "Easy",
            servings: 4,
            category: "Salads"
        },
        {
            id: 2,
            title: "Organic Berry Smoothie",
            description: "A nutritious blend of organic berries, yogurt, and honey for the perfect morning boost.",
            image: "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=400&h=300&fit=crop",
            cookTime: "5 mins",
            difficulty: "Easy",
            servings: 2,
            category: "Smoothies"
        },
        {
            id: 3,
            title: "Roasted Vegetable Medley",
            description: "Colorful organic vegetables roasted to perfection with herbs and olive oil.",
            image: "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop",
            cookTime: "45 mins",
            difficulty: "Medium",
            servings: 6,
            category: "Main Course"
        }
    ];

    // Create product card HTML - UPDATED WITHOUT "VIEW DETAILS" BUTTON AND WITH CLICKABLE TITLE
    function createProductCard(product) {
        const originalPrice = product.originalPrice;
        const hasDiscount = originalPrice && originalPrice > product.price;
        
        return `
            <div class="product-card bg-white border border-gray-200 rounded-2xl overflow-hidden transition-all duration-400 hover:shadow-xl hover:-translate-y-2 relative group">
                <div class="relative overflow-hidden rounded-t-2xl">
                    <img src="${product.image}" alt="${product.name}" class="w-full h-56 object-cover group-hover:scale-110 transition-transform duration-500">
                    
                    ${product.sale ? '<div class="absolute top-4 left-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">🔥 SALE</div>' : ''}
                    ${product.isNew ? '<div class="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">✨ NEW</div>' : ''}
                    
                    <!-- Action Buttons Overlay -->
                    <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end justify-center pb-6">
                        <div class="flex gap-3">
                            <button onclick="event.stopPropagation(); addToWishlist(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-red-500 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Add to Wishlist">
                                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                </svg>
                            </button>
                            <button onclick="event.stopPropagation(); quickViewProduct(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-green-600 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Quick View">
                                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="p-6 space-y-4">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 group-hover:text-green-600 transition-colors line-clamp-2 cursor-pointer" onclick="window.location.href='product-details.html?id=${product.id}'">${product.name}</h3>
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
                                ${hasDiscount ? `<span class="text-lg text-gray-500 line-through">$${originalPrice.toFixed(2)}</span>` : ''}
                            </div>
                            ${hasDiscount ? `<span class="text-sm text-red-600 font-semibold">Save $${(originalPrice - product.price).toFixed(2)} (${Math.round(((originalPrice - product.price) / originalPrice) * 100)}% off)</span>` : '<span class="text-sm text-green-600 font-semibold">Premium quality</span>'}
                        </div>
                        <button onclick="event.stopPropagation(); addToCart(${product.id})" class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:shadow-lg flex items-center gap-2">
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5H19"></path>
                            </svg>
                            ADD
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Create recipe card HTML
    function createRecipeCard(recipe) {
        return `
            <div class="recipe-card bg-white rounded-2xl overflow-hidden shadow-lg group cursor-pointer hover:shadow-2xl transition-all duration-300" onclick="window.location.href='recipe-details.html?id=${recipe.id}'">
                <div class="relative overflow-hidden">
                    <img src="${recipe.image}" alt="${recipe.title}" class="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500">
                    <div class="absolute top-4 left-4 bg-green-600 text-white px-3 py-1 rounded-full text-sm font-semibold">
                        ${recipe.category}
                    </div>
                    <div class="absolute top-4 right-4 bg-white/90 backdrop-blur-sm text-gray-700 px-3 py-1 rounded-full text-sm font-semibold">
                        <svg class="h-3 w-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12,6 12,12 16,14"></polyline>
                        </svg>
                        ${recipe.cookTime}
                    </div>
                </div>
                <div class="p-6">
                    <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-green-600 transition-colors">${recipe.title}</h3>
                    <p class="text-gray-600 mb-4 leading-relaxed">${recipe.description}</p>
                    <div class="flex items-center justify-between text-sm text-gray-500">
                        <div class="flex items-center gap-4">
                            <span class="flex items-center gap-1">
                                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"></path>
                                </svg>
                                ${recipe.servings} servings
                            </span>
                            <span class="flex items-center gap-1">
                                <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"></path>
                                </svg>
                                ${recipe.difficulty}
                            </span>
                        </div>
                        <button class="text-green-600 hover:text-green-700 font-semibold flex items-center gap-1">
                            View Recipe 
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // Load products into sections
    function loadProducts() {
        console.log('🌱 Loading products into all sections...');

        try {
            // 1. Hot Deals Section
            const hotDealsContainer = document.getElementById('hot-deals');
            if (hotDealsContainer) {
                const saleProducts = PRODUCTS.filter(p => p.sale).slice(0, 4);
                hotDealsContainer.innerHTML = saleProducts.map(createProductCard).join('');
                console.log('✅ Hot deals loaded:', saleProducts.length, 'products');
            }

            // 2. New Arrivals Section  
            const newArrivalsContainer = document.getElementById('new-arrivals');
            if (newArrivalsContainer) {
                const newProducts = PRODUCTS.filter(p => p.isNew).slice(0, 4);
                newArrivalsContainer.innerHTML = newProducts.map(createProductCard).join('');
                console.log('✅ New arrivals loaded:', newProducts.length, 'products');
            }

            // 3. Featured Products Section
            const featuredContainer = document.getElementById('featured-products');
            if (featuredContainer) {
                const featuredProducts = PRODUCTS.filter(p => p.rating >= 4.7).slice(0, 4);
                featuredContainer.innerHTML = featuredProducts.map(createProductCard).join('');
                console.log('✅ Featured products loaded:', featuredProducts.length, 'products');
            }

            // 4. Product Tabs Section - Default to vegetables
            loadTabProducts('vegetables');

            // 5. Recipe Section
            const recipeContainer = document.getElementById('recipe-section');
            if (recipeContainer) {
                recipeContainer.innerHTML = RECIPES.map(createRecipeCard).join('');
                console.log('✅ Recipes loaded:', RECIPES.length, 'recipes');
            }

        } catch (error) {
            console.error('❌ Error loading products:', error);
        }
    }

    // Load products for specific tab
    function loadTabProducts(category) {
        console.log('🏷️ Loading tab products for:', category);
        
        const container = document.getElementById('tab-products');
        if (!container) {
            console.error('❌ Tab products container not found');
            return;
        }

        // Update tab button states
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
            btn.classList.add('text-gray-600');
        });
        
        const activeBtn = document.getElementById(`tab-${category}`);
        if (activeBtn) {
            activeBtn.classList.add('active');
            activeBtn.classList.remove('text-gray-600');
        }

        // Update tab image
        updateTabImage(category);

        // Filter and display products
        const categoryProducts = PRODUCTS.filter(p => p.category === category).slice(0, 4);
        
        if (categoryProducts.length > 0) {
            container.innerHTML = categoryProducts.map(createProductCard).join('');
            console.log(`✅ Tab products loaded for ${category}:`, categoryProducts.length, 'products');
        } else {
            container.innerHTML = `<div class="col-span-4 text-center text-gray-500 py-8">No ${category} available</div>`;
        }
    }

    // Update tab image based on category
    function updateTabImage(category) {
        const tabData = {
            vegetables: {
                image: "https://images.unsplash.com/photo-1657288089316-c0350003ca49?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHZlZ2V0YWJsZXMlMjBvcmdhbmljfGVufDF8fHx8MTc1NTY3MzY2N3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
                icon: "🥬",
                title: "Vegetables"
            },
            fruits: {
                image: "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=280&fit=crop",
                icon: "🍎", 
                title: "Fruits"
            },
            dairy: {
                image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=280&fit=crop",
                icon: "🥛",
                title: "Dairy"
            },
            bakery: {
                image: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=400&h=280&fit=crop",
                icon: "🍞",
                title: "Bakery"
            }
        };

        const data = tabData[category];
        if (!data) return;

        const tabImage = document.getElementById('tab-image');
        const tabIcon = document.getElementById('tab-icon');
        const tabTitle = document.getElementById('tab-title');

        if (tabImage) tabImage.src = data.image;
        if (tabIcon) tabIcon.textContent = data.icon;
        if (tabTitle) tabTitle.textContent = data.title;
    }

    // Product interaction functions
    window.addToCart = function(productId) {
        const product = PRODUCTS.find(p => p.id === productId);
        if (product) {
            showToast(`Added ${product.name} to cart!`, 'success');
            console.log('🛒 Added to cart:', product.name);
        }
    };

    window.addToWishlist = function(productId) {
        const product = PRODUCTS.find(p => p.id === productId);
        if (product) {
            showToast(`Added ${product.name} to wishlist!`, 'success');
            console.log('❤️ Added to wishlist:', product.name);
        }
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
        
        setTimeout(() => toast.classList.remove('translate-x-full'), 100);
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 3000);
    }

    // Make tab function globally available
    window.setActiveTab = function(category) {
        loadTabProducts(category);
    };

    // Make products globally available for quick view
    window.PRODUCTS = PRODUCTS;
    window.getAllProducts = function() {
        return PRODUCTS;
    };

    // Initialize when DOM is ready
    function initialize() {
        console.log('🚀 Simple product loader initializing...');
        
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', loadProducts);
        } else {
            loadProducts();
        }
    }

    // Start initialization
    initialize();

    console.log('✅ Simple product loader ready');

})();