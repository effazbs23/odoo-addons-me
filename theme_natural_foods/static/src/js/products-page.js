// Products page specific JavaScript

// Current filters and view state
let currentFilters = {
    search: '',
    category: '',
    minPrice: '',
    maxPrice: '',
    brands: [],
    specifications: [],
    onSale: false,
    newArrivals: false
};

let currentSort = 'featured';
let currentView = 'grid';
let currentPage = 1;
let itemsPerPage = 12;
let filteredProducts = [];

// Initialize products page
function initializeProductsPage() {
    // Parse URL parameters
    parseURLParameters();
    
    // Populate filters
    populateFilters();
    
    // Load products
    loadProducts();
    
    // Set up search debounce
    setupSearchDebounce();
}

// Parse URL parameters
function parseURLParameters() {
    const urlParams = new URLSearchParams(window.location.search);
    
    // Set filters from URL
    if (urlParams.get('search')) {
        currentFilters.search = urlParams.get('search');
        document.getElementById('filter-search').value = currentFilters.search;
    }
    
    if (urlParams.get('category')) {
        currentFilters.category = urlParams.get('category');
    }
    
    if (urlParams.get('filter') === 'new') {
        currentFilters.newArrivals = true;
    }
    
    if (urlParams.get('filter') === 'sale') {
        currentFilters.onSale = true;
    }
}

// Populate filters
function populateFilters() {
    populateCategoryFilter();
    populateBrandsFilter();
    populateSpecificationsFilter();
}

// Populate category filter
function populateCategoryFilter() {
    const container = document.getElementById('category-filter');
    const categories = getCategories();
    
    container.innerHTML = `
        <h3 class="font-medium text-gray-800 mb-3">Categories</h3>
        <div class="space-y-2">
            ${categories.map(category => `
                <label class="flex items-center">
                    <input 
                        type="radio" 
                        name="category" 
                        value="${category.id}"
                        ${currentFilters.category === category.id ? 'checked' : ''}
                        onchange="updateCategoryFilter('${category.id}')"
                        class="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    >
                    <span class="ml-2 text-sm flex items-center gap-2">
                        <span>${category.icon}</span>
                        ${category.name}
                    </span>
                </label>
            `).join('')}
            <label class="flex items-center">
                <input 
                    type="radio" 
                    name="category" 
                    value=""
                    ${currentFilters.category === '' ? 'checked' : ''}
                    onchange="updateCategoryFilter('')"
                    class="rounded border-gray-300 text-green-600 focus:ring-green-500"
                >
                <span class="ml-2 text-sm">All Categories</span>
            </label>
        </div>
    `;
}

// Populate brands filter
function populateBrandsFilter() {
    const container = document.getElementById('brands-filter');
    const brands = getBrands();
    
    container.innerHTML = `
        <h3 class="font-medium text-gray-800 mb-3">Brands</h3>
        <div class="space-y-2 max-h-48 overflow-y-auto">
            ${brands.map(brand => `
                <label class="flex items-center">
                    <input 
                        type="checkbox" 
                        value="${brand}"
                        ${currentFilters.brands.includes(brand) ? 'checked' : ''}
                        onchange="updateBrandFilter('${brand}', this.checked)"
                        class="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    >
                    <span class="ml-2 text-sm">${brand}</span>
                </label>
            `).join('')}
        </div>
    `;
}

// Populate specifications filter
function populateSpecificationsFilter() {
    const container = document.getElementById('specifications-filter');
    const specifications = getSpecifications();
    
    container.innerHTML = `
        <h3 class="font-medium text-gray-800 mb-3">Specifications</h3>
        <div class="space-y-2 max-h-48 overflow-y-auto">
            ${specifications.map(spec => `
                <label class="flex items-center">
                    <input 
                        type="checkbox" 
                        value="${spec}"
                        ${currentFilters.specifications.includes(spec) ? 'checked' : ''}
                        onchange="updateSpecificationFilter('${spec}', this.checked)"
                        class="rounded border-gray-300 text-green-600 focus:ring-green-500"
                    >
                    <span class="ml-2 text-sm">${spec}</span>
                </label>
            `).join('')}
        </div>
    `;
}

