// Enhanced Product Details Data - Detailed product information and constants

const enhancedProductDetails = [
    {
        id: 1,
        name: "Organic Baby Spinach",
        price: 4.99,
        originalPrice: 6.99,
        image: "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&h=600&fit=crop",
        gallery: [
            "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1584464491033-06628f3a6b7b?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=600&h=600&fit=crop&flip=h"
        ],
        category: "vegetables",
        brand: "Fresh Farm",
        description: "Fresh organic baby spinach leaves, perfect for salads and smoothies. Packed with iron, vitamins, and minerals for optimal health and wellness.",
        longDescription: "Our premium organic baby spinach is carefully harvested at peak freshness from certified organic farms. These tender, nutrient-dense leaves are perfect for salads, smoothies, and cooking. Rich in iron, folate, and vitamins A, C, and K, this superfood supports healthy bones, immune function, and overall wellness. The leaves are pre-washed and ready to eat, making healthy eating convenient and delicious.",
        rating: 4.8,
        reviews: 127,
        sale: true,
        isNew: false,
        salePercentage: 29,
        inStock: true,
        weight: "5oz",
        sku: "NF-VS-001",
        specifications: [
            "Certified Organic (USDA)",
            "Pre-washed and ready to eat",
            "Rich in iron and vitamins",
            "Pesticide-free",
            "Sustainably grown",
            "Fresh harvest guarantee"
        ],
        nutritionFacts: {
            servingSize: "85g (3 cups)",
            calories: 20,
            protein: "2g",
            carbs: "3g",
            fat: "0.3g",
            fiber: "2.2g",
            vitaminK: "145mcg",
            vitaminA: "469mcg",
            folate: "58mcg",
            iron: "0.8mg"
        },
        attributes: {
            weight: [
                { label: "5oz", value: "5oz", price: 4.99, available: true },
                { label: "10oz", value: "10oz", price: 8.99, available: true },
                { label: "1lb", value: "1lb", price: 12.99, available: false }
            ]
        }
    },
    {
        id: 2,
        name: "Free Range Eggs",
        price: 4.99,
        originalPrice: 6.99,
        image: "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=600&h=600&fit=crop",
        gallery: [
            "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=600&h=600&fit=crop",
            "https://images.unsplash.com/photo-1569288052389-8c9b8ad8b04b?w=600&h=600&fit=crop"
        ],
        category: "dairy",
        brand: "Happy Hens",
        description: "Fresh free-range eggs from pasture-raised hens. Rich in omega-3 and protein. Ethically sourced from local farms.",
        longDescription: "Our free-range eggs come from hens that roam freely on pasture, resulting in richer, more nutritious eggs with bright orange yolks. These hens are fed a natural diet and live in humane conditions. The eggs are higher in omega-3 fatty acids, vitamin E, and beta-carotene compared to conventional eggs.",
        rating: 4.7,
        reviews: 89,
        sale: true,
        isNew: false,
        salePercentage: 29,
        inStock: true,
        weight: "12 count",
        sku: "NF-DA-002",
        specifications: [
            "Free-range and pasture-raised",
            "High in omega-3 fatty acids",
            "Ethically sourced",
            "Fresh from local farms",
            "Rich in protein and vitamins",
            "Bright orange yolks"
        ],
        nutritionFacts: {
            servingSize: "1 large egg (50g)",
            calories: 70,
            protein: "6g",
            carbs: "0.5g",
            fat: "5g",
            cholesterol: "186mg",
            vitaminD: "1mcg",
            vitaminB12: "0.5mcg",
            choline: "147mg"
        },
        attributes: {
            size: [
                { label: "6 count", value: "6", price: 3.99, available: true },
                { label: "12 count", value: "12", price: 4.99, available: true },
                { label: "18 count", value: "18", price: 7.99, available: true }
            ],
            color: [
                { label: "Brown", value: "brown", available: true },
                { label: "White", value: "white", available: true }
            ]
        }
    },
    {
        id: 6,
        name: "Organic Honey Crisp Apples",
        price: 5.99,
        image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&h=600&fit=crop",
        gallery: [
            "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=600&h=600&fit=crop"
        ],
        category: "fruits",
        brand: "Orchard Fresh",
        description: "Sweet and crispy organic honey crisp apples. Perfect for snacking or baking. Grown without pesticides in sustainable orchards.",
        longDescription: "Our organic Honey Crisp apples are grown in sustainable orchards without harmful pesticides or chemicals. These apples are known for their perfect balance of sweetness and tartness, with a satisfying crispy texture that makes them ideal for fresh eating, baking, or adding to salads.",
        rating: 4.9,
        reviews: 156,
        sale: false,
        isNew: true,
        inStock: true,
        weight: "2lb",
        sku: "NF-FR-006",
        specifications: [
            "Certified Organic",
            "Sweet and crispy texture",
            "Perfect for snacking",
            "Great for baking",
            "Grown without pesticides",
            "Hand-picked at peak ripeness"
        ],
        nutritionFacts: {
            servingSize: "1 medium apple (182g)",
            calories: 95,
            protein: "0.5g",
            carbs: "25g",
            fat: "0.3g",
            fiber: "4g",
            vitaminC: "8.4mg",
            potassium: "195mg"
        },
        attributes: {
            weight: [
                { label: "1lb", value: "1lb", price: 3.99, available: true },
                { label: "2lb", value: "2lb", price: 5.99, available: true },
                { label: "5lb", value: "5lb", price: 12.99, available: true }
            ]
        }
    }
];

