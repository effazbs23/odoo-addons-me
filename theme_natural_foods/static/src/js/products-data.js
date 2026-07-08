// Products Database and Related Functions

// Enhanced product database with detailed attributes
function getProductById(id) {
    const sampleProducts = [
        // Sale Products (Hot Deals)
        {
            id: 1,
            name: "Organic Baby Spinach",
            price: 4.99,
            originalPrice: 6.99,
            image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Fresh Farm",
            description: "Fresh organic baby spinach leaves, perfect for salads and smoothies. Packed with iron, vitamins, and minerals for optimal health and wellness.",
            rating: 4.8,
            sale: true,
            isNew: false,
            sizes: ["5oz", "10oz", "1lb"],
            colors: ["Green"]
        },
        {
            id: 2,
            name: "Free Range Eggs",
            price: 4.99,
            originalPrice: 6.99,
            image: "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Happy Hens",
            description: "Fresh free-range eggs from pasture-raised hens. Rich in omega-3 and protein. Ethically sourced from local farms.",
            rating: 4.7,
            sale: true,
            isNew: false,
            sizes: ["6 count", "12 count", "18 count"],
            colors: ["Brown", "White"]
        },
        {
            id: 3,
            name: "Organic Strawberries",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Berry Fresh",
            description: "Sweet, juicy organic strawberries. Perfect for desserts, smoothies, or eating fresh. Locally grown.",
            rating: 4.7,
            sale: true,
            isNew: false,
            sizes: ["1lb", "2lb"],
            colors: ["Red"]
        },
        {
            id: 4,
            name: "Organic Greek Yogurt",
            price: 5.49,
            image: "https://images.unsplash.com/photo-1571212515416-cd73c6b48529?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Pure Greek",
            description: "Creamy organic Greek yogurt with live cultures. High in protein and probiotics. Perfect for breakfast.",
            rating: 4.8,
            sale: false,
            isNew: false,
            sizes: ["6oz", "32oz"],
            colors: ["White"]
        },
        {
            id: 5,
            name: "Wild Caught Salmon",
            price: 12.99,
            originalPrice: 15.99,
            image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Ocean Fresh",
            description: "Premium wild-caught Atlantic salmon fillets. Rich in omega-3 fatty acids. Sustainably sourced.",
            rating: 4.9,
            sale: true,
            isNew: false,
            sizes: ["1lb", "2lb"],
            colors: ["Pink"]
        },
        // New Products (New Arrivals)
        {
            id: 6,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Orchard Fresh",
            description: "Sweet and crispy organic honey crisp apples. Perfect for snacking or baking. Grown without pesticides in sustainable orchards.",
            rating: 4.9,
            sale: false,
            isNew: true,
            sizes: ["1lb", "2lb", "5lb"],
            colors: ["Red", "Yellow"]
        },
        {
            id: 7,
            name: "Organic Kale",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1557844352-761f2565b576?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Leafy Greens Co",
            description: "Fresh organic kale leaves. Superfood packed with vitamins K, A, and C. Perfect for salads and smoothies.",
            rating: 4.4,
            sale: false,
            isNew: true,
            sizes: ["1 Bunch", "2 Bunches"],
            colors: ["Dark Green"]
        },
        {
            id: 8,
            name: "Organic Blueberries",
            price: 6.99,
            image: "https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Berry Best",
            description: "Sweet organic blueberries packed with antioxidants. Fresh picked and perfect for breakfast or snacking.",
            rating: 4.8,
            sale: false,
            isNew: true,
            sizes: ["6oz", "12oz", "1lb"],
            colors: ["Blue"]
        },
        {
            id: 9,
            name: "Artisan Sourdough Bread",
            price: 4.49,
            image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Baker's Choice",
            description: "Handcrafted sourdough bread with organic flour. Traditional recipe with tangy flavor and perfect crust.",
            rating: 4.6,
            sale: false,
            isNew: true,
            sizes: ["1 Loaf"],
            colors: ["Brown"]
        },
        // Featured Products (High Rating)
        {
            id: 10,
            name: "Organic Carrots",
            price: 2.99,
            image: "https://images.unsplash.com/photo-1445282768818-728615cc910a?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Root & Vine",
            description: "Fresh organic carrots, perfect for cooking or snacking. Sweet and crunchy with natural orange color.",
            rating: 4.7,
            sale: false,
            isNew: false,
            sizes: ["1lb", "2lb", "5lb"],
            colors: ["Orange"]
        },
        {
            id: 11,
            name: "Organic Avocados",
            price: 7.99,
            image: "https://images.unsplash.com/photo-1549324797-371fa825d0da?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Green Gold",
            description: "Perfectly ripe organic avocados. Creamy texture and rich flavor. Great source of healthy fats.",
            rating: 4.6,
            sale: false,
            isNew: false,
            sizes: ["2-pack", "4-pack", "6-pack"],
            colors: ["Green"]
        },
        {
            id: 12,
            name: "Organic Shrimp",
            price: 14.99,
            image: "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Coastal Catch",
            description: "Large organic shrimp, peeled and deveined. Sweet flavor and firm texture. Perfect for grilling or sautéing.",
            rating: 4.6,
            sale: false,
            isNew: false,
            sizes: ["1lb", "2lb"],
            colors: ["Pink"]
        },
        // Additional products for tabs
        {
            id: 13,
            name: "Organic Bell Peppers Mix",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1525607551340-4864c4162d29?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Rainbow Harvest",
            description: "Colorful mix of organic bell peppers - red, yellow, and green. Sweet, crispy, and perfect for any dish.",
            rating: 4.7,
            sale: false,
            isNew: false,
            sizes: ["3-pack", "6-pack"],
            colors: ["Red", "Yellow", "Green"]
        },
        {
            id: 14,
            name: "Organic Bananas",
            price: 2.49,
            image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Tropical Fresh",
            description: "Organic bananas, perfectly ripe and sweet. Great source of potassium and natural energy.",
            rating: 4.6,
            sale: false,
            isNew: false,
            sizes: ["1 Bunch", "2 Bunches"],
            colors: ["Yellow"]
        },
        {
            id: 15,
            name: "Organic Whole Milk",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Pure Dairy",
            description: "Fresh organic whole milk from grass-fed cows. Rich, creamy, and naturally delicious.",
            rating: 4.7,
            sale: false,
            isNew: false,
            sizes: ["1/2 Gallon", "1 Gallon"],
            colors: ["White"]
        },
        {
            id: 16,
            name: "Gluten-Free Oat Bread",
            price: 6.99,
            image: "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Healthy Grains",
            description: "Nutritious gluten-free bread made with organic oats. Soft texture and nutty flavor. Perfect for toast.",
            rating: 4.4,
            sale: false,
            isNew: false,
            sizes: ["1 Loaf"],
            colors: ["Brown"]
        },
        {
            id: 17,
            name: "Organic Broccoli",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1628773822503-930a7eaecf80?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Green Valley",
            description: "Fresh organic broccoli crowns. High in vitamins C and K, fiber, and antioxidants.",
            rating: 4.5,
            sale: false,
            isNew: false,
            sizes: ["1 Head", "2 Heads"],
            colors: ["Green"]
        },
        {
            id: 18,
            name: "Organic Cherry Tomatoes",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1592841200221-21973486d5d1?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Sun Kissed",
            description: "Sweet organic cherry tomatoes on the vine. Perfect for salads and snacking.",
            rating: 4.6,
            sale: false,
            isNew: false,
            sizes: ["1 Pint", "2 Pints"],
            colors: ["Red"]
        }
    ];
    
    return sampleProducts.find(product => product.id === parseInt(id));
}