// Update category filter
function updateCategoryFilter(category) {
    currentFilters.category = category;
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}

// Update brand filter
function updateBrandFilter(brand, checked) {
    if (checked) {
        if (!currentFilters.brands.includes(brand)) {
            currentFilters.brands.push(brand);
        }
    } else {
        currentFilters.brands = currentFilters.brands.filter(b => b !== brand);
    }
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}

// Update specification filter
function updateSpecificationFilter(spec, checked) {
    if (checked) {
        if (!currentFilters.specifications.includes(spec)) {
            currentFilters.specifications.push(spec);
        }
    } else {
        currentFilters.specifications = currentFilters.specifications.filter(s => s !== spec);
    }
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}

// Update filters (for price and special offers)
function updateFilters() {
    // Get price range
    const minPrice = document.getElementById('min-price').value;
    const maxPrice = document.getElementById('max-price').value;
    
    currentFilters.minPrice = minPrice ? parseFloat(minPrice) : '';
    currentFilters.maxPrice = maxPrice ? parseFloat(maxPrice) : '';
    
    // Get special offers checkboxes specifically from the Special Offers section
    const specialOffersSection = document.querySelector('h3').parentNode;
    const saleCheckbox = Array.from(specialOffersSection.querySelectorAll('input[type="checkbox"]')).find(cb => 
        cb.nextElementSibling.textContent.trim() === 'On Sale'
    );
    const newCheckbox = Array.from(specialOffersSection.querySelectorAll('input[type="checkbox"]')).find(cb => 
        cb.nextElementSibling.textContent.trim() === 'New Arrivals'
    );
    
    currentFilters.onSale = saleCheckbox ? saleCheckbox.checked : false;
    currentFilters.newArrivals = newCheckbox ? newCheckbox.checked : false;
    
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}

// Search functionality
let searchTimeout;
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentFilters.search = document.getElementById('filter-search').value.trim();
        currentPage = 1;
        loadProducts();
        updateActiveFilters();
    }, 300);
}

function setupSearchDebounce() {
    // Override the global search to work with this page
    const headerSearch = document.getElementById('search-input');
    if (headerSearch && currentFilters.search) {
        headerSearch.value = currentFilters.search;
    }
}

// Load products
function loadProducts() {
    const container = document.getElementById('products-container');
    
    // Show loading state
    container.innerHTML = `
        <div class="flex items-center justify-center py-20">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
            <span class="ml-3 text-gray-600">Loading products...</span>
        </div>
    `;
    
    // Simulate loading delay
    setTimeout(() => {
        // Get filtered products
        filteredProducts = getFilteredProducts({
            search: currentFilters.search,
            category: currentFilters.category,
            minPrice: currentFilters.minPrice,
            maxPrice: currentFilters.maxPrice,
            sale: currentFilters.onSale,
            new: currentFilters.newArrivals,
            sortBy: currentSort
        });
        
        // Apply brand filter
        if (currentFilters.brands.length > 0) {
            filteredProducts = filteredProducts.filter(product => 
                currentFilters.brands.includes(product.brand)
            );
        }
        
        // Apply specification filter
        if (currentFilters.specifications.length > 0) {
            filteredProducts = filteredProducts.filter(product => 
                product.specifications && 
                currentFilters.specifications.some(spec => 
                    product.specifications.includes(spec)
                )
            );
        }
        
        // Update results count
        updateResultsCount();
        
        // Paginate results
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedProducts = filteredProducts.slice(startIndex, endIndex);
        
        if (paginatedProducts.length === 0) {
            showNoResults();
        } else {
            renderProducts(paginatedProducts);
        }
        
        // Update pagination
        updatePagination();
        
    }, 500);
}

// Render products
function renderProducts(products) {
    const container = document.getElementById('products-container');
    
    if (currentView === 'grid') {
        container.innerHTML = `
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                ${products.map(product => createProductCard(product)).join('')}
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="space-y-6">
                ${products.map(product => createProductListItem(product)).join('')}
            </div>
        `;
    }
    
    // Re-initialize icons
    lucide.createIcons();
}

