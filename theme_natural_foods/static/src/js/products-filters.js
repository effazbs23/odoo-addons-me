/**
 * Products Page Filtering System
 * Handles all filter logic, active filter management, and product filtering
 */

class ProductFilters {
    constructor() {
        this.activeFilters = {
            categories: [],
            brands: [],
            sizes: [],
            colors: [],
            special: [],
            priceRange: { min: 0, max: 50 },
            sortBy: 'newest'
        };
        
        this.initialize();
    }

    initialize() {
        console.log('🔍 Initializing product filters...');
        this.setupEventListeners();
        this.updatePriceRange();
    }

    setupEventListeners() {
        // Price range inputs
        const minPriceInput = document.getElementById('min-price-input');
        const maxPriceInput = document.getElementById('max-price-input');
        
        if (minPriceInput) minPriceInput.addEventListener('change', () => this.updatePriceFromInputs());
        if (maxPriceInput) maxPriceInput.addEventListener('change', () => this.updatePriceFromInputs());
    }

    // Price range functionality
    updatePriceRange() {
        const slider = document.getElementById('price-slider');
        if (!slider) return;
        
        const maxPrice = parseInt(slider.value);
        
        document.getElementById('current-max-price').textContent = maxPrice;
        document.getElementById('max-price-display').textContent = maxPrice;
        document.getElementById('max-price-input').value = maxPrice;
        
        this.activeFilters.priceRange.max = maxPrice;
        this.applyFilters();
    }

    updatePriceFromInputs() {
        const minInput = document.getElementById('min-price-input');
        const maxInput = document.getElementById('max-price-input');
        const slider = document.getElementById('price-slider');
        
        if (!minInput || !maxInput || !slider) return;
        
        let minPrice = parseInt(minInput.value) || 0;
        let maxPrice = parseInt(maxInput.value) || 50;
        
        // Validate range
        if (minPrice > maxPrice) {
            minPrice = maxPrice - 1;
            minInput.value = minPrice;
        }
        
        // Update displays
        document.getElementById('min-price-display').textContent = minPrice;
        document.getElementById('max-price-display').textContent = maxPrice;
        document.getElementById('current-max-price').textContent = maxPrice;
        slider.value = maxPrice;
        
        this.activeFilters.priceRange = { min: minPrice, max: maxPrice };
        this.applyFilters();
    }

    // Size filter functionality
    toggleSizeFilter(size) {
        const button = document.querySelector(`[data-size="${size}"]`);
        if (!button) return;
        
        const isActive = button.classList.contains('active');
        
        if (isActive) {
            button.classList.remove('active');
            this.activeFilters.sizes = this.activeFilters.sizes.filter(s => s !== size);
        } else {
            button.classList.add('active');
            this.activeFilters.sizes.push(size);
        }
        
        this.applyFilters();
    }

    // Color filter functionality
    toggleColorFilter(color) {
        const button = document.querySelector(`[data-color="${color}"]`);
        if (!button) return;
        
        const isActive = button.classList.contains('active');
        
        if (isActive) {
            button.classList.remove('active');
            this.activeFilters.colors = this.activeFilters.colors.filter(c => c !== color);
        } else {
            button.classList.add('active');
            this.activeFilters.colors.push(color);
        }
        
        this.applyFilters();
    }

    // Apply filters functionality
    applyFilters() {
        // Update categories
        this.activeFilters.categories = Array.from(document.querySelectorAll('input[name="category"]:checked'))
            .map(input => input.value);
        
        // Update brands
        this.activeFilters.brands = Array.from(document.querySelectorAll('input[name="brand"]:checked'))
            .map(input => input.value);
        
        // Update special offers
        this.activeFilters.special = Array.from(document.querySelectorAll('input[name="special"]:checked'))
            .map(input => input.value);
        
        this.updateActiveFiltersDisplay();
        this.filterProducts();
    }

    // Sort products functionality
    sortProducts() {
        const sortSelect = document.getElementById('sort-select');
        if (!sortSelect) return;
        
        this.activeFilters.sortBy = sortSelect.value;
        this.filterProducts();
    }

    // Update active filters display
    updateActiveFiltersDisplay() {
        const activeFiltersContainer = document.getElementById('active-filters');
        const activeFiltersList = document.getElementById('active-filters-list');
        
        if (!activeFiltersContainer || !activeFiltersList) return;
        
        // Clear existing tags
        activeFiltersList.innerHTML = '';
        
        let hasActiveFilters = false;
        
        // Add category filters
        this.activeFilters.categories.forEach(category => {
            this.addFilterTag(category, 'category');
            hasActiveFilters = true;
        });
        
        // Add brand filters
        this.activeFilters.brands.forEach(brand => {
            this.addFilterTag(brand, 'brand');
            hasActiveFilters = true;
        });
        
        // Add size filters
        this.activeFilters.sizes.forEach(size => {
            this.addFilterTag(size.toUpperCase(), 'size');
            hasActiveFilters = true;
        });
        
        // Add color filters
        this.activeFilters.colors.forEach(color => {
            this.addFilterTag(color, 'color');
            hasActiveFilters = true;
        });
        
        // Add special filters
        this.activeFilters.special.forEach(special => {
            const displayName = special === 'sale' ? 'Sale Items' : 
                              special === 'new' ? 'New Arrivals' : 'Featured';
            this.addFilterTag(displayName, 'special');
            hasActiveFilters = true;
        });
        
        // Add price range filter if not default
        if (this.activeFilters.priceRange.min > 0 || this.activeFilters.priceRange.max < 50) {
            this.addFilterTag(`$${this.activeFilters.priceRange.min} - $${this.activeFilters.priceRange.max}`, 'price');
            hasActiveFilters = true;
        }
        
        // Show/hide active filters container
        activeFiltersContainer.classList.toggle('hidden', !hasActiveFilters);
    }

