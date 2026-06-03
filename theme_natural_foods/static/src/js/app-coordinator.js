// App Coordinator - Manages the complete application lifecycle
// This file coordinates all modules and ensures proper initialization

class OrganicStoreApp {
    constructor() {
        this.initialized = false;
        this.templateLoader = null;
        this.loadingStartTime = Date.now();
        this.initializationSteps = [];
    }

    log(message, type = 'info') {
        const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
        const emoji = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
        console.log(`${emoji} [${timestamp}] ${message}`);
        this.initializationSteps.push({ message, type, timestamp });
    }

    async initialize() {
        this.log('🚀 Starting Natural Foods application initialization');

        try {
            // Step 1: Check template loader
            if (typeof templateLoader === 'undefined') {
                throw new Error('Template loader not available - check js/template-loader.js');
            }
            this.templateLoader = templateLoader;
            this.log('Template loader ready', 'success');

            // Step 2: Load all templates
            await this.loadTemplates();

            // Step 3: Initialize Lucide icons
            this.initializeLucideIcons();

            // Step 4: Initialize core modules
            await this.initializeCoreModules();

            // Step 5: Initialize page-specific functionality
            await this.initializePageFunctionality();

            // Step 6: Final setup
            this.finalizeInitialization();

            this.initialized = true;
            const loadTime = Date.now() - this.loadingStartTime;
            this.log(`🎉 Application initialized successfully in ${loadTime}ms`, 'success');

            // Show welcome notification
            if (typeof showNotification === 'function') {
                showNotification('🌿 Welcome to Natural Foods! All systems ready.', 'success');
            }

        } catch (error) {
            this.log(`💥 Critical initialization error: ${error.message}`, 'error');
            this.handleInitializationError(error);
        }
    }

    async loadTemplates() {
        this.log('📄 Loading page templates...');
        
        const templates = [
            { containerId: 'header-container', templatePath: 'templates/header.html' },
            { containerId: 'hero-container', templatePath: 'templates/hero-section.html' },
            { containerId: 'categories-container', templatePath: 'templates/categories-section.html' },
            { containerId: 'product-sections-container', templatePath: 'templates/product-sections.html' },
            { containerId: 'product-tabs-container', templatePath: 'templates/product-tabs-section.html' },
            { containerId: 'remaining-sections-container', templatePath: 'templates/remaining-sections.html' },
            { containerId: 'footer-container', templatePath: 'templates/footer.html' }
        ];

        try {
            await this.templateLoader.loadMultipleTemplates(templates);
            this.log(`All ${templates.length} templates loaded successfully`, 'success');
        } catch (error) {
            throw new Error(`Template loading failed: ${error.message}`);
        }
    }

