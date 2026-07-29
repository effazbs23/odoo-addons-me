// Products Page with Home Page Consistent Design
// Uses exact same product card design as home page

// Use the enhanced products data
const productsData = [
    {
        id: 1,
        name: "Organic Baby Spinach",
        price: 4.99,
        originalPrice: 6.99,
        image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=300&h=300&fit=crop",
        category: "vegetables",
        brand: "Fresh Farm",
        description: "Fresh organic baby spinach leaves, perfect for salads and smoothies. Packed with iron, vitamins, and minerals.",
        rating: 4.8,
        reviews: 127,
        sale: true,
        isNew: false,
        size: "medium",
        color: "green",
        weight: "5oz",
        inStock: true,
        salePercentage: 29
    },
    {
        id: 2,
        name: "Free Range Eggs",
        price: 4.99,
        originalPrice: 6.99,
        image: "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&h=300&fit=crop",
        category: "dairy",
        brand: "Happy Hens",
        description: "Fresh free-range eggs from pasture-raised hens. Rich in omega-3 and protein.",
        rating: 4.7,
        reviews: 89,
        sale: true,
        isNew: false,
        size: "large",
        color: "white",
        weight: "12 count",
        inStock: true,
        salePercentage: 29
    },
    {
        id: 3,
        name: "Organic Strawberries",
        price: 4.99,
        originalPrice: 6.49,
        image: "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=300&h=300&fit=crop",
        category: "fruits",
        brand: "Berry Fresh",
        description: "Sweet, juicy organic strawberries. Perfect for desserts, smoothies, or eating fresh.",
        rating: 4.7,
        reviews: 156,
        sale: true,
        isNew: false,
        size: "medium",
        color: "red",
        weight: "1lb",
        inStock: true,
        salePercentage: 23
    },
    {
        id: 4,
        name: "Organic Greek Yogurt",
        price: 5.49,
        image: "https://images.unsplash.com/photo-1571212515416-cd73c6b48529?w=300&h=300&fit=crop",
        category: "dairy",
        brand: "Pure Greek",
        description: "Creamy organic Greek yogurt with live cultures. High in protein and probiotics.",
        rating: 4.8,
        reviews: 203,
        sale: false,
        isNew: false,
        size: "large",
        color: "white",
        weight: "32oz",
        inStock: true
    },
    {
        id: 5,
        name: "Wild Caught Salmon",
        price: 12.99,
        originalPrice: 15.99,
        image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=300&h=300&fit=crop",
        category: "seafood",
        brand: "Ocean Fresh",
        description: "Premium wild-caught Atlantic salmon fillets. Rich in omega-3 fatty acids.",
        rating: 4.9,
        reviews: 94,
        sale: true,
        isNew: false,
        size: "large",
        color: "orange",
        weight: "1lb",
        inStock: true,
        salePercentage: 19
    },
    {
        id: 6,
        name: "Organic Honey Crisp Apples",
        price: 5.99,
        image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
        category: "fruits",
        brand: "Orchard Fresh",
        description: "Sweet and crispy organic honey crisp apples. Perfect for snacking or baking.",
        rating: 4.9,
        reviews: 167,
        sale: false,
        isNew: true,
        size: "large",
        color: "red",
        weight: "2lb",
        inStock: true
    },
    {
        id: 7,
        name: "Organic Kale",
        price: 3.99,
        image: "https://images.unsplash.com/photo-1557844352-761f2565b576?w=300&h=300&fit=crop",
        category: "vegetables",
        brand: "Leafy Greens Co",
        description: "Fresh organic kale leaves. Superfood packed with vitamins K, A, and C.",
        rating: 4.4,
        reviews: 89,
        sale: false,
        isNew: true,
        size: "medium",
        color: "green",
        weight: "6oz",
        inStock: true
    },
    {
        id: 8,
        name: "Organic Blueberries",
        price: 6.99,
        image: "https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=300&h=300&fit=crop",
        category: "fruits",
        brand: "Berry Best",
        description: "Sweet organic blueberries packed with antioxidants. Fresh picked and delicious.",
        rating: 4.8,
        reviews: 134,
        sale: false,
        isNew: true,
        size: "small",
        color: "purple",
        weight: "6oz",
        inStock: true
    },
    {
        id: 9,
        name: "Artisan Sourdough Bread",
        price: 4.49,
        image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
        category: "bakery",
        brand: "Baker's Choice",
        description: "Handcrafted sourdough bread with organic flour. Traditional recipe with perfect crust.",
        rating: 4.6,
        reviews: 78,
        sale: false,
        isNew: true,
        size: "large",
        color: "brown",
        weight: "1.5lb",
        inStock: true
    },
    {
        id: 10,
        name: "Organic Carrots",
        price: 2.99,
        image: "https://images.unsplash.com/photo-1445282768818-728615cc910a?w=300&h=300&fit=crop",
        category: "vegetables",
        brand: "Root & Vine",
        description: "Fresh organic carrots, perfect for cooking or snacking. Sweet and crunchy.",
        rating: 4.7,
        reviews: 123,
        sale: false,
        isNew: false,
        size: "medium",
        color: "orange",
        weight: "2lb",
        inStock: true
    },
    {
        id: 11,
        name: "Organic Avocados",
        price: 7.99,
        image: "https://images.unsplash.com/photo-1549324797-371fa825d0da?w=300&h=300&fit=crop",
        category: "fruits",
        brand: "Green Gold",
        description: "Perfectly ripe organic avocados. Creamy texture and rich flavor.",
        rating: 4.6,
        reviews: 189,
        sale: false,
        isNew: false,
        size: "large",
        color: "green",
        weight: "6 count",
        inStock: true
    },
    {
        id: 12,
        name: "Organic Shrimp",
        price: 14.99,
        image: "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=300&h=300&fit=crop",
        category: "seafood",
        brand: "Coastal Catch",
        description: "Large organic shrimp, peeled and deveined. Sweet flavor and firm texture.",
        rating: 4.6,
        reviews: 67,
        sale: false,
        isNew: false,
        size: "large",
        color: "white",
        weight: "1lb",
        inStock: true
    },
    {
        id: 13,
        name: "Organic Bell Peppers Mix",
        price: 5.99,
        image: "https://images.unsplash.com/photo-1525607551340-4864c4162d29?w=300&h=300&fit=crop",
        category: "vegetables",
        brand: "Rainbow Harvest",
        description: "Colorful mix of organic bell peppers - red, yellow, and green. Sweet and crispy.",
        rating: 4.7,
        reviews: 145,
        sale: false,
        isNew: false,
        size: "medium",
        color: "red",
        weight: "3 count",
        inStock: true
    },
    {
        id: 14,
        name: "Organic Bananas",
        price: 2.49,
        image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop",
        category: "fruits",
        brand: "Tropical Fresh",
        description: "Organic bananas, perfectly ripe and sweet. Great source of potassium.",
        rating: 4.6,
        reviews: 234,
        sale: false,
        isNew: false,
        size: "medium",
        color: "yellow",
        weight: "6 count",
        inStock: true
    },
    {
        id: 15,
        name: "Organic Whole Milk",
        price: 3.49,
        image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
        category: "dairy",
        brand: "Pure Dairy",
        description: "Fresh organic whole milk from grass-fed cows. Rich, creamy, and delicious.",
        rating: 4.7,
        reviews: 178,
        sale: false,
        isNew: false,
        size: "large",
        color: "white",
        weight: "1 gallon",
        inStock: true
    },
    {
        id: 16,
        name: "Gluten-Free Oat Bread",
        price: 6.99,
        image: "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=300&h=300&fit=crop",
        category: "bakery",
        brand: "Healthy Grains",
        description: "Nutritious gluten-free bread made with organic oats. Soft texture and nutty flavor.",
        rating: 4.4,
        reviews: 92,
        sale: false,
        isNew: false,
        size: "medium",
        color: "brown",
        weight: "1lb",
        inStock: true
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
        reviews: 156,
        sale: false,
        isNew: false,
        size: "large",
        color: "green",
        weight: "1lb",
        inStock: true
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
        reviews: 187,
        sale: false,
        isNew: false,
        size: "small",
        color: "red",
        weight: "1lb",
        inStock: true
    },
    {
        id: 19,
        name: "Organic Sourdough Starter",
        price: 8.99,
        image: "https://images.unsplash.com/photo-1590736969955-71cc94901144?w=300&h=300&fit=crop",
        category: "bakery",
        brand: "Artisan Bakers",
        description: "Live organic sourdough starter. Perfect for making your own artisan bread at home.",
        rating: 4.8,
        reviews: 45,
        sale: false,
        isNew: true,
        size: "small",
        color: "white",
        weight: "4oz",
        inStock: true
    },
    {
        id: 20,
        name: "Organic Mozzarella",
        price: 6.49,
        image: "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32b?w=300&h=300&fit=crop",
        category: "dairy",
        brand: "Italian Traditions",
        description: "Fresh organic mozzarella cheese. Creamy texture perfect for pizzas and salads.",
        rating: 4.7,
        reviews: 112,
        sale: false,
        isNew: false,
        size: "medium",
        color: "white",
        weight: "8oz",
        inStock: true
    },
    {
        id: 21,
        name: "Wild Alaskan Cod",
        price: 16.99,
        originalPrice: 19.99,
        image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=300&h=300&fit=crop",
        category: "seafood",
        brand: "Arctic Catch",
        description: "Premium wild Alaskan cod fillets. Flaky white fish perfect for healthy meals.",
        rating: 4.8,
        reviews: 73,
        sale: true,
        isNew: false,
        size: "large",
        color: "white",
        weight: "1lb",
        inStock: true,
        salePercentage: 15
    },
    {
        id: 22,
        name: "Organic Quinoa Bread",
        price: 7.49,
        image: "https://images.unsplash.com/photo-1549398771-6346b3a1d8aa?w=300&h=300&fit=crop",
        category: "bakery",
        brand: "Ancient Grains",
        description: "Nutritious bread made with organic quinoa flour. High in protein and fiber.",
        rating: 4.3,
        reviews: 68,
        sale: false,
        isNew: true,
        size: "medium",
        color: "brown",
        weight: "1lb",
        inStock: true
    },
    {
        id: 23,
        name: "Organic Purple Cabbage",
        price: 3.99,
        image: "https://images.unsplash.com/photo-1596799816514-4c76d5b15d7f?w=300&h=300&fit=crop",
        category: "vegetables",
        brand: "Rainbow Harvest",
        description: "Fresh organic purple cabbage. Rich in antioxidants and perfect for slaws.",
        rating: 4.5,
        reviews: 87,
        sale: false,
        isNew: false,
        size: "large",
        color: "purple",
        weight: "2lb",
        inStock: true
    },
    {
        id: 24,
        name: "Organic Sea Bass",
        price: 18.99,
        image: "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=300&h=300&fit=crop",
        category: "seafood",
        brand: "Mediterranean Catch",
        description: "Fresh organic sea bass fillets. Delicate flavor and firm texture for gourmet meals.",
        rating: 4.9,
        reviews: 52,
        sale: false,
        isNew: true,
        size: "xl",
        color: "white",
        weight: "1.5lb",
        inStock: true
    }
];