// Create product list item (for list view)
function createProductListItem(product) {
    const salePrice = product.originalPrice ? product.price : null;
    const originalPrice = product.originalPrice;
    
    return `
        <div class="bg-white rounded-2xl shadow-lg border p-6 hover:shadow-xl transition-all duration-300">
            <div class="flex flex-col md:flex-row gap-6">
                <div class="md:w-48 flex-shrink-0">
                    <div class="relative">
                        <img src="${product.image}" alt="${product.name}" class="w-full h-48 md:h-32 object-cover rounded-lg">
                        ${product.sale ? '<div class="absolute top-2 left-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">SALE</div>' : ''}
                        ${product.isNew ? '<div class="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs font-bold">NEW</div>' : ''}
                    </div>
                </div>
                
                <div class="flex-1">
                    <div class="flex flex-col md:flex-row md:items-start md:justify-between h-full">
                        <div class="flex-1 mb-4 md:mb-0 md:mr-6">
                            <h3 class="text-xl font-semibold text-gray-800 mb-2 hover:text-green-600 cursor-pointer" onclick="navigateToProduct(${product.id})">${product.name}</h3>
                            <p class="text-gray-600 mb-3">${product.description}</p>
                            
                            <div class="flex items-center mb-3">
                                <div class="flex text-yellow-400 mr-2">
                                    ${Array(5).fill().map((_, i) => 
                                        `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                    ).join('')}
                                </div>
                                <span class="text-sm text-gray-500">(${product.rating})</span>
                                <span class="text-sm text-gray-400 mx-2">•</span>
                                <span class="text-sm text-gray-500">${product.brand}</span>
                            </div>
                            
                            ${product.specifications ? `
                                <div class="flex flex-wrap gap-1 mb-3">
                                    ${product.specifications.slice(0, 3).map(spec => 
                                        `<span class="bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs">${spec}</span>`
                                    ).join('')}
                                </div>
                            ` : ''}
                        </div>
                        
                        <div class="flex flex-col items-end">
                            <div class="mb-4">
                                <div class="text-right">
                                    <span class="text-2xl font-bold text-green-600">$${product.price.toFixed(2)}</span>
                                    ${originalPrice ? `<div class="text-sm text-gray-500 line-through">$${originalPrice.toFixed(2)}</div>` : ''}
                                </div>
                            </div>
                            
                            <div class="flex gap-2">
                                <button onclick="navigateToProduct(${product.id})" class="border border-green-600 text-green-600 hover:bg-green-50 px-4 py-2 rounded-lg font-medium transition-colors">
                                    View Details
                                </button>
                                <button onclick="addToCart(${product.id})" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors">
                                    Add to Cart
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Show no results
function showNoResults() {
    const container = document.getElementById('products-container');
    container.innerHTML = `
        <div class="text-center py-20">
            <div class="text-gray-400 text-6xl mb-6">🔍</div>
            <h3 class="text-2xl font-semibold text-gray-800 mb-2">No products found</h3>
            <p class="text-gray-600 mb-6">Try adjusting your filters or search terms</p>
            <button onclick="clearAllFilters()" class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
                Clear All Filters
            </button>
        </div>
    `;
}

// Update results count
function updateResultsCount() {
    const countElement = document.getElementById('results-count');
    const totalResults = filteredProducts.length;
    const startItem = totalResults > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0;
    const endItem = Math.min(currentPage * itemsPerPage, totalResults);
    
    countElement.textContent = `Showing ${startItem}-${endItem} of ${totalResults} products`;
}

// Update pagination
function updatePagination() {
    const container = document.getElementById('pagination-container');
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    container.innerHTML = createPagination(currentPage, totalPages, 'goToPage');
}