    initializeLucideIcons() {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
            this.log('Lucide icons initialized', 'success');
        } else {
            this.log('Lucide icons not available', 'warning');
        }
    }

    async initializeCoreModules() {
        this.log('⚙️ Initializing core modules...');

        // Initialize cart functionality
        if (typeof initializeDemoCartItems === 'function') {
            initializeDemoCartItems();
            this.log('Demo cart items initialized', 'success');
        } else {
            this.log('initializeDemoCartItems not found', 'warning');
        }

        // Initialize cart display
        if (typeof updateCartDisplay === 'function') {
            updateCartDisplay();
            this.log('Cart display initialized', 'success');
        } else {
            this.log('updateCartDisplay not found', 'warning');
        }

        // Initialize wishlist
        if (typeof initializeWishlist === 'function') {
            initializeWishlist();
            this.log('Wishlist initialized', 'success');
        } else {
            this.log('initializeWishlist not found', 'warning');
        }

        // Initialize product tabs
        if (typeof initializeProductTabs === 'function') {
            initializeProductTabs();
            this.log('Product tabs initialized', 'success');
        } else {
            this.log('initializeProductTabs not found', 'warning');
        }

        // Populate home page sections
        if (typeof populateHomePageSections === 'function') {
            populateHomePageSections();
            this.log('Home page sections populated', 'success');
        } else {
            this.log('populateHomePageSections not found', 'warning');
        }
    }

    async initializePageFunctionality() {
        this.log('🎯 Initializing page-specific functionality...');

        // Initialize search
        this.initializeSearch();

        // Initialize keyboard shortcuts
        this.initializeKeyboardShortcuts();

        // Initialize hero slider (with delay to ensure DOM is ready)
        setTimeout(() => {
            this.initializeHeroSlider();
        }, 300);
    }

    initializeSearch() {
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    const query = searchInput.value.trim();
                    if (query) {
                        if (typeof performSearch === 'function') {
                            performSearch();
                        } else {
                            window.location.href = `products.html?search=${encodeURIComponent(query)}`;
                        }
                    }
                }
            });
            this.log('Search functionality initialized', 'success');
        } else {
            this.log('Search input not found', 'warning');
        }
    }

    initializeKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Escape key to close modals
            if (e.key === 'Escape') {
                const ajaxCart = document.querySelector('.ajax-cart-modal');
                if (ajaxCart && typeof hideAjaxCartPopup === 'function') {
                    hideAjaxCartPopup();
                    return;
                }
                
                const quickView = document.querySelector('.quick-view-modal-backdrop');
                if (quickView) {
                    quickView.remove();
                    return;
                }
            }
            
            // Ctrl/Cmd + K for search focus
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.getElementById('search-input');
                if (searchInput) {
                    searchInput.focus();
                    searchInput.select();
                }
            }
        });
        this.log('Keyboard shortcuts initialized', 'success');
    }

    initializeHeroSlider() {
        const slides = document.querySelectorAll('.slider-slide');
        const dots = document.querySelectorAll('.slider-dot');
        const totalSlides = slides.length;
        
        if (totalSlides === 0) {
            this.log('No hero slides found', 'warning');
            return;
        }

        let currentSlide = 0;

        const showSlide = (index) => {
            slides.forEach((slide, i) => {
                slide.style.opacity = '0';
                slide.style.transform = i < index ? 'translateX(-100%)' : i > index ? 'translateX(100%)' : 'translateX(0)';
            });
            
            if (slides[index]) {
                slides[index].style.opacity = '1';
                slides[index].style.transform = 'translateX(0)';
            }
            
            dots.forEach((dot, i) => {
                if (dot) {
                    dot.style.opacity = i === index ? '1' : '0.5';
                }
            });
            
            currentSlide = index;
        };

        const nextSlide = () => {
            const next = (currentSlide + 1) % totalSlides;
            showSlide(next);
        };

        const previousSlide = () => {
            const prev = (currentSlide - 1 + totalSlides) % totalSlides;
            showSlide(prev);
        };

        const goToSlide = (index) => {
            if (index >= 0 && index < totalSlides) {
                showSlide(index);
            }
        };

        // Auto-play slider
        setInterval(nextSlide, 5000);

        // Make functions global
        window.nextSlide = nextSlide;
        window.previousSlide = previousSlide;
        window.goToSlide = goToSlide;

        this.log(`Hero slider initialized with ${totalSlides} slides`, 'success');
    }

    finalizeInitialization() {
        this.log('🏁 Finalizing initialization...');

        // Remove loading overlay if it exists
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            setTimeout(() => {
                loadingOverlay.style.opacity = '0';
                setTimeout(() => {
                    loadingOverlay.remove();
                }, 300);
            }, 500);
        }

        // Add some visual feedback
        document.body.classList.add('app-loaded');
        
        this.log('Application finalized', 'success');
    }

    handleInitializationError(error) {
        console.error('🚨 Application initialization failed:', error);
        
        // Remove loading overlay and show error
        const loadingOverlay = document.getElementById('loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.innerHTML = `
                <div class="text-center max-w-md mx-auto">
                    <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span class="text-red-600 text-2xl">⚠️</span>
                    </div>
                    <h3 class="text-xl font-bold text-red-600 mb-2">Loading Failed</h3>
                    <p class="text-gray-600 mb-4">${error.message}</p>
                    <div class="space-y-2">
                        <button onclick="location.reload()" class="block w-full bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium">
                            Refresh Page
                        </button>
                        <button onclick="window.location.href='debug.html'" class="block w-full bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium">
                            Debug Mode
                        </button>
                    </div>
                </div>
            `;
        }
    }

    // Debug method to show initialization steps
    showDebugInfo() {
        console.group('🔧 Initialization Debug Info');
        this.initializationSteps.forEach(step => {
            console.log(`${step.type === 'success' ? '✅' : step.type === 'error' ? '❌' : step.type === 'warning' ? '⚠️' : 'ℹ️'} ${step.message}`);
        });
        console.groupEnd();
    }
}

// Create global app instance
const organicStoreApp = new OrganicStoreApp();

// Make it available globally
window.organicStoreApp = organicStoreApp;

// Export initialization function
window.initializeOrganicStore = () => organicStoreApp.initialize();

console.log('🎯 App Coordinator loaded successfully');