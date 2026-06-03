// Enhanced Products Page JavaScript - Comprehensive filtering, quick view, and product management

// Enhanced products data with additional attributes
const enhancedProducts = [
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
let filteredProducts = [...enhancedProducts];
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

// Initialize products page
function initializeProductsPage() {
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
        const count = enhancedProducts.filter(p => p.category === category).length;
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
    filteredProducts = enhancedProducts.filter(product => {
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

// Update products display
function updateProductsDisplay() {
    const productsGrid = document.getElementById('products-grid');
    const loadingState = document.getElementById('loading-state');
    const emptyState = document.getElementById('empty-state');
    
    if (!productsGrid) return;
    
    if (filteredProducts.length === 0) {
        productsGrid.innerHTML = '';
        if (loadingState) loadingState.classList.add('hidden');
        if (emptyState) emptyState.classList.remove('hidden');
        return;
    }
    
    if (loadingState) loadingState.classList.add('hidden');
    if (emptyState) emptyState.classList.add('hidden');
    
    const productsHtml = filteredProducts.map(product => createProductCard(product)).join('');
    productsGrid.innerHTML = productsHtml;
    
    // Re-initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Create product card
function createProductCard(product) {
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    
    return `
        <div class="product-card p-6 relative group">
            <!-- Badges -->
            ${product.sale && product.salePercentage ? `<div class="absolute top-4 left-4 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-bold z-10">-${product.salePercentage}% OFF</div>` : ''}
            ${product.isNew ? `<div class="absolute top-4 right-4 bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-bold z-10">NEW</div>` : ''}
            
            <!-- Product Image -->
            <div class="relative overflow-hidden rounded-xl mb-4">
                <img src="${product.image}" alt="${product.name}" class="product-image">
                
                <!-- Action buttons overlay -->
                <div class="absolute top-3 ${product.sale && product.isNew ? 'right-16' : product.sale || product.isNew ? 'right-3' : 'right-3'} flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="addToWishlist(${product.id})" class="p-2 bg-white/90 backdrop-blur-sm rounded-full hover:bg-red-50 transition-colors shadow-md">
                        <i data-lucide="heart" class="h-4 w-4 text-gray-600 hover:text-red-500"></i>
                    </button>
                    <button onclick="openQuickView(${product.id})" class="p-2 bg-white/90 backdrop-blur-sm rounded-full hover:bg-blue-50 transition-colors shadow-md">
                        <i data-lucide="eye" class="h-4 w-4 text-gray-600 hover:text-blue-500"></i>
                    </button>
                </div>
                
                <!-- Quick actions on image -->
                <div class="absolute bottom-3 left-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="addToCart(${product.id})" class="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2">
                        <i data-lucide="shopping-cart" class="h-4 w-4"></i>
                        Quick Add
                    </button>
                </div>
            </div>
            
            <!-- Product Info -->
            <div class="space-y-3">
                <div>
                    <div class="flex items-center gap-2 mb-1">
                        <span class="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-semibold capitalize">${product.category}</span>
                        <span class="text-gray-400">•</span>
                        <span class="text-gray-600 text-sm">${product.brand}</span>
                    </div>
                    <h3 class="font-bold text-gray-900 text-lg hover:text-green-600 transition-colors cursor-pointer" onclick="window.location.href='product-details.html?id=${product.id}'">${product.name}</h3>
                    <p class="text-gray-600 text-sm mt-1 line-clamp-2">${product.description}</p>
                </div>
                
                <!-- Rating and Reviews -->
                <div class="flex items-center gap-2">
                    <div class="flex text-yellow-400 text-sm">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="text-gray-600 text-sm">${product.rating}</span>
                    <span class="text-gray-400 text-sm">(${product.reviews})</span>
                </div>
                
                <!-- Product Details -->
                <div class="flex items-center gap-3 text-xs text-gray-600">
                    <span class="flex items-center gap-1">
                        <i data-lucide="package" class="h-3 w-3"></i>
                        ${product.weight}
                    </span>
                    <span class="flex items-center gap-1">
                        <div class="w-3 h-3 rounded-full border" style="background-color: ${getColorCode(product.color)};"></div>
                        ${product.color}
                    </span>
                    <span class="bg-gray-100 px-2 py-1 rounded-full text-xs capitalize">${product.size}</span>
                </div>
                
                <!-- Price and Add to Cart -->
                <div class="flex items-center justify-between">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="text-xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                            ${product.originalPrice ? `<span class="text-sm text-gray-500 line-through">$${product.originalPrice.toFixed(2)}</span>` : ''}
                        </div>
                        ${savings > 0 ? `<span class="text-xs text-red-600 font-semibold">Save $${savings.toFixed(2)}</span>` : '<span class="text-xs text-green-600 font-semibold">Premium quality</span>'}
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="addToCart(${product.id})" class="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-4 py-2 rounded-lg font-semibold transition-all hover:shadow-md flex items-center gap-2">
                            <i data-lucide="shopping-cart" class="h-4 w-4"></i>
                            ADD
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Get color code for display
function getColorCode(color) {
    const colorMap = {
        red: '#ef4444',
        green: '#10b981',
        yellow: '#f59e0b',
        orange: '#f97316',
        purple: '#8b5cf6',
        white: '#ffffff',
        brown: '#a3a3a3'
    };
    return colorMap[color] || '#6b7280';
}

// Update product count
function updateProductCount() {
    const countElements = [
        document.getElementById('products-count'),
        document.getElementById('filtered-count')
    ];
    
    countElements.forEach(element => {
        if (element) {
            element.textContent = filteredProducts.length;
        }
    });
}

// Toggle view (grid/list)
function toggleView(view) {
    currentView = view;
    
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    const productsGrid = document.getElementById('products-grid');
    
    if (view === 'grid') {
        if (gridBtn) {
            gridBtn.classList.add('bg-green-600', 'text-white');
            gridBtn.classList.remove('bg-gray-200', 'text-gray-600');
        }
        if (listBtn) {
            listBtn.classList.remove('bg-green-600', 'text-white');
            listBtn.classList.add('bg-gray-200', 'text-gray-600');
        }
        if (productsGrid) {
            productsGrid.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6';
        }
    } else {
        if (listBtn) {
            listBtn.classList.add('bg-green-600', 'text-white');
            listBtn.classList.remove('bg-gray-200', 'text-gray-600');
        }
        if (gridBtn) {
            gridBtn.classList.remove('bg-green-600', 'text-white');
            gridBtn.classList.add('bg-gray-200', 'text-gray-600');
        }
        if (productsGrid) {
            productsGrid.className = 'grid grid-cols-1 gap-4';
        }
    }
}

// Toggle mobile filters
function toggleMobileFilters() {
    const overlay = document.getElementById('mobile-filters-overlay');
    const filtersContent = document.getElementById('mobile-filters-content');
    const sidebarFilters = document.getElementById('filters-sidebar');
    
    if (overlay && filtersContent && sidebarFilters) {
        if (overlay.classList.contains('hidden')) {
            // Clone desktop filters to mobile
            filtersContent.innerHTML = sidebarFilters.innerHTML;
            overlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
            
            // Re-initialize Lucide icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        } else {
            overlay.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }
}

// Open quick view modal
function openQuickView(productId) {
    console.log('Opening quick view for product:', productId); // Debug log
    
    const product = enhancedProducts.find(p => p.id === productId);
    if (!product) {
        console.error('Product not found:', productId);
        return;
    }
    
    const modal = document.getElementById('quick-view-modal');
    const content = document.getElementById('quick-view-content');
    
    if (!modal || !content) {
        console.error('Quick view modal elements not found');
        return;
    }
    
    const savings = product.originalPrice ? (product.originalPrice - product.price) : 0;
    
    content.innerHTML = `
        <div class="relative">
            <!-- Close button -->
            <button onclick="closeQuickView()" class="absolute top-4 right-4 p-3 text-gray-400 hover:text-gray-600 bg-white rounded-full shadow-lg z-20 hover:shadow-xl transition-all">
                <i data-lucide="x" class="h-6 w-6"></i>
            </button>
            
            <div class="flex flex-col lg:flex-row">
                <!-- Product Image -->
                <div class="w-full lg:w-1/2 p-6">
                    <div class="relative">
                        <img src="${product.image}" alt="${product.name}" class="w-full h-80 lg:h-96 object-cover rounded-2xl shadow-lg">
                        ${product.sale && product.salePercentage ? `<div class="absolute top-4 left-4 bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">-${product.salePercentage}% OFF</div>` : ''}
                        ${product.isNew ? `<div class="absolute top-4 right-4 bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">NEW</div>` : ''}
                    </div>
                </div>
                
                <!-- Product Details -->
                <div class="w-full lg:w-1/2 p-6 space-y-6">
                    <div>
                        <div class="flex items-center gap-3 mb-3">
                            <span class="bg-gradient-to-r from-green-100 to-emerald-100 text-green-800 px-4 py-2 rounded-full text-sm font-bold capitalize border border-green-200">${product.category}</span>
                            <span class="text-gray-400">•</span>
                            <span class="text-gray-600 font-medium">${product.brand}</span>
                        </div>
                        <h2 class="text-3xl font-bold text-gray-900 mb-3">${product.name}</h2>
                        <p class="text-gray-600 leading-relaxed text-lg">${product.description}</p>
                    </div>
                    
                    <!-- Rating -->
                    <div class="flex items-center gap-4 flex-wrap">
                        <div class="flex items-center gap-2">
                            <div class="flex text-yellow-400 text-lg">
                                ${Array(5).fill().map((_, i) => 
                                    `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                ).join('')}
                            </div>
                            <span class="text-gray-600 font-semibold text-lg">${product.rating}</span>
                        </div>
                        <span class="text-gray-400">•</span>
                        <span class="text-gray-600">${product.reviews} reviews</span>
                        <span class="text-gray-400">•</span>
                        <span class="flex items-center gap-1 text-green-600 font-semibold">
                            <i data-lucide="check-circle" class="h-4 w-4"></i>
                            In Stock
                        </span>
                    </div>
                    
                    <!-- Product Attributes -->
                    <div class="flex items-center gap-4 text-sm text-gray-600 bg-gray-50 rounded-xl p-4">
                        <span class="flex items-center gap-2">
                            <i data-lucide="package" class="h-4 w-4"></i>
                            <span class="font-medium">${product.weight}</span>
                        </span>
                        <span class="flex items-center gap-2">
                            <div class="w-4 h-4 rounded-full border-2 border-gray-300" style="background-color: ${getColorCode(product.color)};"></div>
                            <span class="font-medium capitalize">${product.color}</span>
                        </span>
                        <span class="bg-white px-3 py-1 rounded-full capitalize font-medium border">${product.size}</span>
                    </div>
                    
                    <!-- Price -->
                    <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-6">
                        <div class="flex items-center justify-between">
                            <div>
                                <div class="flex items-center gap-3 mb-2">
                                    <span class="text-3xl lg:text-4xl font-bold text-green-600">${product.price.toFixed(2)}</span>
                                    ${product.originalPrice ? `<span class="text-xl text-gray-500 line-through">${product.originalPrice.toFixed(2)}</span>` : ''}
                                </div>
                                ${savings > 0 ? `
                                    <div class="flex items-center gap-2">
                                        <span class="bg-red-500 text-white px-3 py-1 rounded-full text-sm font-bold">Save ${savings.toFixed(2)}</span>
                                        <span class="text-green-700 font-bold">${Math.round((savings / product.originalPrice) * 100)}% off</span>
                                    </div>
                                ` : '<span class="text-green-700 font-bold">Premium Quality Guaranteed</span>'}
                            </div>
                            <div class="text-center">
                                <div class="text-3xl mb-1">🚚</div>
                                <div class="text-sm text-gray-600 font-semibold">Free Delivery</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="space-y-4">
                        <div class="flex gap-3">
                            <button onclick="addToCart(${product.id}); closeQuickView();" class="flex-1 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white px-6 py-4 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2">
                                <i data-lucide="shopping-cart" class="h-5 w-5"></i>
                                Add to Cart
                            </button>
                            <button onclick="addToWishlist(${product.id})" class="p-4 border-2 border-gray-300 rounded-xl hover:border-red-500 hover:bg-red-50 transition-colors">
                                <i data-lucide="heart" class="h-5 w-5 text-gray-600 hover:text-red-500"></i>
                            </button>
                        </div>
                        
                        <button onclick="window.location.href='product-details.html?id=${product.id}'" class="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-3 rounded-xl font-semibold transition-colors">
                            View Full Details
                        </button>
                    </div>
                    
                    <!-- Trust Indicators -->
                    <div class="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
                        <div class="text-center">
                            <div class="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                                <i data-lucide="shield-check" class="h-5 w-5 text-green-600"></i>
                            </div>
                            <div class="text-xs font-bold text-gray-900">Certified Organic</div>
                        </div>
                        <div class="text-center">
                            <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                                <i data-lucide="truck" class="h-5 w-5 text-blue-600"></i>
                            </div>
                            <div class="text-xs font-bold text-gray-900">Free Delivery</div>
                        </div>
                        <div class="text-center">
                            <div class="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-2">
                                <i data-lucide="rotate-ccw" class="h-5 w-5 text-orange-600"></i>
                            </div>
                            <div class="text-xs font-bold text-gray-900">30-Day Returns</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    
    // Re-initialize Lucide icons
    setTimeout(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }, 100);
}

// Close quick view modal
function closeQuickView() {
    const modal = document.getElementById('quick-view-modal');
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Add to cart function
function addToCart(productId) {
    const product = enhancedProducts.find(p => p.id === productId);
    if (product) {
        showNotification(`${product.name} added to cart!`, 'success');
    }
}

// Add to wishlist function
function addToWishlist(productId) {
    const product = enhancedProducts.find(p => p.id === productId);
    if (product) {
        showNotification(`${product.name} added to wishlist!`, 'success');
    }
}

// Search function
function performSearch() {
    const searchInput = document.getElementById('search-input');
    const query = searchInput.value.trim();
    
    currentFilters.search = query;
    applyFilters();
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.initializeProductsPage = initializeProductsPage;
    window.applyFilters = applyFilters;
    window.sortProducts = sortProducts;
    window.clearAllFilters = clearAllFilters;
    window.removeFilter = removeFilter;
    window.updatePriceRange = updatePriceRange;
    window.toggleSizeFilter = toggleSizeFilter;
    window.toggleColorFilter = toggleColorFilter;
    window.toggleView = toggleView;
    window.toggleMobileFilters = toggleMobileFilters;
    window.openQuickView = openQuickView;
    window.closeQuickView = closeQuickView;
    window.addToCart = addToCart;
    window.addToWishlist = addToWishlist;
    window.performSearch = performSearch;
}