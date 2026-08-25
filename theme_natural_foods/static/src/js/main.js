// Main application coordinator for Natural Foods Organic Store
console.log('🌱 Loading main.js...');

// Global state
let currentActiveTab = 'vegetables';
let allProducts = [];
let allRecipes = [];
let isApplicationInitialized = false;

// Initialize the application
function initializeOrganicStore() {
    console.log('🌱 Initializing Natural Foods Organic Store...');
    
    if (isApplicationInitialized) {
        console.log('⚠️ Application already initialized');
        return;
    }
    
    try {
        // Check if we're on the home page
        const isHomePage = window.location.pathname === '/' || window.location.pathname.includes('index.html');
        
        if (!isHomePage) {
            console.log('📍 Not on home page, skipping home page initialization');
            return;
        }
        
        console.log('🏠 Initializing home page...');
        
        // Load all data first
        loadProducts();
        loadRecipes();
        
        // Wait a moment for DOM to be fully ready, then initialize sections
        setTimeout(() => {
            initializeAllSections();
        }, 100);
        
        isApplicationInitialized = true;
        console.log('✅ Application initialized successfully');
    } catch (error) {
        console.error('❌ Error initializing application:', error);
    }
}

// Initialize all sections
function initializeAllSections() {
    console.log('🔧 Initializing all sections...');
    
    try {
        // Initialize sections in order
        initializeHotDeals();
        initializeNewArrivals();  
        initializeFeaturedProducts();
        initializeProductTabs();
        initializeRecipeSection();
        
        // Initialize interactive systems
        initializeCartSystem();
        initializeWishlistSystem();
        
        console.log('✅ All sections initialized');
    } catch (error) {
        console.error('❌ Error initializing sections:', error);
    }
}

// Load products data
function loadProducts() {
    console.log('📦 Loading products...');
    
    try {
        // Try to get products from products-data.js
        if (typeof getAllProducts === 'function') {
            allProducts = getAllProducts();
            console.log(`✅ Loaded ${allProducts.length} products from data file`);
        } else {
            console.log('⚠️ getAllProducts function not found, using mock data');
            allProducts = getMockProducts();
            console.log(`✅ Loaded ${allProducts.length} mock products`);
        }
        
        // Log first few products for debugging
        console.log('📋 Sample products:', allProducts.slice(0, 3));
        
    } catch (error) {
        console.error('❌ Error loading products:', error);
        allProducts = getMockProducts();
    }
}

