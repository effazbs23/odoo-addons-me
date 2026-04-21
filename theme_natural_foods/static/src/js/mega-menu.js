// Mega Menu System for Natural Foods Static HTML
console.log('🍔 Loading mega-menu.js...');

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
                        { name: 'Fresh Produce', link: 'products.html?category=vegetables,fruits', desc: 'Today\\'s fresh picks' },
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
                { name: '🔥 Today\\'s Deals', link: 'products.html?filter=daily-deals', badge: 'Limited Time' },
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
        'Recipes': {
            categories: [
                {
                    title: 'By Meal Type',
                    icon: '🍽️',
                    items: [
                        { name: 'Breakfast Recipes', link: 'recipes.html?category=breakfast', desc: 'Start your day right' },
                        { name: 'Lunch Ideas', link: 'recipes.html?category=lunch', desc: 'Midday nourishment' },
                        { name: 'Dinner Recipes', link: 'recipes.html?category=dinner', desc: 'Evening meals' },
                        { name: 'Healthy Snacks', link: 'recipes.html?category=snack', desc: 'Quick energy boosts' },
                        { name: 'Desserts', link: 'recipes.html?category=dessert', desc: 'Sweet healthy treats' }
                    ]
                },
                {
                    title: 'By Diet Type',
                    icon: '🥗',
                    items: [
                        { name: 'Vegan Recipes', link: 'recipes.html?filter=vegan', desc: 'Plant-based meals' },
                        { name: 'Gluten-Free', link: 'recipes.html?filter=gluten-free', desc: 'Safe for celiac' },
                        { name: 'Keto-Friendly', link: 'recipes.html?filter=keto', desc: 'Low-carb options' },
                        { name: 'Paleo Recipes', link: 'recipes.html?filter=paleo', desc: 'Ancestral diet' },
                        { name: 'Raw Food', link: 'recipes.html?filter=raw', desc: 'Uncooked goodness' }
                    ]
                },
                {
                    title: 'Beverages & More',
                    icon: '🥤',
                    items: [
                        { name: 'Green Smoothies', link: 'recipes.html?category=smoothie', desc: 'Nutrient-packed drinks' },
                        { name: 'Fresh Juices', link: 'recipes.html?category=juice', desc: 'Cold-pressed goodness' },
                        { name: 'Herbal Teas', link: 'recipes.html?category=tea', desc: 'Healing blends' },
                        { name: 'Detox Drinks', link: 'recipes.html?filter=detox', desc: 'Cleansing recipes' },
                        { name: 'Fermented Foods', link: 'recipes.html?category=fermented', desc: 'Gut-healthy options' }
                    ]
                }
            ],
            featured: [
                { name: '⏰ Quick Recipes', link: 'recipes.html?filter=quick', badge: '< 30min' },
                { name: '👨‍🍳 Chef\'s Choice', link: 'recipes.html?filter=featured', badge: 'Featured' },
                { name: '🔥 Trending Now', link: 'recipes.html?filter=trending', badge: 'Hot' },
                { name: '🥇 Top Rated', link: 'recipes.html?filter=top-rated', badge: '4.8★' }
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
        'Fruits': {
            categories: [
                {
                    title: 'Tree Fruits',
                    icon: '🍎',
                    items: [
                        { name: 'Organic Apples', link: 'products.html?category=fruits&type=apples', desc: 'Multiple varieties' },
                        { name: 'Fresh Pears', link: 'products.html?category=fruits&type=pears', desc: 'Anjou & Bartlett' },
                        { name: 'Stone Fruits', link: 'products.html?category=fruits&type=stone-fruits', desc: 'Peaches & plums' },
                        { name: 'Citrus Fruits', link: 'products.html?category=fruits&type=citrus', desc: 'Oranges & lemons' }
                    ]
                },
                {
                    title: 'Berries',
                    icon: '🫐',
                    items: [
                        { name: 'Organic Berries', link: 'products.html?category=fruits&type=berries', desc: 'Strawberries & more' },
                        { name: 'Blueberries', link: 'products.html?category=fruits&type=blueberries', desc: 'Antioxidant rich' },
                        { name: 'Raspberries', link: 'products.html?category=fruits&type=raspberries', desc: 'Fresh & frozen' },
                        { name: 'Blackberries', link: 'products.html?category=fruits&type=blackberries', desc: 'Sweet & tart' }
                    ]
                },
                {
                    title: 'Exotic & Tropical',
                    icon: '🥭',
                    items: [
                        { name: 'Tropical Fruits', link: 'products.html?category=fruits&type=tropical', desc: 'Mango & pineapple' },
                        { name: 'Avocados', link: 'products.html?category=fruits&type=avocados', desc: 'Hass & organic' },
                        { name: 'Specialty Fruits', link: 'products.html?category=fruits&type=specialty', desc: 'Dragon fruit & more' }
                    ]
                }
            ],
            featured: [
                { name: '🌞 Seasonal Picks', link: 'products.html?category=fruits&filter=seasonal', badge: 'Seasonal' },
                { name: '🍓 Berry Collection', link: 'products.html?category=fruits&filter=berries', badge: 'Popular' },
                { name: '🥭 Exotic Selection', link: 'products.html?category=fruits&filter=exotic', badge: 'Unique' }
            ]
        },
        'Dairy': {
            categories: [
                {
                    title: 'Fresh Milk',
                    icon: '🥛',
                    items: [
                        { name: 'Organic Whole Milk', link: 'products.html?category=dairy&type=whole-milk', desc: 'Grass-fed cows' },
                        { name: 'Low-Fat Milk', link: 'products.html?category=dairy&type=low-fat-milk', desc: '1% & 2% options' },
                        { name: 'Plant-Based Milk', link: 'products.html?category=dairy&type=plant-milk', desc: 'Almond, oat & soy' },
                        { name: 'Raw Milk', link: 'products.html?category=dairy&type=raw-milk', desc: 'Unpasteurized' }
                    ]
                },
                {
                    title: 'Cheese & Yogurt',
                    icon: '🧀',
                    items: [
                        { name: 'Artisan Cheese', link: 'products.html?category=dairy&type=cheese', desc: 'Local & imported' },
                        { name: 'Greek Yogurt', link: 'products.html?category=dairy&type=greek-yogurt', desc: 'High protein' },
                        { name: 'Probiotic Yogurt', link: 'products.html?category=dairy&type=probiotic', desc: 'Gut health' },
                        { name: 'Cottage Cheese', link: 'products.html?category=dairy&type=cottage-cheese', desc: 'Low fat options' }
                    ]
                },
                {
                    title: 'Eggs & More',
                    icon: '🥚',
                    items: [
                        { name: 'Free-Range Eggs', link: 'products.html?category=dairy&type=eggs', desc: 'Pasture raised' },
                        { name: 'Organic Butter', link: 'products.html?category=dairy&type=butter', desc: 'Grass-fed cream' },
                        { name: 'Heavy Cream', link: 'products.html?category=dairy&type=cream', desc: 'Cooking & whipping' }
                    ]
                }
            ],
            featured: [
                { name: '🥛 Farm Fresh', link: 'products.html?category=dairy&filter=farm-fresh', badge: 'Local' },
                { name: '🧀 Artisan Selection', link: 'products.html?category=dairy&filter=artisan', badge: 'Premium' },
                { name: '🌱 Plant-Based', link: 'products.html?category=dairy&filter=plant-based', badge: 'Vegan' }
            ]
        },
        'Meat & Fish': {
            categories: [
                {
                    title: 'Fresh Seafood',
                    icon: '🐟',
                    items: [
                        { name: 'Wild Salmon', link: 'products.html?category=seafood&type=salmon', desc: 'Atlantic & Pacific' },
                        { name: 'Fresh Cod', link: 'products.html?category=seafood&type=cod', desc: 'Sustainable catch' },
                        { name: 'Organic Shrimp', link: 'products.html?category=seafood&type=shrimp', desc: 'Farm-raised' },
                        { name: 'Sea Bass', link: 'products.html?category=seafood&type=bass', desc: 'Mediterranean style' }
                    ]
                },
                {
                    title: 'Premium Cuts',
                    icon: '🥩',
                    items: [
                        { name: 'Grass-Fed Beef', link: 'products.html?category=meat&type=beef', desc: 'Premium quality' },
                        { name: 'Free-Range Chicken', link: 'products.html?category=meat&type=chicken', desc: 'Organic certified' },
                        { name: 'Heritage Pork', link: 'products.html?category=meat&type=pork', desc: 'Ethically raised' },
                        { name: 'Wild Game', link: 'products.html?category=meat&type=game', desc: 'Venison & more' }
                    ]
                },
                {
                    title: 'Prepared Options',
                    icon: '🍖',
                    items: [
                        { name: 'Marinated Meats', link: 'products.html?category=meat&type=marinated', desc: 'Ready to cook' },
                        { name: 'Smoked Fish', link: 'products.html?category=seafood&type=smoked', desc: 'Traditional methods' },
                        { name: 'Deli Selections', link: 'products.html?category=meat&type=deli', desc: 'Sliced fresh daily' }
                    ]
                }
            ],
            featured: [
                { name: '🌊 Wild Caught', link: 'products.html?category=seafood&filter=wild', badge: 'Sustainable' },
                { name: '🐄 Grass Fed', link: 'products.html?category=meat&filter=grass-fed', badge: 'Premium' },
                { name: '🏆 Chef\\'s Choice', link: 'products.html?category=seafood,meat&filter=premium', badge: 'Featured' }
            ]
        },
        'Bakery': {
            categories: [
                {
                    title: 'Fresh Breads',
                    icon: '🍞',
                    items: [
                        { name: 'Artisan Sourdough', link: 'products.html?category=bakery&type=sourdough', desc: 'Traditional recipes' },
                        { name: 'Whole Grain Breads', link: 'products.html?category=bakery&type=whole-grain', desc: 'Healthy options' },
                        { name: 'Gluten-Free Options', link: 'products.html?category=bakery&type=gluten-free', desc: 'Safe alternatives' },
                        { name: 'Specialty Rolls', link: 'products.html?category=bakery&type=rolls', desc: 'Daily fresh baked' }
                    ]
                },
                {
                    title: 'Pastries & Sweets',
                    icon: '🥐',
                    items: [
                        { name: 'Fresh Croissants', link: 'products.html?category=bakery&type=croissants', desc: 'Buttery & flaky' },
                        { name: 'Organic Muffins', link: 'products.html?category=bakery&type=muffins', desc: 'Morning favorites' },
                        { name: 'Healthy Cookies', link: 'products.html?category=bakery&type=cookies', desc: 'Natural sweeteners' },
                        { name: 'Seasonal Pastries', link: 'products.html?category=bakery&type=seasonal', desc: 'Limited time' }
                    ]
                },
                {
                    title: 'Specialty Items',
                    icon: '🧁',
                    items: [
                        { name: 'Custom Cakes', link: 'products.html?category=bakery&type=cakes', desc: 'Made to order' },
                        { name: 'Pizza Dough', link: 'products.html?category=bakery&type=dough', desc: 'Fresh daily' },
                        { name: 'Sandwich Wraps', link: 'products.html?category=bakery&type=wraps', desc: 'Healthy options' }
                    ]
                }
            ],
            featured: [
                { name: '🌅 Fresh Daily', link: 'products.html?category=bakery&filter=daily', badge: 'Baked Today' },
                { name: '🌾 Organic Flour', link: 'products.html?category=bakery&filter=organic', badge: 'Certified' },
                { name: '🍰 Custom Orders', link: 'products.html?category=bakery&filter=custom', badge: 'Available' }
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
        'Wishlist': {
            categories: [
                {
                    title: 'My Lists',
                    icon: '💝',
                    items: [
                        { name: 'Favorites', link: 'wishlist.html?tab=favorites', desc: 'Your liked products' },
                        { name: 'Save for Later', link: 'wishlist.html?tab=saved', desc: 'Items to buy later' },
                        { name: 'Gift Ideas', link: 'wishlist.html?tab=gifts', desc: 'Perfect for gifting' },
                        { name: 'Seasonal Items', link: 'wishlist.html?tab=seasonal', desc: 'Holiday specials' }
                    ]
                },
                {
                    title: 'Shopping Lists',
                    icon: '📝',
                    items: [
                        { name: 'Weekly Shopping', link: 'wishlist.html?tab=weekly', desc: 'Regular purchases' },
                        { name: 'Meal Planning', link: 'wishlist.html?tab=meals', desc: 'Recipe ingredients' },
                        { name: 'Bulk Orders', link: 'wishlist.html?tab=bulk', desc: 'Large quantities' },
                        { name: 'Special Occasions', link: 'wishlist.html?tab=occasions', desc: 'Party planning' }
                    ]
                },
                {
                    title: 'Sharing',
                    icon: '🔗',
                    items: [
                        { name: 'Share List', link: 'wishlist.html?action=share', desc: 'Send to family/friends' },
                        { name: 'Registry', link: 'wishlist.html?tab=registry', desc: 'Wedding & baby' },
                        { name: 'Gift Cards', link: 'wishlist.html?tab=gift-cards', desc: 'Send as gifts' }
                    ]
                }
            ],
            featured: [
                { name: '🎁 Gift Registry', link: 'wishlist.html?tab=registry', badge: 'Create' },
                { name: '📧 Share Lists', link: 'wishlist.html?action=share', badge: 'Family' },
                { name: '🔔 Price Alerts', link: 'wishlist.html?tab=alerts', badge: 'Notify Me' },
                { name: '⭐ Top Picks', link: 'wishlist.html?filter=recommended', badge: 'For You' }
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
        const navElements = document.querySelectorAll('nav ul, nav .flex, .header-actions, header .flex');
        
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
                let wrapper = item.closest('li');
                if (!wrapper) {
                    wrapper = document.createElement('div');
                    wrapper.className = 'relative inline-block';
                    item.parentNode.insertBefore(wrapper, item);
                    wrapper.appendChild(item);
                }
                wrapper.classList.add('relative');
                setupMegaMenu(wrapper, configKey, menuConfig[configKey]);
                console.log(`✅ Added mega menu to header item: ${text} -> ${configKey}`);
            }
        });
        
        console.log('✅ Mega menu initialized');
    }
    
    // Add mega menu to navigation
    function addMegaMenuToNavigation(nav) {
        const menuItems = nav.querySelectorAll('li, > a, > button');
        
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
                item.classList.add('relative');
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
            indicator.className = 'mega-menu-indicator ml-1 h-3 w-3';
            indicator.setAttribute('data-lucide', 'chevron-down');
            link.appendChild(indicator);
        }
    }
    
    // Create mega menu dropdown HTML
    function createMegaMenuDropdown(config) {
        const dropdown = document.createElement('div');
        
        // Determine dropdown size based on content
        const hasMultipleCategories = config.categories.length > 2;
        const minWidth = hasMultipleCategories ? '800px' : '600px';
        
        dropdown.className = `mega-menu-dropdown hidden absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-2xl shadow-2xl z-50 transform opacity-0 scale-95 transition-all duration-200`;
        dropdown.style.minWidth = minWidth;
        
        const gridCols = Math.min(config.categories.length + 1, 4); // +1 for featured section
        
        dropdown.innerHTML = `
            <div class="p-6 lg:p-8">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-${gridCols} gap-6 lg:gap-8">
                    ${config.categories.map(category => `
                        <div class="space-y-4">
                            <h3 class="flex items-center gap-2 font-bold text-gray-800 mb-4 pb-2 border-b border-gray-100">
                                <span class="text-xl">${category.icon}</span>
                                <span class="text-base lg:text-lg">${category.title}</span>
                            </h3>
                            <ul class="space-y-3">
                                ${category.items.map(item => `
                                    <li>
                                        <a href="${item.link}" class="block group hover:bg-green-50 hover:border-green-100 rounded-lg p-2 -m-2 transition-all duration-200">
                                            <div class="font-medium text-gray-700 group-hover:text-green-600 transition-colors text-sm lg:text-base">
                                                ${item.name}
                                            </div>
                                            <div class="text-xs lg:text-sm text-gray-500 mt-1 leading-relaxed">
                                                ${item.desc}
                                            </div>
                                        </a>
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `).join('')}
                    
                    <!-- Featured Section -->
                    <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 lg:p-6 border border-green-200 ${config.categories.length < 3 ? 'md:col-span-1' : ''}">
                        <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2 pb-2 border-b border-green-200">
                            <span class="text-xl">⭐</span>
                            <span class="text-base lg:text-lg">Featured</span>
                        </h3>
                        <ul class="space-y-3">
                            ${config.featured.map(item => `
                                <li>
                                    <a href="${item.link}" class="block group hover:bg-white/50 rounded-lg p-2 -m-2 transition-all duration-200">
                                        <div class="flex items-center justify-between">
                                            <span class="font-medium text-gray-700 group-hover:text-green-600 transition-colors text-sm lg:text-base">
                                                ${item.name}
                                            </span>
                                            <span class="text-xs px-2 py-1 bg-green-200 text-green-800 rounded-full font-medium whitespace-nowrap ml-2">
                                                ${item.badge}
                                            </span>
                                        </div>
                                    </a>
                                </li>
                            `).join('')}
                        </ul>
                        
                        <!-- Call to Action -->
                        <div class="mt-6 pt-4 border-t border-green-200">
                            <a href="products.html" class="inline-flex items-center justify-center w-full bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm">
                                <span>Browse All Products</span>
                                <svg class="ml-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                                </svg>
                            </a>
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
        
        megaMenu.classList.remove('hidden');
        // Trigger animation
        setTimeout(() => {
            megaMenu.classList.remove('opacity-0', 'scale-95');
            megaMenu.classList.add('opacity-100', 'scale-100');
        }, 10);
        
        currentOpenMenu = megaMenu;
        console.log('🍔 Mega menu shown');
    }
    
    // Hide mega menu
    function hideMegaMenu(megaMenu) {
        menuTimeout = setTimeout(() => {
            megaMenu.classList.add('opacity-0', 'scale-95');
            megaMenu.classList.remove('opacity-100', 'scale-100');
            // Hide after animation
            setTimeout(() => {
                megaMenu.classList.add('hidden');
            }, 200);
            
            if (currentOpenMenu === megaMenu) {
                currentOpenMenu = null;
            }
            console.log('🍔 Mega menu hidden');
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
    console.log('✅ Mega menu system loaded');
    
})();