// Go to page
function goToPage(page) {
    currentPage = page;
    loadProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Update sort
function updateSort() {
    currentSort = document.getElementById('sort-select').value;
    currentPage = 1;
    loadProducts();
}

// Set view
function setView(view) {
    currentView = view;
    
    // Update button states
    const gridBtn = document.getElementById('grid-view-btn');
    const listBtn = document.getElementById('list-view-btn');
    
    if (view === 'grid') {
        gridBtn.className = 'p-2 bg-green-600 text-white';
        listBtn.className = 'p-2 bg-white text-gray-600 hover:bg-gray-50';
    } else {
        gridBtn.className = 'p-2 bg-white text-gray-600 hover:bg-gray-50';
        listBtn.className = 'p-2 bg-green-600 text-white';
    }
    
    // Re-render products
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedProducts = filteredProducts.slice(startIndex, endIndex);
    renderProducts(paginatedProducts);
}

// Update active filters display
function updateActiveFilters() {
    const container = document.getElementById('active-filters');
    const listContainer = document.getElementById('active-filters-list');
    
    let activeFilters = [];
    
    // Add active filters to array
    if (currentFilters.search) {
        activeFilters.push({ type: 'search', value: currentFilters.search, label: `Search: "${currentFilters.search}"` });
    }
    
    if (currentFilters.category) {
        const category = getCategories().find(c => c.id === currentFilters.category);
        activeFilters.push({ type: 'category', value: currentFilters.category, label: category ? category.name : currentFilters.category });
    }
    
    if (currentFilters.minPrice || currentFilters.maxPrice) {
        const priceLabel = `Price: $${currentFilters.minPrice || '0'} - $${currentFilters.maxPrice || '∞'}`;
        activeFilters.push({ type: 'price', value: 'price', label: priceLabel });
    }
    
    currentFilters.brands.forEach(brand => {
        activeFilters.push({ type: 'brand', value: brand, label: brand });
    });
    
    currentFilters.specifications.forEach(spec => {
        activeFilters.push({ type: 'specification', value: spec, label: spec });
    });
    
    if (currentFilters.onSale) {
        activeFilters.push({ type: 'sale', value: 'sale', label: 'On Sale' });
    }
    
    if (currentFilters.newArrivals) {
        activeFilters.push({ type: 'new', value: 'new', label: 'New Arrivals' });
    }
    
    if (activeFilters.length > 0) {
        container.classList.remove('hidden');
        listContainer.innerHTML = activeFilters.map(filter => `
            <span class="inline-flex items-center gap-2 bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                ${filter.label}
                <button onclick="removeFilter('${filter.type}', '${filter.value}')" class="hover:text-green-900">
                    <i data-lucide="x" class="h-3 w-3"></i>
                </button>
            </span>
        `).join('');
        lucide.createIcons();
    } else {
        container.classList.add('hidden');
    }
}

// Remove filter
function removeFilter(type, value) {
    switch (type) {
        case 'search':
            currentFilters.search = '';
            document.getElementById('filter-search').value = '';
            break;
        case 'category':
            currentFilters.category = '';
            break;
        case 'price':
            currentFilters.minPrice = '';
            currentFilters.maxPrice = '';
            document.getElementById('min-price').value = '';
            document.getElementById('max-price').value = '';
            break;
        case 'brand':
            currentFilters.brands = currentFilters.brands.filter(b => b !== value);
            break;
        case 'specification':
            currentFilters.specifications = currentFilters.specifications.filter(s => s !== value);
            break;
        case 'sale':
            currentFilters.onSale = false;
            break;
        case 'new':
            currentFilters.newArrivals = false;
            break;
    }
    
    // Re-populate filters to update checkboxes
    populateFilters();
    
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}

// Clear all filters
function clearAllFilters() {
    currentFilters = {
        search: '',
        category: '',
        minPrice: '',
        maxPrice: '',
        brands: [],
        specifications: [],
        onSale: false,
        newArrivals: false
    };
    
    // Clear form inputs
    document.getElementById('filter-search').value = '';
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    
    // Re-populate filters
    populateFilters();
    
    currentPage = 1;
    loadProducts();
    updateActiveFilters();
}