// Mock products data with more comprehensive data
function getMockProducts() {
    console.log('🔄 Creating mock products...');
    
    return [
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
            description: "Fresh organic baby spinach leaves, perfect for salads and smoothies.",
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
            description: "Nutrient-rich organic kale, perfect for smoothies and salads.",
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
}

// Load recipes data
function loadRecipes() {
    console.log('🍽️ Loading recipes...');
    
    try {
        // Try to get recipes from recipe-data.js
        if (typeof getAllRecipes === 'function') {
            allRecipes = getAllRecipes();
            console.log(`✅ Loaded ${allRecipes.length} recipes from data file`);
        } else {
            console.log('⚠️ getAllRecipes function not found, using mock data');
            allRecipes = getMockRecipes();
            console.log(`✅ Loaded ${allRecipes.length} mock recipes`);
        }
        
        // Log first few recipes for debugging
        console.log('📋 Sample recipes:', allRecipes.slice(0, 2));
        
    } catch (error) {
        console.error('❌ Error loading recipes:', error);
        allRecipes = getMockRecipes();
    }
}

// Mock recipes data
function getMockRecipes() {
    console.log('🔄 Creating mock recipes...');
    
    return [
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
}

// Initialize Hot Deals section
function initializeHotDeals() {
    console.log('🔥 Loading hot deals...');
    
    const container = document.getElementById('hot-deals');
    if (!container) {
        console.error('❌ Hot deals container not found');
        return;
    }
    
    const saleProducts = allProducts.filter(product => product.sale).slice(0, 4);
    console.log(`📦 Found ${saleProducts.length} sale products`);
    
    if (saleProducts.length === 0) {
        container.innerHTML = '<div class="col-span-4 text-center text-gray-500">No hot deals available at the moment.</div>';
        return;
    }
    
    container.innerHTML = saleProducts.map(product => 
        createProductCard(product)
    ).join('');
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log(`✅ Loaded ${saleProducts.length} hot deals`);
}

// Initialize New Arrivals section
function initializeNewArrivals() {
    console.log('✨ Loading new arrivals...');
    
    const container = document.getElementById('new-arrivals');
    if (!container) {
        console.error('❌ New arrivals container not found');
        return;
    }
    
    const newProducts = allProducts.filter(product => product.isNew).slice(0, 4);
    console.log(`📦 Found ${newProducts.length} new products`);
    
    if (newProducts.length === 0) {
        container.innerHTML = '<div class="col-span-4 text-center text-gray-500">No new arrivals at the moment.</div>';
        return;
    }
    
    container.innerHTML = newProducts.map(product => 
        createProductCard(product)
    ).join('');
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log(`✅ Loaded ${newProducts.length} new arrivals`);
}

// Initialize Featured Products section
function initializeFeaturedProducts() {
    console.log('⭐ Loading featured products...');
    
    const container = document.getElementById('featured-products');
    if (!container) {
        console.error('❌ Featured products container not found');
        return;
    }
    
    const featuredProducts = allProducts.filter(product => product.rating >= 4.7).slice(0, 4);
    console.log(`📦 Found ${featuredProducts.length} featured products`);
    
    if (featuredProducts.length === 0) {
        container.innerHTML = '<div class="col-span-4 text-center text-gray-500">No featured products available.</div>';
        return;
    }
    
    container.innerHTML = featuredProducts.map(product => 
        createProductCard(product)
    ).join('');
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log(`✅ Loaded ${featuredProducts.length} featured products`);
}

// Initialize product tabs - THIS IS THE KEY FIX FOR "OUR PRODUCTS"
function initializeProductTabs() {
    console.log('🏷️ Initializing product tabs...');
    
    // Check if tab containers exist
    const tabContainer = document.getElementById('tab-products');
    if (!tabContainer) {
        console.error('❌ Tab products container (#tab-products) not found');
        return;
    }
    
    console.log('✅ Tab container found, setting default tab');
    
    // Set default active tab to vegetables
    setActiveTab('vegetables');
}

// Set active product tab - ENHANCED VERSION
function setActiveTab(category) {
    console.log(`🏷️ Setting active tab: ${category}`);
    
    currentActiveTab = category;
    
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.getElementById(`tab-${category}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
        console.log(`✅ Active tab button updated: ${category}`);
    } else {
        console.error(`❌ Tab button not found: tab-${category}`);
    }
    
    // Update tab image and content
    updateTabImage(category);
    loadTabProducts(category);
}

// Update tab image based on category
function updateTabImage(category) {
    const tabData = {
        vegetables: {
            image: "https://images.unsplash.com/photo-1657288089316-c0350003ca49?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxmcmVzaCUyMHZlZ2V0YWJsZXMlMjBvcmdhbmljfGVufDF8fHx8MTc1NTY3MzY2N3ww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
            icon: "🥬",
            title: "Vegetables",
            description: "Fresh & Organic"
        },
        fruits: {
            image: "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=280&fit=crop",
            icon: "🍎",
            title: "Fruits",
            description: "Sweet & Juicy"
        },
        dairy: {
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&h=280&fit=crop",
            icon: "🥛",
            title: "Dairy",
            description: "Fresh & Pure"
        },
        bakery: {
            image: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=400&h=280&fit=crop",
            icon: "🍞",
            title: "Bakery",
            description: "Fresh Baked"
        }
    };
    
    const data = tabData[category];
    if (!data) {
        console.error(`❌ No tab data found for category: ${category}`);
        return;
    }
    
    // Update image
    const tabImage = document.getElementById('tab-image');
    if (tabImage) {
        tabImage.src = data.image;
        tabImage.alt = data.title;
    }
    
    // Update icon
    const tabIcon = document.getElementById('tab-icon');
    if (tabIcon) {
        tabIcon.textContent = data.icon;
    }
    
    // Update title
    const tabTitle = document.getElementById('tab-title');
    if (tabTitle) {
        tabTitle.textContent = data.title;
    }
    
    console.log(`✅ Tab image updated for: ${category}`);
}

// Load products for active tab - ENHANCED VERSION WITH BETTER DEBUGGING
function loadTabProducts(category) {
    console.log(`📦 Loading products for category: ${category}`);
    
    const container = document.getElementById('tab-products');
    if (!container) {
        console.error('❌ Tab products container not found');
        return;
    }
    
    // Filter products by category
    const categoryProducts = allProducts.filter(product => {
        console.log(`🔍 Checking product: ${product.name}, category: ${product.category}`);
        return product.category === category;
    }).slice(0, 4); // Show only 4 products
    
    console.log(`📊 Found ${categoryProducts.length} products for category: ${category}`);
    console.log('📋 Category products:', categoryProducts);
    
    if (categoryProducts.length === 0) {
        container.innerHTML = `
            <div class="col-span-4 text-center text-gray-500 py-8">
                <p class="text-lg">No products found for ${category}</p>
                <p class="text-sm mt-2">Available categories: ${allProducts.map(p => p.category).filter((v, i, a) => a.indexOf(v) === i).join(', ')}</p>
            </div>
        `;
        return;
    }
    
    // Generate product cards
    const productCards = categoryProducts.map(product => {
        console.log(`🏷️ Creating card for: ${product.name}`);
        return createProductCard(product);
    }).join('');
    
    container.innerHTML = productCards;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log(`✅ Loaded ${categoryProducts.length} products for ${category}`);
}

// Initialize Recipe section - ENHANCED VERSION
function initializeRecipeSection() {
    console.log('🍽️ Loading recipes section...');
    
    const container = document.getElementById('recipe-section');
    if (!container) {
        console.error('❌ Recipe section container (#recipe-section) not found');
        return;
    }
    
    console.log(`📊 Total recipes available: ${allRecipes.length}`);
    
    const featuredRecipes = allRecipes.slice(0, 3);
    console.log(`📋 Featured recipes:`, featuredRecipes);
    
    if (featuredRecipes.length === 0) {
        container.innerHTML = '<div class="col-span-3 text-center text-gray-500 py-8">No recipes available at the moment.</div>';
        return;
    }
    
    const recipeCards = featuredRecipes.map(recipe => {
        console.log(`🍽️ Creating recipe card for: ${recipe.title}`);
        return createRecipeCard(recipe);
    }).join('');
    
    container.innerHTML = recipeCards;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log(`✅ Loaded ${featuredRecipes.length} recipes`);
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
                    <i data-lucide="clock" class="h-3 w-3 inline mr-1"></i>
                    ${recipe.cookTime}
                </div>
            </div>
            <div class="p-6">
                <h3 class="text-xl font-bold text-gray-900 mb-3 group-hover:text-green-600 transition-colors">${recipe.title}</h3>
                <p class="text-gray-600 mb-4 leading-relaxed">${recipe.description}</p>
                <div class="flex items-center justify-between text-sm text-gray-500">
                    <div class="flex items-center gap-4">
                        <span class="flex items-center gap-1">
                            <i data-lucide="users" class="h-4 w-4"></i>
                            ${recipe.servings} servings
                        </span>
                        <span class="flex items-center gap-1">
                            <i data-lucide="chef-hat" class="h-4 w-4"></i>
                            ${recipe.difficulty}
                        </span>
                    </div>
                    <button class="text-green-600 hover:text-green-700 font-semibold flex items-center gap-1">
                        View Recipe <i data-lucide="arrow-right" class="h-4 w-4"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Create product card HTML (enhanced version)
function createProductCard(product) {
    const salePrice = product.originalPrice ? product.price : null;
    const originalPrice = product.originalPrice;
    
    return `
        <div class="product-card bg-white border border-gray-200 rounded-2xl overflow-hidden transition-all duration-400 hover:shadow-xl hover:-translate-y-2 relative group">
            <div class="relative overflow-hidden rounded-t-2xl">
                <img src="${product.image}" alt="${product.name}" class="w-full h-56 object-cover group-hover:scale-110 transition-transform duration-500">
                
                ${product.sale ? '<div class="absolute top-4 left-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">🔥 SALE</div>' : ''}
                ${product.isNew ? '<div class="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-3 py-2 rounded-full text-xs font-bold shadow-lg">✨ NEW</div>' : ''}
                
                <!-- Action Buttons Overlay -->
                <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-end justify-center pb-6">
                    <div class="flex gap-3">
                        <button onclick="event.stopPropagation(); toggleWishlist(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-red-500 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Add to Wishlist">
                            <i data-lucide="heart" class="h-5 w-5"></i>
                        </button>
                        <button onclick="event.stopPropagation(); quickViewProduct(${product.id})" class="bg-white/90 backdrop-blur-sm text-gray-700 hover:text-green-600 p-3 rounded-full hover:bg-white transition-all shadow-lg" title="Quick View">
                            <i data-lucide="eye" class="h-5 w-5"></i>
                        </button>
                        <button onclick="event.stopPropagation(); navigateToProduct(${product.id})" class="bg-green-600 text-white px-6 py-3 rounded-full font-semibold hover:bg-green-700 transition-all shadow-lg">
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
                    <button onclick="event.stopPropagation(); addToCart(${product.id})" class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-3 rounded-xl font-semibold transition-all hover:shadow-lg flex items-center gap-2">
                        <i data-lucide="shopping-cart" class="h-4 w-4"></i>
                        ADD
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Navigation functions
function navigateToProduct(productId) {
    window.location.href = `product-details.html?id=${productId}`;
}

// Initialize cart and wishlist systems
function initializeCartSystem() {
    console.log('🛒 Initializing cart system...');
    // Cart functionality will be handled by cart-functionality.js
}

function initializeWishlistSystem() {
    console.log('❤️ Initializing wishlist system...');
    // Wishlist functionality will be handled by wishlist-functionality.js
}

// Search functionality
function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput ? searchInput.value.trim() : '';
    
    if (query) {
        window.location.href = `products.html?search=${encodeURIComponent(query)}`;
    }
}

// Utility function to check if DOM is ready
function isDOMReady() {
    return document.readyState === 'complete' || document.readyState === 'interactive';
}

// Enhanced initialization with better timing
function waitForDOMAndInitialize() {
    if (isDOMReady()) {
        console.log('🚀 DOM is ready, initializing immediately');
        initializeOrganicStore();
    } else {
        console.log('⏳ Waiting for DOM to be ready...');
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 DOM loaded, initializing now');
            initializeOrganicStore();
        });
    }
}

// Make functions globally available
window.initializeOrganicStore = initializeOrganicStore;
window.setActiveTab = setActiveTab;
window.performSearch = performSearch;
window.navigateToProduct = navigateToProduct;
window.createProductCard = createProductCard;
window.createRecipeCard = createRecipeCard;

// Auto-initialize when script loads
waitForDOMAndInitialize();

console.log(' main.js loaded successfully');

//  Newsletter Subscribe
document.addEventListener('DOMContentLoaded', function () {

    const btn = document.getElementById('newsletter-btn');
    if (btn) {
        btn.addEventListener('click', function () {
            const email = document.getElementById('newsletter-email').value;

            if (!email) {
                alert('Please enter your email address.');
                return;
            }


            fetch('/web/dataset/call_kw', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        model: 'mail.mass_mailing.contact',
                        method: 'create',
                        args: [{ email: email }],
                        kwargs: {},
                    }
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.result) {
                    btn.innerHTML = '<i class="bi bi-check me-2"></i> Subscribed!';
                    btn.classList.add('text-success');
                    document.getElementById('newsletter-email').value = '';
                }
            })
            .catch(() => {
                alert('Something went wrong. Please try again.');
            });
        });
    }

});