// Get all products
function getAllProducts() {
    return Array.from({length: 18}, (_, i) => getProductById(i + 1)).filter(Boolean);
}

// Filter products function
function filterProducts(filters) {
    let products = getAllProducts();
    
    // Filter by category
    if (filters.category && filters.category.length > 0) {
        products = products.filter(product => filters.category.includes(product.category));
    }
    
    // Filter by brand
    if (filters.brand && filters.brand.length > 0) {
        products = products.filter(product => filters.brand.includes(product.brand));
    }
    
    // Filter by price range
    if (filters.minPrice !== undefined && filters.maxPrice !== undefined) {
        products = products.filter(product => 
            product.price >= filters.minPrice && product.price <= filters.maxPrice
        );
    }
    
    // Filter by size
    if (filters.size && filters.size.length > 0) {
        products = products.filter(product => 
            product.sizes && product.sizes.some(size => filters.size.includes(size))
        );
    }
    
    // Filter by color
    if (filters.color && filters.color.length > 0) {
        products = products.filter(product => 
            product.colors && product.colors.some(color => filters.color.includes(color))
        );
    }
    
    return products;
}

// Create product card HTML
function createProductCard(product) {
    const inWishlist = isInWishlist(product.id);
    
    return `
        <div class="product-card group bg-white border border-gray-200 rounded-xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative">
            <div class="relative overflow-hidden">
                <img src="${product.image}" alt="${product.name}" class="w-full h-48 object-cover group-hover:scale-110 transition-transform duration-500">
                
                <!-- Badges -->
                ${product.sale ? '<div class="absolute top-3 left-3 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold">SALE</div>' : ''}
                ${product.isNew ? '<div class="absolute top-3 right-3 bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold">NEW</div>' : ''}
                
                <!-- Action buttons -->
                <div class="absolute top-3 ${product.sale && product.isNew ? 'right-20' : product.sale || product.isNew ? 'right-3' : 'right-3'} flex flex-col gap-2">
                    <button onclick="addToWishlist(${product.id})" 
                            data-wishlist-id="${product.id}"
                            class="p-2 rounded-full backdrop-blur-sm transition-all shadow-md hover:scale-110 ${inWishlist ? 'bg-red-500 text-white' : 'bg-white/90 text-gray-400 hover:text-red-500'}"
                            title="${inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}">
                        <i data-lucide="heart" class="h-4 w-4 ${inWishlist ? 'fill-current' : ''}"></i>
                    </button>
                    <button onclick="quickViewProduct(${product.id})" 
                            class="p-2 rounded-full bg-white/90 backdrop-blur-sm text-gray-700 hover:text-green-600 transition-all shadow-md hover:scale-110" 
                            title="Quick View">
                        <i data-lucide="eye" class="h-4 w-4"></i>
                    </button>
                </div>
            </div>
            
            <div class="p-6 space-y-4">
                <div>
                    <a href="product-details.html?id=${product.id}" class="font-bold text-gray-900 hover:text-green-600 transition-colors line-clamp-2 cursor-pointer block">
                        ${product.name}
                    </a>
                    <p class="text-gray-600 text-sm mt-1 flex items-center gap-1">
                        <span class="w-2 h-2 bg-green-400 rounded-full"></span>
                        ${product.brand} • Organic
                    </p>
                </div>
                
                <div class="flex items-center gap-2">
                    <div class="flex text-yellow-400">
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
                        ${product.originalPrice ? `<span class="text-xs text-red-600 font-semibold">Save $${(product.originalPrice - product.price).toFixed(2)}</span>` : '<span class="text-xs text-green-600 font-semibold">Premium quality</span>'}
                    </div>
                    <button onclick="addToCartWithAjax(${product.id})" 
                            class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-4 py-2 rounded-lg font-semibold transition-all hover:shadow-md flex items-center gap-2">
                        <i data-lucide="shopping-cart" class="h-4 w-4"></i>
                        ADD
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Create compact product card for tabs (3 per row)
function createCompactProductCard(product) {
    const inWishlist = isInWishlist(product.id);
    
    return `
        <div class="compact-product-card group bg-white border border-gray-200 rounded-xl overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 relative">
            <div class="relative overflow-hidden">
                <img src="${product.image}" alt="${product.name}" class="w-full h-40 object-cover group-hover:scale-110 transition-transform duration-500">
                
                <!-- Badges -->
                ${product.sale ? '<div class="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">SALE</div>' : ''}
                ${product.isNew ? '<div class="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-bold">NEW</div>' : ''}
                
                <!-- Wishlist and Quick View buttons -->
                <div class="absolute top-2 ${product.sale && product.isNew ? 'right-16' : product.sale || product.isNew ? 'right-2' : 'right-2'} flex flex-col gap-1">
                    <button onclick="addToWishlist(${product.id})" 
                            data-wishlist-id="${product.id}"
                            class="p-2 rounded-full backdrop-blur-sm transition-all shadow-md hover:scale-110 ${inWishlist ? 'bg-red-500 text-white' : 'bg-white/90 text-gray-400 hover:text-red-500'}"
                            title="${inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}">
                        <i data-lucide="heart" class="h-3 w-3 ${inWishlist ? 'fill-current' : ''}"></i>
                    </button>
                    <button onclick="quickViewProduct(${product.id})" 
                            class="p-2 rounded-full bg-white/90 backdrop-blur-sm text-gray-700 hover:text-green-600 transition-all shadow-md hover:scale-110" 
                            title="Quick View">
                        <i data-lucide="eye" class="h-3 w-3"></i>
                    </button>
                </div>
            </div>
            
            <div class="p-4 space-y-3">
                <div>
                    <a href="product-details.html?id=${product.id}" class="font-bold text-gray-900 hover:text-green-600 transition-colors line-clamp-2 cursor-pointer block text-sm">
                        ${product.name}
                    </a>
                    <p class="text-gray-600 text-xs mt-1 flex items-center gap-1">
                        <span class="w-1.5 h-1.5 bg-green-400 rounded-full"></span>
                        ${product.brand} • Organic
                    </p>
                </div>
                
                <div class="flex items-center gap-1">
                    <div class="flex text-yellow-400 text-sm">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="text-gray-600 text-xs">(${product.rating})</span>
                </div>
                
                <div class="flex items-center justify-between">
                    <div class="space-y-1">
                        <div class="flex items-center gap-2">
                            <span class="text-lg font-bold text-green-600">$${product.price.toFixed(2)}</span>
                            ${product.originalPrice ? `<span class="text-sm text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${product.originalPrice ? `<span class="text-xs text-red-600 font-semibold">Save $${(product.originalPrice - product.price).toFixed(2)}</span>` : '<span class="text-xs text-green-600 font-semibold">Premium quality</span>'}
                    </div>
                    <button onclick="addToCartWithAjax(${product.id})" 
                            class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-3 py-2 rounded-lg font-semibold transition-all hover:shadow-md flex items-center gap-1 text-xs">
                        <i data-lucide="shopping-cart" class="h-3 w-3"></i>
                        ADD
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Populate home page sections
function populateHomePageSections() {
    console.log('Populating home page sections...');
    
    const allProducts = getAllProducts();
    
    // Hot Deals (sale products)
    const hotDeals = allProducts.filter(product => product.sale).slice(0, 4);
    const hotDealsContainer = document.getElementById('hot-deals');
    if (hotDealsContainer && hotDeals.length > 0) {
        hotDealsContainer.innerHTML = hotDeals.map(product => createProductCard(product)).join('');
    }
    
    // New Arrivals (new products)
    const newArrivals = allProducts.filter(product => product.isNew).slice(0, 4);
    const newArrivalsContainer = document.getElementById('new-arrivals');
    if (newArrivalsContainer && newArrivals.length > 0) {
        newArrivalsContainer.innerHTML = newArrivals.map(product => createProductCard(product)).join('');
    }
    
    // Featured Products (high rating)
    const featuredProducts = allProducts.filter(product => product.rating >= 4.6 && !product.sale && !product.isNew).slice(0, 4);
    const featuredContainer = document.getElementById('featured-products');
    if (featuredContainer && featuredProducts.length > 0) {
        featuredContainer.innerHTML = featuredProducts.map(product => createProductCard(product)).join('');
    }
    
    // Our Products (mixed)
    const ourProducts = allProducts.slice(0, 4);
    const ourProductsContainer = document.getElementById('our-products');
    if (ourProductsContainer && ourProducts.length > 0) {
        ourProductsContainer.innerHTML = ourProducts.map(product => createProductCard(product)).join('');
    }
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    console.log('Home page sections populated');
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.getProductById = getProductById;
    window.getAllProducts = getAllProducts;
    window.filterProducts = filterProducts;
    window.createProductCard = createProductCard;
    window.createCompactProductCard = createCompactProductCard;
    window.populateHomePageSections = populateHomePageSections;
}