// Global state
let filteredProducts = [...productsData];
let currentFilters = {
    categories: [],
    brands: [],
    maxPrice: 25,
    sizes: [],
    colors: [],
    special: [],
    search: ''
};
let currentSort = 'newest';
let currentView = 'grid';

// Create product card HTML - SUPPORTS BOTH GRID AND LIST VIEW
function createProductCard(product, viewType = 'grid') {
    const originalPrice = product.originalPrice;
    const hasDiscount = originalPrice && originalPrice > product.price;
    
    if (viewType === 'list') {
        return createListViewProduct(product, hasDiscount, originalPrice);
    }
    
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
                    <span class="text-gray-400 text-sm">${product.reviews || Math.floor(Math.random() * 50) + 20} reviews</span>
                </div>
                
                <div class="flex items-center justify-between">
                    <div class="space-y-1">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl font-bold text-green-600">${product.price.toFixed(2)}</span>
                            ${hasDiscount ? `<span class="text-lg text-gray-500 line-through">${originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${hasDiscount ? `<span class="text-sm text-red-600 font-semibold">Save ${(originalPrice - product.price).toFixed(2)} (${Math.round(((originalPrice - product.price) / originalPrice) * 100)}% off)</span>` : '<span class="text-sm text-green-600 font-semibold">Premium quality</span>'}
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

// Create list view product layout
function createListViewProduct(product, hasDiscount, originalPrice) {
    return `
        <div class="product-card bg-white border border-gray-200 rounded-2xl overflow-hidden transition-all duration-400 hover:shadow-xl hover:-translate-y-1 relative group">
            <div class="flex gap-6 p-6">
                <!-- Product Image -->
                <div class="relative flex-shrink-0 w-32 h-32 overflow-hidden rounded-xl">
                    <img src="${product.image}" alt="${product.name}" class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500">
                    
                    ${product.sale ? '<div class="absolute top-2 left-2 bg-gradient-to-r from-red-500 to-red-600 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg">🔥 SALE</div>' : ''}
                    ${product.isNew ? '<div class="absolute top-2 right-2 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg">✨ NEW</div>' : ''}
                </div>
                
                <!-- Product Info -->
                <div class="flex-1 flex flex-col justify-between">
                    <div>
                        <h3 class="text-xl font-bold text-gray-900 group-hover:text-green-600 transition-colors cursor-pointer mb-2" onclick="window.location.href='product-details.html?id=${product.id}'">${product.name}</h3>
                        <p class="text-gray-600 text-sm mb-2">Farm fresh • Pesticide free</p>
                        <p class="text-gray-600 text-sm line-clamp-2">${product.description}</p>
                    </div>
                    
                    <div class="flex items-center gap-2 mt-3">
                        <div class="flex text-yellow-400">
                            ${Array(5).fill().map((_, i) => 
                                `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                            ).join('')}
                        </div>
                        <span class="text-gray-600 font-medium">(${product.rating})</span>
                        <span class="text-gray-400 text-sm">${product.reviews || Math.floor(Math.random() * 50) + 20} reviews</span>
                    </div>
                </div>
                
                <!-- Price and Actions -->
                <div class="flex flex-col justify-between items-end">
                    <div class="text-right">
                        <div class="flex items-center gap-2">
                            <span class="text-2xl font-bold text-green-600">${product.price.toFixed(2)}</span>
                            ${hasDiscount ? `<span class="text-lg text-gray-500 line-through">${originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${hasDiscount ? `<div class="text-sm text-red-600 font-semibold">Save ${(originalPrice - product.price).toFixed(2)} (${Math.round(((originalPrice - product.price) / originalPrice) * 100)}% off)</div>` : '<div class="text-sm text-green-600 font-semibold">Premium quality</div>'}
                    </div>
                    
                    <div class="flex items-center gap-2 mt-4">
                        <button onclick="event.stopPropagation(); addToWishlist(${product.id})" class="bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-red-500 p-2 rounded-lg transition-all" title="Add to Wishlist">
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                        </button>
                        <button onclick="event.stopPropagation(); quickViewProduct(${product.id})" class="bg-gray-100 hover:bg-gray-200 text-gray-700 hover:text-green-600 p-2 rounded-lg transition-all" title="Quick View">
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
                            </svg>
                        </button>
                        <button onclick="event.stopPropagation(); addToCart(${product.id})" class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-4 py-2 rounded-lg font-semibold transition-all hover:shadow-lg flex items-center gap-2">
                            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5H19"></path>
                            </svg>
                            ADD
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Initialize products page
function initializeProductsPage() {
    console.log('🌱 Initializing products page with home page design...');
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Parse URL parameters
    parseUrlParameters();
    
    // Update category counts
    updateCategoryCounts();
    
    // Apply initial filters and render products
    applyFilters();
}

// Parse URL parameters for initial filters
function parseUrlParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Category filter
    const category = urlParams.get('category');
    if (category) {
        const categoryCheckbox = document.querySelector(`input[name="category"][value="${category}"]`);
        if (categoryCheckbox) {
            categoryCheckbox.checked = true;
            currentFilters.categories.push(category);
        }
    }
    
    // Search filter
    const search = urlParams.get('search');
    if (search) {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = search;
            currentFilters.search = search;
        }
    }
}

// Update category counts
function updateCategoryCounts() {
    const categories = ['vegetables', 'fruits', 'dairy', 'seafood', 'bakery'];
    
    categories.forEach(category => {
        const count = productsData.filter(p => p.category === category).length;
        const countElement = document.getElementById(`${category}-count`);
        if (countElement) {
            countElement.textContent = `(${count})`;
        }
    });
}

// Apply all filters
function applyFilters() {
    // Get all filter values
    currentFilters.categories = Array.from(document.querySelectorAll('input[name="category"]:checked')).map(cb => cb.value);
    currentFilters.brands = Array.from(document.querySelectorAll('input[name="brand"]:checked')).map(cb => cb.value);
    currentFilters.special = Array.from(document.querySelectorAll('input[name="special"]:checked')).map(cb => cb.value);
    currentFilters.search = document.getElementById('search-input')?.value || '';
    
    // Filter products
    filteredProducts = productsData.filter(product => {
        // Category filter
        if (currentFilters.categories.length > 0 && !currentFilters.categories.includes(product.category)) {
            return false;
        }
        
        // Brand filter
        if (currentFilters.brands.length > 0 && !currentFilters.brands.includes(product.brand)) {
            return false;
        }
        
        // Price filter
        if (product.price > currentFilters.maxPrice) {
            return false;
        }
        
        // Size filter
        if (currentFilters.sizes.length > 0 && !currentFilters.sizes.includes(product.size)) {
            return false;
        }
        
        // Color filter
        if (currentFilters.colors.length > 0 && !currentFilters.colors.includes(product.color)) {
            return false;
        }
        
        // Special filters
        if (currentFilters.special.length > 0) {
            let matchesSpecial = false;
            if (currentFilters.special.includes('sale') && product.sale) matchesSpecial = true;
            if (currentFilters.special.includes('new') && product.isNew) matchesSpecial = true;
            if (!matchesSpecial) return false;
        }
        
        // Search filter
        if (currentFilters.search) {
            const searchTerm = currentFilters.search.toLowerCase();
            const searchableText = `${product.name} ${product.description} ${product.brand} ${product.category}`.toLowerCase();
            if (!searchableText.includes(searchTerm)) {
                return false;
            }
        }
        
        return true;
    });
    
    // Sort products
    sortProducts();
    
    // Update UI
    updateActiveFiltersDisplay();
    updateProductsDisplay();
    updateProductCount();
}

// Sort products
function sortProducts() {
    const sortBy = document.getElementById('sort-select')?.value || currentSort;
    currentSort = sortBy;
    
    filteredProducts.sort((a, b) => {
        switch (sortBy) {
            case 'price-low':
                return a.price - b.price;
            case 'price-high':
                return b.price - a.price;
            case 'name':
                return a.name.localeCompare(b.name);
            case 'rating':
                return b.rating - a.rating;
            case 'sale':
                if (a.sale && !b.sale) return -1;
                if (!a.sale && b.sale) return 1;
                return b.rating - a.rating;
            case 'newest':
            default:
                // Sort new items first, then by rating
                if (a.isNew && !b.isNew) return -1;
                if (!a.isNew && b.isNew) return 1;
                return b.rating - a.rating;
        }
    });
}

// Update products display
function updateProductsDisplay() {
    const container = document.getElementById('products-grid');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    
    if (!container) return;
    
    // Hide loading and empty states
    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    
    if (filteredProducts.length === 0) {
        if (emptyState) emptyState.classList.remove('hidden');
        container.innerHTML = '';
        return;
    }
    
    // Update container classes based on view type
    if (currentView === 'list') {
        container.className = 'space-y-4';
        container.innerHTML = filteredProducts.map(product => createProductCard(product, 'list')).join('');
    } else {
        container.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6';
        container.innerHTML = filteredProducts.map(product => createProductCard(product, 'grid')).join('');
    }
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Update product count
function updateProductCount() {
    const countElements = [
        document.getElementById('filtered-count'),
        document.getElementById('products-count')
    ];
    
    countElements.forEach(element => {
        if (element) {
            element.textContent = filteredProducts.length;
        }
    });
}

// Update active filters display
function updateActiveFiltersDisplay() {
    const activeFiltersContainer = document.getElementById('active-filters');
    const activeFiltersList = document.getElementById('active-filters-list');
    
    if (!activeFiltersContainer || !activeFiltersList) return;
    
    const hasActiveFilters = currentFilters.categories.length > 0 || 
                            currentFilters.brands.length > 0 || 
                            currentFilters.maxPrice < 25 || 
                            currentFilters.sizes.length > 0 || 
                            currentFilters.colors.length > 0 || 
                            currentFilters.special.length > 0 || 
                            currentFilters.search;
    
    if (hasActiveFilters) {
        activeFiltersContainer.classList.remove('hidden');
        
        let filtersHtml = '';
        
        // Category filters
        currentFilters.categories.forEach(category => {
            filtersHtml += `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                ${category}
                <button onclick="removeFilter('category', '${category}')" class="text-green-600 hover:text-green-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        });
        
        // Brand filters
        currentFilters.brands.forEach(brand => {
            filtersHtml += `<span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                ${brand}
                <button onclick="removeFilter('brand', '${brand}')" class="text-blue-600 hover:text-blue-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        });
        
        // Price filter
        if (currentFilters.maxPrice < 25) {
            filtersHtml += `<span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                Under $${currentFilters.maxPrice}
                <button onclick="removeFilter('price')" class="text-green-600 hover:text-green-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        }
        
        // Size filters
        currentFilters.sizes.forEach(size => {
            filtersHtml += `<span class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                ${size}
                <button onclick="removeFilter('size', '${size}')" class="text-purple-600 hover:text-purple-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        });
        
        // Color filters
        currentFilters.colors.forEach(color => {
            filtersHtml += `<span class="bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                ${color}
                <button onclick="removeFilter('color', '${color}')" class="text-gray-600 hover:text-gray-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        });
        
        // Special filters
        currentFilters.special.forEach(special => {
            filtersHtml += `<span class="bg-orange-100 text-orange-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                ${special === 'sale' ? 'Sale' : 'New'}
                <button onclick="removeFilter('special', '${special}')" class="text-orange-600 hover:text-orange-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        });
        
        // Search filter
        if (currentFilters.search) {
            filtersHtml += `<span class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1">
                "${currentFilters.search}"
                <button onclick="removeFilter('search')" class="text-indigo-600 hover:text-indigo-800">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>`;
        }
        
        activeFiltersList.innerHTML = filtersHtml;
        
        // Re-initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    } else {
        activeFiltersContainer.classList.add('hidden');
    }
}

// Remove filter
function removeFilter(type, value) {
    switch (type) {
        case 'category':
            const categoryCheckbox = document.querySelector(`input[name="category"][value="${value}"]`);
            if (categoryCheckbox) categoryCheckbox.checked = false;
            break;
        case 'brand':
            const brandCheckbox = document.querySelector(`input[name="brand"][value="${value}"]`);
            if (brandCheckbox) brandCheckbox.checked = false;
            break;
        case 'price':
            const priceSlider = document.getElementById('price-slider');
            if (priceSlider) priceSlider.value = 25;
            updatePriceRange();
            break;
        case 'size':
            const sizeButton = document.querySelector(`[data-size="${value}"]`);
            if (sizeButton) sizeButton.classList.remove('active');
            currentFilters.sizes = currentFilters.sizes.filter(s => s !== value);
            break;
        case 'color':
            const colorButton = document.querySelector(`[data-color="${value}"]`);
            if (colorButton) colorButton.classList.remove('active');
            currentFilters.colors = currentFilters.colors.filter(c => c !== value);
            break;
        case 'special':
            const specialCheckbox = document.querySelector(`input[name="special"][value="${value}"]`);
            if (specialCheckbox) specialCheckbox.checked = false;
            break;
        case 'search':
            const searchInput = document.getElementById('search-input');
            if (searchInput) searchInput.value = '';
            currentFilters.search = '';
            break;
    }
    
    applyFilters();
}

// Clear all filters
function clearAllFilters() {
    // Reset checkboxes
    document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    
    // Reset price slider
    const priceSlider = document.getElementById('price-slider');
    if (priceSlider) {
        priceSlider.value = 25;
        updatePriceRange();
    }
    
    // Reset size buttons
    document.querySelectorAll('.size-option').forEach(btn => btn.classList.remove('active'));
    
    // Reset color buttons
    document.querySelectorAll('.color-swatch').forEach(btn => btn.classList.remove('active'));
    
    // Reset search
    const searchInput = document.getElementById('search-input');
    if (searchInput) searchInput.value = '';
    
    // Reset filters
    currentFilters = {
        categories: [],
        brands: [],
        maxPrice: 25,
        sizes: [],
        colors: [],
        special: [],
        search: ''
    };
    
    applyFilters();
}

// Update price range
function updatePriceRange() {
    const priceSlider = document.getElementById('price-slider');
    const maxPriceDisplay = document.getElementById('max-price-display');
    const currentMaxPriceDisplay = document.getElementById('current-max-price');
    
    if (priceSlider) {
        const value = parseFloat(priceSlider.value);
        currentFilters.maxPrice = value;
        
        if (maxPriceDisplay) maxPriceDisplay.textContent = value;
        if (currentMaxPriceDisplay) currentMaxPriceDisplay.textContent = value;
        
        applyFilters();
    }
}

// Toggle size filter
function toggleSizeFilter(size) {
    const button = document.querySelector(`[data-size="${size}"]`);
    if (!button) return;
    
    if (currentFilters.sizes.includes(size)) {
        currentFilters.sizes = currentFilters.sizes.filter(s => s !== size);
        button.classList.remove('active');
    } else {
        currentFilters.sizes.push(size);
        button.classList.add('active');
    }
    
    applyFilters();
}

// Toggle color filter
function toggleColorFilter(color) {
    const button = document.querySelector(`[data-color="${color}"]`);
    if (!button) return;
    
    if (currentFilters.colors.includes(color)) {
        currentFilters.colors = currentFilters.colors.filter(c => c !== color);
        button.classList.remove('active');
    } else {
        currentFilters.colors.push(color);
        button.classList.add('active');
    }
    
    applyFilters();
}

// Toggle view functions
function toggleView(view) {
    currentView = view;
    
    // Update button states
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    
    if (view === 'grid') {
        if (gridBtn) gridBtn.className = 'p-2 bg-green-600 text-white rounded-lg';
        if (listBtn) listBtn.className = 'p-2 bg-gray-200 text-gray-600 rounded-lg';
    } else {
        if (gridBtn) gridBtn.className = 'p-2 bg-gray-200 text-gray-600 rounded-lg';
        if (listBtn) listBtn.className = 'p-2 bg-green-600 text-white rounded-lg';
    }
    
    updateProductsDisplay();
}

// Helper functions for interactivity
function addToCart(productId) {
    const product = productsData.find(p => p.id === productId);
    if (product) {
        showToast(`Added ${product.name} to cart!`, 'success');
        console.log('🛒 Added to cart:', product.name);
    }
}

function addToWishlist(productId) {
    const product = productsData.find(p => p.id === productId);
    if (product) {
        showToast(`Added ${product.name} to wishlist!`, 'success');
        console.log('❤️ Added to wishlist:', product.name);
    }
}

function quickViewProduct(productId) {
    console.log('🔍 Opening quick view for product:', productId);
    
    // Wait a bit for all scripts to load, then try quick view functions
    setTimeout(() => {
        if (typeof window.showQuickView === 'function') {
            window.showQuickView(productId);
        } else if (typeof window.quickViewProduct === 'function' && window.quickViewProduct !== quickViewProduct) {
            window.quickViewProduct(productId);
        } else {
            // Initialize quick view if not already done
            if (typeof window.initializeModal === 'function') {
                window.initializeModal();
                setTimeout(() => {
                    if (typeof window.showQuickView === 'function') {
                        window.showQuickView(productId);
                    } else {
                        window.location.href = `product-details.html?id=${productId}`;
                    }
                }, 100);
            } else {
                // Fallback to product details page
                window.location.href = `product-details.html?id=${productId}`;
            }
        }
    }, 100);
}

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

// Make functions globally available
window.addToCart = addToCart;
window.addToWishlist = addToWishlist;
window.quickViewProduct = quickViewProduct;
window.toggleView = toggleView;
window.applyFilters = applyFilters;
window.clearAllFilters = clearAllFilters;
window.updatePriceRange = updatePriceRange;
window.toggleSizeFilter = toggleSizeFilter;
window.toggleColorFilter = toggleColorFilter;
window.removeFilter = removeFilter;

// Initialize page when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeProductsPage);
} else {
    initializeProductsPage();
}

console.log('✅ Products page with home design consistency loaded');