    addFilterTag(text, type) {
        const activeFiltersList = document.getElementById('active-filters-list');
        if (!activeFiltersList) return;
        
        const tag = document.createElement('div');
        tag.className = 'filter-tag';
        tag.innerHTML = `
            ${text}
            <button onclick="window.productFilters.removeFilter('${text}', '${type}')" type="button">
                <i data-lucide="x" class="h-3 w-3"></i>
            </button>
        `;
        
        activeFiltersList.appendChild(tag);
        
        // Re-initialize Lucide icons for the new button
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    removeFilter(text, type) {
        switch (type) {
            case 'category':
                const categoryCheckbox = document.querySelector(`input[name="category"][value="${text}"]`);
                if (categoryCheckbox) categoryCheckbox.checked = false;
                break;
            case 'brand':
                const brandCheckbox = document.querySelector(`input[name="brand"][value="${text}"]`);
                if (brandCheckbox) brandCheckbox.checked = false;
                break;
            case 'size':
                const sizeButton = document.querySelector(`[data-size="${text.toLowerCase()}"]`);
                if (sizeButton) sizeButton.classList.remove('active');
                break;
            case 'color':
                const colorButton = document.querySelector(`[data-color="${text}"]`);
                if (colorButton) colorButton.classList.remove('active');
                break;
            case 'special':
                let specialValue = text === 'Sale Items' ? 'sale' : 
                                 text === 'New Arrivals' ? 'new' : 'featured';
                const specialCheckbox = document.querySelector(`input[name="special"][value="${specialValue}"]`);
                if (specialCheckbox) specialCheckbox.checked = false;
                break;
            case 'price':
                document.getElementById('min-price-input').value = 0;
                document.getElementById('max-price-input').value = 50;
                this.updatePriceFromInputs();
                return; // Skip applyFilters call since updatePriceFromInputs calls it
        }
        
        this.applyFilters();
    }

    // Clear all filters
    clearAllFilters() {
        // Clear checkboxes
        document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Clear size selections
        document.querySelectorAll('.size-option').forEach(button => {
            button.classList.remove('active');
        });
        
        // Clear color selections
        document.querySelectorAll('.color-swatch').forEach(button => {
            button.classList.remove('active');
        });
        
        // Reset price range
        const minPriceInput = document.getElementById('min-price-input');
        const maxPriceInput = document.getElementById('max-price-input');
        const priceSlider = document.getElementById('price-slider');
        
        if (minPriceInput) minPriceInput.value = 0;
        if (maxPriceInput) maxPriceInput.value = 50;
        if (priceSlider) priceSlider.value = 50;
        
        this.updatePriceRange();
        
        // Reset sort
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) sortSelect.value = 'newest';
        
        // Reset active filters
        this.activeFilters = {
            categories: [],
            brands: [],
            sizes: [],
            colors: [],
            special: [],
            priceRange: { min: 0, max: 50 },
            sortBy: 'newest'
        };
        
        this.applyFilters();
        
        if (window.ajaxCart) {
            window.ajaxCart.showToast('All filters cleared!', 'success');
        }
    }

    // Filter products based on active filters
    filterProducts() {
        if (typeof updateProductsDisplay === 'function') {
            updateProductsDisplay();
        }
        
        // Update product count
        const filteredCount = document.getElementById('filtered-count');
        if (filteredCount) {
            // This would be calculated based on actual filtering logic
            // For demo purposes, showing random count
            const count = Math.floor(Math.random() * 20) + 5;
            filteredCount.textContent = count;
        }
    }

    // Get current filters (for external use)
    getActiveFilters() {
        return { ...this.activeFilters };
    }

    // Set filters programmatically (for external use)
    setFilters(filters) {
        this.activeFilters = { ...this.activeFilters, ...filters };
        this.applyFilters();
    }
}

// Global functions for backward compatibility
function updatePriceRange() {
    if (window.productFilters) {
        window.productFilters.updatePriceRange();
    }
}

function updatePriceFromInputs() {
    if (window.productFilters) {
        window.productFilters.updatePriceFromInputs();
    }
}

function toggleSizeFilter(size) {
    if (window.productFilters) {
        window.productFilters.toggleSizeFilter(size);
    }
}

function toggleColorFilter(color) {
    if (window.productFilters) {
        window.productFilters.toggleColorFilter(color);
    }
}

function applyFilters() {
    if (window.productFilters) {
        window.productFilters.applyFilters();
    }
}

function sortProducts() {
    if (window.productFilters) {
        window.productFilters.sortProducts();
    }
}

function clearAllFilters() {
    if (window.productFilters) {
        window.productFilters.clearAllFilters();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.productFilters = new ProductFilters();
    console.log('✅ Product filters initialized');
});