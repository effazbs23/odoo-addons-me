// Bootstrap-Compatible Mega Menu System for Natural Foods
console.log('🍔 Loading Bootstrap mega-menu.js...');

(function() {
    'use strict';
    
    // Comprehensive mega menu configuration for ALL navigation items
    const menuConfig = {
        'Home': {
            categories: [
                {
                    title: 'Quick Shop',
                    icon: '⚡',
                    items: [
                        { name: 'Daily Essentials', link: 'products.html?filter=daily', desc: 'Everyday organic products' },
                        { name: 'Fresh Produce', link: 'products.html?category=vegetables,fruits', desc: 'Today\'s fresh picks' },
                        { name: 'Best Sellers', link: 'products.html?filter=bestseller', desc: 'Customer favorites' },
                        { name: 'New Arrivals', link: 'products.html?filter=new', desc: 'Latest products' }
                    ]
                },
                {
                    title: 'Categories',
                    icon: '📦',
                    items: [
                        { name: 'All Products', link: 'products.html', desc: 'Browse everything' },
                        { name: 'Vegetables', link: 'products.html?category=vegetables', desc: 'Fresh organic vegetables' },
                        { name: 'Fruits', link: 'products.html?category=fruits', desc: 'Sweet seasonal fruits' },
                        { name: 'Dairy & Eggs', link: 'products.html?category=dairy', desc: 'Farm fresh dairy' }
                    ]
                },
                {
                    title: 'Recipes',
                    icon: '👨‍🍳',
                    items: [
                        { name: 'Recipe Collection', link: 'recipes.html', desc: 'Healthy recipe ideas' },
                        { name: 'Quick Meals', link: 'recipes.html?filter=quick', desc: '30-minute recipes' },
                        { name: 'Seasonal Recipes', link: 'recipes.html?filter=seasonal', desc: 'Current season favorites' },
                        { name: 'Meal Plans', link: 'recipes.html?filter=meal-plans', desc: 'Weekly meal planning' }
                    ]
                }
            ],
            featured: [
                { name: '🔥 Today\'s Deals', link: 'products.html?filter=daily-deals', badge: 'Limited Time' },
                { name: '🏆 Premium Quality', link: 'products.html?filter=premium', badge: 'Certified' },
                { name: '🌱 Organic Only', link: 'products.html?filter=organic', badge: '100% Natural' },
                { name: '🚚 Free Delivery', link: 'products.html?filter=free-shipping', badge: 'Orders $50+' }
            ]
        },
        'All Products': {
            categories: [
                {
                    title: 'Fresh Produce',
                    icon: '🥬',
                    items: [
                        { name: 'Organic Vegetables', link: 'products.html?category=vegetables', desc: 'Fresh & crisp vegetables' },
                        { name: 'Seasonal Fruits', link: 'products.html?category=fruits', desc: 'Sweet & juicy fruits' },
                        { name: 'Leafy Greens', link: 'products.html?category=leafy-greens', desc: 'Nutrient-rich greens' },
                        { name: 'Root Vegetables', link: 'products.html?category=root-vegetables', desc: 'Hearty & nutritious' },
                        { name: 'Fresh Herbs', link: 'products.html?category=herbs', desc: 'Aromatic cooking herbs' }
                    ]
                },
                {
                    title: 'Dairy & Proteins',
                    icon: '🥛',
                    items: [
                        { name: 'Organic Milk', link: 'products.html?category=dairy', desc: 'Fresh from local farms' },
                        { name: 'Artisan Cheese', link: 'products.html?category=cheese', desc: 'Premium aged cheese' },
                        { name: 'Free-Range Eggs', link: 'products.html?category=eggs', desc: 'From happy chickens' },
                        { name: 'Fresh Seafood', link: 'products.html?category=seafood', desc: 'Wild-caught & sustainable' },
                        { name: 'Plant Proteins', link: 'products.html?category=plant-protein', desc: 'Tofu, tempeh & more' }
                    ]
                },
                {
                    title: 'Pantry Essentials',
                    icon: '🌾',
                    items: [
                        { name: 'Organic Grains', link: 'products.html?category=grains', desc: 'Quinoa, rice & more' },
                        { name: 'Nuts & Seeds', link: 'products.html?category=nuts-seeds', desc: 'Premium quality' },
                        { name: 'Organic Oils', link: 'products.html?category=oils', desc: 'Cold-pressed oils' },
                        { name: 'Natural Sweeteners', link: 'products.html?category=sweeteners', desc: 'Honey, maple & agave' },
                        { name: 'Spices & Seasonings', link: 'products.html?category=spices', desc: 'Global flavors' }
                    ]
                }
            ],
            featured: [
                { name: '🔥 Hot Deals', link: 'products.html?filter=sale', badge: 'Up to 40% Off' },
                { name: '✨ New Arrivals', link: 'products.html?filter=new', badge: 'Just In' },
                { name: '⭐ Best Sellers', link: 'products.html?filter=bestseller', badge: 'Popular' },
                { name: '🌱 Seasonal Picks', link: 'products.html?filter=seasonal', badge: 'Limited Time' }
            ]
        },
        'Vegetables': {
            categories: [
                {
                    title: 'Leafy Greens',
                    icon: '🥬',
                    items: [
                        { name: 'Organic Spinach', link: 'products.html?category=vegetables&type=spinach', desc: 'Baby & mature leaves' },
                        { name: 'Fresh Kale', link: 'products.html?category=vegetables&type=kale', desc: 'Curly & baby kale' },
                        { name: 'Mixed Greens', link: 'products.html?category=vegetables&type=mixed-greens', desc: 'Salad blends' },
                        { name: 'Arugula', link: 'products.html?category=vegetables&type=arugula', desc: 'Peppery greens' }
                    ]
                },
                {
                    title: 'Root Vegetables',
                    icon: '🥕',
                    items: [
                        { name: 'Organic Carrots', link: 'products.html?category=vegetables&type=carrots', desc: 'Rainbow varieties' },
                        { name: 'Sweet Potatoes', link: 'products.html?category=vegetables&type=sweet-potatoes', desc: 'Orange & purple' },
                        { name: 'Fresh Beets', link: 'products.html?category=vegetables&type=beets', desc: 'Red & golden beets' },
                        { name: 'Turnips & Radishes', link: 'products.html?category=vegetables&type=turnips', desc: 'Crisp & fresh' }
                    ]
                },
                {
                    title: 'Premium Selection',
                    icon: '🌟',
                    items: [
                        { name: 'Heirloom Tomatoes', link: 'products.html?category=vegetables&type=heirloom', desc: 'Unique varieties' },
                        { name: 'Exotic Vegetables', link: 'products.html?category=vegetables&type=exotic', desc: 'Global varieties' },
                        { name: 'Microgreens', link: 'products.html?category=vegetables&type=microgreens', desc: 'Nutrient dense' }
                    ]
                }
            ],
            featured: [
                { name: '🥕 Seasonal Harvest', link: 'products.html?category=vegetables&filter=seasonal', badge: 'Fresh' },
                { name: '🏆 Premium Quality', link: 'products.html?category=vegetables&filter=premium', badge: 'Premium' },
                { name: '📦 Variety Boxes', link: 'products.html?category=vegetables&filter=boxes', badge: 'Value' }
            ]
        },
        'Account': {
            categories: [
                {
                    title: 'My Account',
                    icon: '👤',
                    items: [
                        { name: 'Profile Settings', link: 'login.html?tab=profile', desc: 'Update your information' },
                        { name: 'Order History', link: 'login.html?tab=orders', desc: 'View past purchases' },
                        { name: 'Address Book', link: 'login.html?tab=addresses', desc: 'Manage addresses' },
                        { name: 'Payment Methods', link: 'login.html?tab=payments', desc: 'Saved cards & methods' }
                    ]
                },
                {
                    title: 'Preferences',
                    icon: '⚙️',
                    items: [
                        { name: 'Dietary Preferences', link: 'login.html?tab=dietary', desc: 'Set dietary needs' },
                        { name: 'Delivery Preferences', link: 'login.html?tab=delivery', desc: 'Preferred times' },
                        { name: 'Communication', link: 'login.html?tab=notifications', desc: 'Email & SMS settings' },
                        { name: 'Privacy Settings', link: 'login.html?tab=privacy', desc: 'Data preferences' }
                    ]
                },
                {
                    title: 'Quick Actions',
                    icon: '⚡',
                    items: [
                        { name: 'Reorder Items', link: 'login.html?tab=reorder', desc: 'Buy again favorites' },
                        { name: 'Track Delivery', link: 'login.html?tab=tracking', desc: 'Current orders' },
                        { name: 'Customer Support', link: 'login.html?tab=support', desc: 'Get help' }
                    ]
                }
            ],
            featured: [
                { name: '🆕 New User', link: 'login.html?action=register', badge: 'Sign Up' },
                { name: '🔐 Sign In', link: 'login.html?action=login', badge: 'Login' },
                { name: '💳 Rewards Program', link: 'login.html?tab=rewards', badge: 'Join Now' },
                { name: '📱 Mobile App', link: '#mobile-app', badge: 'Download' }
            ]
        },
        'Cart': {
            categories: [
                {
                    title: 'Shopping Cart',
                    icon: '🛒',
                    items: [
                        { name: 'View Cart', link: 'cart.html', desc: 'Review your items' },
                        { name: 'Quick Checkout', link: 'checkout.html', desc: 'Fast & secure' },
                        { name: 'Saved Items', link: 'cart.html?tab=saved', desc: 'Items for later' },
                        { name: 'Recently Viewed', link: 'cart.html?tab=recent', desc: 'Products you viewed' }
                    ]
                },
                {
                    title: 'Checkout Options',
                    icon: '💳',
                    items: [
                        { name: 'Express Checkout', link: 'checkout.html?type=express', desc: 'One-click purchase' },
                        { name: 'Guest Checkout', link: 'checkout.html?type=guest', desc: 'No account needed' },
                        { name: 'Subscription Orders', link: 'checkout.html?type=subscription', desc: 'Auto-delivery' },
                        { name: 'Bulk Ordering', link: 'checkout.html?type=bulk', desc: 'Large quantities' }
                    ]
                },
                {
                    title: 'Delivery',
                    icon: '🚚',
                    items: [
                        { name: 'Same Day Delivery', link: 'checkout.html?delivery=same-day', desc: 'Order by 2pm' },
                        { name: 'Scheduled Delivery', link: 'checkout.html?delivery=scheduled', desc: 'Choose your time' },
                        { name: 'Pickup Options', link: 'checkout.html?delivery=pickup', desc: 'Store locations' }
                    ]
                }
            ],
            featured: [
                { name: '🆓 Free Shipping', link: 'cart.html?promo=free-ship', badge: 'Orders $50+' },
                { name: '🎯 Smart Suggestions', link: 'cart.html?tab=suggestions', badge: 'For You' },
                { name: '💰 Apply Coupon', link: 'cart.html?tab=coupons', badge: 'Save More' },
                { name: '🔄 Subscribe & Save', link: 'cart.html?tab=subscribe', badge: '15% Off' }
            ]
        }
    };
    
    let currentOpenMenu = null;
    let menuTimeout = null;
    
    // Initialize mega menu
    function initializeMegaMenu() {
        // Find navigation menus across all pages
        const navElements = document.querySelectorAll('nav .nav, nav .navbar-nav, .organic-nav .nav');
        
        navElements.forEach(nav => {
            addMegaMenuToNavigation(nav);
        });
        
        // Also check for individual buttons/links that might need mega menus
        const individualItems = document.querySelectorAll('header button, header a');
        individualItems.forEach(item => {
            const text = item.textContent.trim();
            const cleanText = text.replace(/[\u{1F300}-\u{1F9FF}]/gu, '').replace(/\s+/g, ' ').trim();
            
            let configKey = null;
            if (menuConfig[text]) {
                configKey = text;
            } else if (menuConfig[cleanText]) {
                configKey = cleanText;
            } else {
                // Check for partial matches
                for (const key in menuConfig) {
                    if (cleanText.toLowerCase().includes(key.toLowerCase()) || 
                        key.toLowerCase().includes(cleanText.toLowerCase())) {
                        configKey = key;
                        break;
                    }
                }
            }
            
            if (configKey && !item.closest('.mega-menu-dropdown')) {
                // Create a wrapper if the item doesn't have a parent li
                let wrapper = item.closest('.nav-item');
                if (!wrapper) {
                    wrapper = document.createElement('div');
                    wrapper.className = 'nav-item position-relative d-inline-block';
                    item.parentNode.insertBefore(wrapper, item);
                    wrapper.appendChild(item);
                }
                wrapper.classList.add('position-relative');
                setupMegaMenu(wrapper, configKey, menuConfig[configKey]);
                console.log(`✅ Added mega menu to header item: ${text} -> ${configKey}`);
            }
        });
        
        console.log('✅ Bootstrap mega menu initialized');
    }
    
    // Add mega menu to navigation
    function addMegaMenuToNavigation(nav) {
        const menuItems = nav.querySelectorAll('.nav-item, li');
        
        menuItems.forEach(item => {
            const link = item.querySelector('a') || item.querySelector('button') || item;
            let text = link.textContent.trim();
            
            // Clean up text by removing extra whitespace and emojis for matching
            const cleanText = text.replace(/[\u{1F300}-\u{1F9FF}]/gu, '').replace(/\s+/g, ' ').trim();
            
            // Try exact match first, then clean match
            let configKey = null;
            if (menuConfig[text]) {
                configKey = text;
            } else if (menuConfig[cleanText]) {
                configKey = cleanText;
            } else {
                // Try partial matches for common navigation patterns
                for (const key in menuConfig) {
                    if (text.toLowerCase().includes(key.toLowerCase()) || 
                        key.toLowerCase().includes(cleanText.toLowerCase())) {
                        configKey = key;
                        break;
                    }
                }
            }
            
            if (configKey) {
                item.classList.add('position-relative');
                setupMegaMenu(item, configKey, menuConfig[configKey]);
                console.log(`✅ Added mega menu to: ${text} -> ${configKey}`);
            }
        });
    }
    
    // Setup mega menu for a specific item
    function setupMegaMenu(menuItem, menuName, config) {
        // Create mega menu dropdown
        const megaMenu = createMegaMenuDropdown(config);
        megaMenu.id = `mega-menu-${menuName.toLowerCase().replace(/\s+/g, '-')}`;
        
        // Add to DOM
        menuItem.appendChild(megaMenu);
        
        // Add hover event listeners
        menuItem.addEventListener('mouseenter', () => showMegaMenu(megaMenu));
        menuItem.addEventListener('mouseleave', () => hideMegaMenu(megaMenu));
        
        // Add chevron indicator
        const link = menuItem.querySelector('a');
        if (link && !link.querySelector('.mega-menu-indicator')) {
            const indicator = document.createElement('i');
            indicator.className = 'mega-menu-indicator bi bi-chevron-down ms-1';
            link.appendChild(indicator);
        }
    }
    
    // Create mega menu dropdown HTML using Bootstrap classes
    function createMegaMenuDropdown(config) {
        const dropdown = document.createElement('div');
        
        // Determine dropdown size based on content
        const hasMultipleCategories = config.categories.length > 2;
        const minWidth = hasMultipleCategories ? '800px' : '600px';
        
        dropdown.className = 'mega-menu-dropdown position-absolute';
        dropdown.style.minWidth = minWidth;
        
        const gridCols = Math.min(config.categories.length + 1, 4); // +1 for featured section
        
        dropdown.innerHTML = `
            <div class="p-4">
                <div class="row g-4">
                    ${config.categories.map(category => `
                        <div class="col-lg-${Math.floor(12/gridCols)} col-md-6 col-12">
                            <div class="mega-menu-category">
                                <h6 class="d-flex align-items-center gap-2 mb-3 pb-2 border-bottom">
                                    <span class="fs-5">${category.icon}</span>
                                    <span>${category.title}</span>
                                </h6>
                                <ul class="list-unstyled space-y-3">
                                    ${category.items.map(item => `
                                        <li>
                                            <a href="${item.link}" class="mega-menu-item text-decoration-none">
                                                <div class="fw-medium text-dark">
                                                    ${item.name}
                                                </div>
                                                <div class="small text-muted mt-1">
                                                    ${item.desc}
                                                </div>
                                            </a>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        </div>
                    `).join('')}
                    
                    <!-- Featured Section -->
                    <div class="col-lg-${Math.floor(12/gridCols)} col-md-6 col-12">
                        <div class="mega-menu-featured p-3 h-100">
                            <h6 class="d-flex align-items-center gap-2 mb-3 pb-2 border-bottom border-success">
                                <span class="fs-5">⭐</span>
                                <span>Featured</span>
                            </h6>
                            <ul class="list-unstyled space-y-3">
                                ${config.featured.map(item => `
                                    <li>
                                        <a href="${item.link}" class="mega-menu-item text-decoration-none">
                                            <div class="d-flex align-items-center justify-content-between">
                                                <span class="fw-medium text-dark small">
                                                    ${item.name}
                                                </span>
                                                <span class="badge bg-success text-white rounded-pill small">
                                                    ${item.badge}
                                                </span>
                                            </div>
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                            
                            <!-- Call to Action -->
                            <div class="mt-4 pt-3 border-top border-success">
                                <a href="products.html" class="btn btn-success btn-sm w-100 d-flex align-items-center justify-content-center">
                                    <span>Browse All Products</span>
                                    <i class="bi bi-arrow-right ms-2"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        return dropdown;
    }
    
    // Show mega menu
    function showMegaMenu(megaMenu) {
        clearTimeout(menuTimeout);
        
        // Hide other open menus
        if (currentOpenMenu && currentOpenMenu !== megaMenu) {
            hideMegaMenu(currentOpenMenu);
        }
        
        megaMenu.classList.add('show');
        currentOpenMenu = megaMenu;
        console.log('🍔 Bootstrap mega menu shown');
    }
    
    // Hide mega menu
    function hideMegaMenu(megaMenu) {
        menuTimeout = setTimeout(() => {
            megaMenu.classList.remove('show');
            
            if (currentOpenMenu === megaMenu) {
                currentOpenMenu = null;
            }
            console.log('🍔 Bootstrap mega menu hidden');
        }, 150);
    }
    
    // Initialize when DOM is ready
    function initialize() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(initializeMegaMenu, 100); // Small delay to ensure DOM is fully ready
            });
        } else {
            setTimeout(initializeMegaMenu, 100);
        }
    }
    
    initialize();
    console.log('✅ Bootstrap mega menu system loaded');
    
})();