// Tab content templates
const detailsTabTemplates = {
    description: (product) => `
        <div class="space-y-8 animate-fade-in">
            <div>
                <h3 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <span class="text-3xl">📝</span>
                    Product Description
                </h3>
                <p class="text-gray-700 leading-relaxed text-lg mb-6">${product.longDescription || product.description}</p>
                <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6">
                    <div class="flex items-center gap-3 mb-3">
                        <i data-lucide="package" class="h-5 w-5 text-green-600"></i>
                        <span class="font-semibold text-gray-800">Product Details</span>
                    </div>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>SKU: <span class="font-semibold">${product.sku}</span></div>
                        <div>Weight: <span class="font-semibold">${product.weight}</span></div>
                        <div>Brand: <span class="font-semibold">${product.brand}</span></div>
                        <div>Category: <span class="font-semibold capitalize">${product.category}</span></div>
                    </div>
                </div>
            </div>
            
            ${product.specifications && product.specifications.length > 0 ? `
                <div>
                    <h4 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-3">
                        <span class="text-2xl">✨</span>
                        Key Features
                    </h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        ${product.specifications.map(spec => `
                            <div class="flex items-start gap-3 p-4 bg-gray-50 rounded-xl">
                                <span class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                                <span class="text-gray-700 font-medium">${spec}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `,
    
    nutrition: (product) => `
        <div class="space-y-8 animate-fade-in">
            <div>
                <h3 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <span class="text-3xl">🥗</span>
                    Nutrition Information
                </h3>
                <p class="text-gray-600 mb-8 text-lg">
                    Nutritional values per ${product.nutritionFacts?.servingSize || 'serving'}
                </p>
            </div>
            
            <div class="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-2xl p-8">
                <h4 class="text-xl font-bold text-gray-800 mb-6">Nutrition Facts</h4>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-6">
                    ${product.nutritionFacts ? Object.entries(product.nutritionFacts).filter(([key]) => key !== 'servingSize').map(([key, value]) => `
                        <div class="bg-white rounded-xl p-4 text-center shadow-sm border border-green-100">
                            <div class="text-2xl font-bold text-green-600">${value}</div>
                            <div class="text-sm text-gray-600 capitalize">${key.replace(/([A-Z])/g, ' $1').trim()}</div>
                        </div>
                    `).join('') : `
                        <div class="col-span-full text-center text-gray-600">
                            Detailed nutrition information will be available soon.
                        </div>
                    `}
                </div>
            </div>
        </div>
    `,
    
    reviews: (product) => `
        <div class="space-y-8 animate-fade-in">
            <div>
                <h3 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <span class="text-3xl">⭐</span>
                    Customer Reviews
                </h3>
                
                <div class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6 mb-8">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center gap-6">
                            <div class="text-4xl font-bold text-green-600">${product.rating}</div>
                            <div>
                                <div class="flex text-yellow-400 text-xl mb-2">
                                    ${Array(5).fill().map((_, i) => 
                                        `<span class="${i < Math.floor(product.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                                    ).join('')}
                                </div>
                                <p class="text-gray-600">Based on ${product.reviews} reviews</p>
                            </div>
                        </div>
                        <button class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-semibold transition-colors">
                            Write a Review
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="space-y-6">
                ${[1, 2, 3].map(review => `
                    <div class="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center gap-4">
                                <div class="w-12 h-12 bg-gradient-to-br from-green-400 to-emerald-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                                    ${String.fromCharCode(64 + review)}
                                </div>
                                <div>
                                    <div class="flex text-yellow-400 mb-1">
                                        ${Array(5).fill().map(() => '<span class="text-yellow-400">★</span>').join('')}
                                    </div>
                                    <span class="font-semibold text-gray-800">Anonymous Customer</span>
                                </div>
                            </div>
                            <span class="text-sm text-gray-500">3 days ago</span>
                        </div>
                        <p class="text-gray-700 leading-relaxed">
                            Excellent quality product! Fresh, organic, and delivered quickly. The ${product.name.toLowerCase()} exceeded my expectations. Will definitely order again!
                        </p>
                    </div>
                `).join('')}
            </div>
        </div>
    `,
    
    shipping: () => `
        <div class="space-y-8 animate-fade-in">
            <div>
                <h3 class="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-3">
                    <span class="text-3xl">🚚</span>
                    Shipping & Delivery
                </h3>
            </div>
            
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div class="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-2xl p-6">
                    <h4 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-3">
                        <span class="text-2xl">📦</span>
                        Delivery Options
                    </h4>
                    <div class="space-y-3">
                        <div class="flex justify-between items-center p-3 bg-white rounded-xl border border-blue-100">
                            <span class="font-medium">Standard Delivery (2-3 days)</span>
                            <span class="font-bold text-green-600">$5.99</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-white rounded-xl border border-blue-100">
                            <span class="font-medium">Express Delivery (1-2 days)</span>
                            <span class="font-bold text-green-600">$9.99</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-white rounded-xl border border-blue-100">
                            <span class="font-medium">Same Day Delivery</span>
                            <span class="font-bold text-green-600">$14.99</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gradient-to-r from-green-100 to-emerald-100 rounded-xl border border-green-200">
                            <span class="font-bold text-green-800">Free shipping on orders over $50</span>
                            <span class="font-bold text-green-600">FREE</span>
                        </div>
                    </div>
                </div>
                
                <div class="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6">
                    <h4 class="text-xl font-bold text-gray-800 mb-4 flex items-center gap-3">
                        <span class="text-2xl">🥬</span>
                        Storage & Handling
                    </h4>
                    <div class="space-y-3">
                        <div class="flex items-start gap-3 p-3 bg-white rounded-xl">
                            <span class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                            <span class="text-gray-700 font-medium">Store in a cool, dry place</span>
                        </div>
                        <div class="flex items-start gap-3 p-3 bg-white rounded-xl">
                            <span class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                            <span class="text-gray-700 font-medium">Refrigerate after opening</span>
                        </div>
                        <div class="flex items-start gap-3 p-3 bg-white rounded-xl">
                            <span class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                            <span class="text-gray-700 font-medium">Use within 3-5 days of delivery</span>
                        </div>
                        <div class="flex items-start gap-3 p-3 bg-white rounded-xl">
                            <span class="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></span>
                            <span class="text-gray-700 font-medium">Keep away from direct sunlight</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Make data globally available
if (typeof window !== 'undefined') {
    window.enhancedProductDetails = enhancedProductDetails;
    window.detailsTabTemplates = detailsTabTemplates;
}