// Recipe Data for Natural Foods Organic Store
console.log('🍽️ Loading recipe-data.js...');

// Recipe database
const recipeDatabase = [
    {
        id: 1,
        title: "Fresh Garden Salad",
        description: "A vibrant mix of organic greens, tomatoes, and vegetables tossed in a light vinaigrette dressing.",
        image: "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400&h=300&fit=crop",
        cookTime: "15 mins",
        prepTime: 10,
        totalTime: 15,
        difficulty: "Easy",
        servings: 4,
        rating: 4.5,
        featured: true,
        category: "Salads",
        ingredients: [
            { amount: "2 cups", name: "mixed organic greens", productId: 1 },
            { amount: "1 cup", name: "cherry tomatoes, halved", productId: 2 },
            { amount: "1/2", name: "cucumber, sliced", productId: 3 },
            { amount: "1/4", name: "red onion, thinly sliced", productId: 4 },
            { amount: "2 tbsp", name: "olive oil", productId: 5 },
            { amount: "1 tbsp", name: "balsamic vinegar", productId: 6 },
            { amount: "to taste", name: "salt and pepper", productId: null }
        ],
        instructions: [
            "Wash and dry all vegetables thoroughly.",
            "In a large bowl, combine mixed greens, tomatoes, cucumber, and red onion.",
            "In a small bowl, whisk together olive oil, balsamic vinegar, salt, and pepper.",
            "Drizzle dressing over salad and toss gently to combine.",
            "Serve immediately and enjoy!"
        ],
        nutrition: {
            calories: 120,
            protein: "3g",
            carbs: "8g",
            fat: "9g",
            fiber: "4g"
        },
        tags: ["healthy", "vegetarian", "gluten-free", "quick"]
    },
    {
        id: 2,
        title: "Organic Berry Smoothie",
        description: "A nutritious blend of organic berries, yogurt, and honey for the perfect morning energy boost.",
        image: "https://images.unsplash.com/photo-1553530666-ba11a7da3888?w=400&h=300&fit=crop",
        cookTime: "5 mins",
        prepTime: 5,
        totalTime: 5,
        difficulty: "Easy",
        servings: 2,
        rating: 4.7,
        featured: true,
        category: "Smoothies",
        ingredients: [
            { amount: "1 cup", name: "organic mixed berries (frozen or fresh)", productId: 7 },
            { amount: "1/2 cup", name: "organic Greek yogurt", productId: 8 },
            { amount: "1/2 cup", name: "organic almond milk", productId: 9 },
            { amount: "1 tbsp", name: "organic honey", productId: 10 },
            { amount: "1/2", name: "banana", productId: 11 },
            { amount: "1 tsp", name: "chia seeds (optional)", productId: 12 }
        ],
        instructions: [
            "Add all ingredients to a high-speed blender.",
            "Blend on high for 60-90 seconds until smooth and creamy.",
            "If too thick, add more almond milk gradually.",
            "Pour into glasses and serve immediately.",
            "Garnish with extra berries if desired."
        ],
        nutrition: {
            calories: 180,
            protein: "8g",
            carbs: "32g",
            fat: "3g",
            fiber: "6g"
        },
        tags: ["healthy", "breakfast", "protein-rich", "antioxidants"]
    },
    {
        id: 3,
        title: "Roasted Vegetable Medley",
        description: "Colorful organic vegetables roasted to perfection with herbs and olive oil for maximum flavor.",
        image: "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400&h=300&fit=crop",
        cookTime: "45 mins",
        difficulty: "Medium",
        servings: 6,
        category: "Main Course",
        ingredients: [
            "2 bell peppers, cut into strips",
            "1 zucchini, sliced",
            "1 eggplant, cubed",
            "1 red onion, wedged",
            "2 cups cherry tomatoes",
            "3 tbsp olive oil",
            "2 cloves garlic, minced",
            "1 tsp dried herbs (rosemary, thyme)",
            "Salt and pepper to taste"
        ],
        instructions: [
            "Preheat oven to 425°F (220°C).",
            "Cut all vegetables into similar-sized pieces.",
            "In a large bowl, toss vegetables with olive oil, garlic, herbs, salt, and pepper.",
            "Spread vegetables in a single layer on a large baking sheet.",
            "Roast for 25-30 minutes, stirring once halfway through.",
            "Vegetables should be tender and lightly caramelized.",
            "Serve hot as a side dish or over quinoa for a complete meal."
        ],
        nutrition: {
            calories: 95,
            protein: "3g",
            carbs: "12g",
            fat: "5g",
            fiber: "5g"
        },
        tags: ["vegetarian", "vegan", "gluten-free", "fiber-rich"]
    },
    {
        id: 4,
        title: "Quinoa Power Bowl",
        description: "A nutrient-packed bowl with quinoa, roasted vegetables, and tahini dressing.",
        image: "https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400&h=300&fit=crop",
        cookTime: "30 mins",
        difficulty: "Medium",
        servings: 4,
        category: "Main Course",
        ingredients: [
            "1 cup organic quinoa",
            "2 cups vegetable broth",
            "1 sweet potato, cubed",
            "1 cup broccoli florets",
            "1/2 cup chickpeas",
            "2 tbsp tahini",
            "1 lemon, juiced",
            "2 tbsp olive oil",
            "1 avocado, sliced"
        ],
        instructions: [
            "Cook quinoa in vegetable broth according to package instructions.",
            "Roast sweet potato and broccoli at 400°F for 20 minutes.",
            "Mix tahini, lemon juice, and olive oil for dressing.",
            "Assemble bowls with quinoa, roasted vegetables, and chickpeas.",
            "Top with avocado and drizzle with tahini dressing."
        ],
        nutrition: {
            calories: 420,
            protein: "15g",
            carbs: "58g",
            fat: "16g",
            fiber: "12g"
        },
        tags: ["vegan", "protein-rich", "complete-meal", "superfoods"]
    },
    {
        id: 5,
        title: "Green Detox Juice",
        description: "A refreshing green juice packed with nutrients from organic leafy greens and fruits.",
        image: "https://images.unsplash.com/photo-1610970881699-44a5587cabec?w=400&h=300&fit=crop",
        cookTime: "10 mins",
        difficulty: "Easy",
        servings: 2,
        category: "Beverages",
        ingredients: [
            "2 cups organic spinach",
            "1 cucumber",
            "2 green apples",
            "1 lemon, juiced",
            "1 inch fresh ginger",
            "1 cup coconut water"
        ],
        instructions: [
            "Wash all fruits and vegetables thoroughly.",
            "Core apples and cut into chunks.",
            "Add all ingredients to a high-speed juicer or blender.",
            "If using a blender, strain the mixture through a fine mesh.",
            "Serve immediately over ice for best taste."
        ],
        nutrition: {
            calories: 85,
            protein: "2g",
            carbs: "22g",
            fat: "0g",
            fiber: "4g"
        },
        tags: ["detox", "vegan", "raw", "vitamin-c"]
    },
    {
        id: 6,
        title: "Overnight Oats with Berries",
        description: "Make-ahead breakfast with organic oats, fresh berries, and creamy yogurt.",
        image: "https://images.unsplash.com/photo-1571197119282-36c3b998085b?w=400&h=300&fit=crop",
        cookTime: "5 mins (+ overnight)",
        difficulty: "Easy",
        servings: 2,
        category: "Breakfast",
        ingredients: [
            "1 cup rolled oats",
            "1 cup organic almond milk",
            "2 tbsp chia seeds",
            "2 tbsp maple syrup",
            "1/2 cup Greek yogurt",
            "1 cup mixed berries",
            "1/4 cup chopped nuts"
        ],
        instructions: [
            "Mix oats, almond milk, chia seeds, and maple syrup in a bowl.",
            "Divide mixture between two jars or containers.",
            "Refrigerate overnight or at least 4 hours.",
            "In the morning, top with yogurt, berries, and nuts.",
            "Enjoy cold or warm in the microwave for 30 seconds."
        ],
        nutrition: {
            calories: 320,
            protein: "12g",
            carbs: "45g",
            fat: "11g",
            fiber: "10g"
        },
        tags: ["make-ahead", "high-fiber", "breakfast", "protein"]
    }
];

// Get all recipes
function getAllRecipes() {
    return recipeDatabase;
}

// Get recipe by ID
function getRecipeById(id) {
    return recipeDatabase.find(recipe => recipe.id === parseInt(id));
}

// Get recipes by category
function getRecipesByCategory(category) {
    return recipeDatabase.filter(recipe => 
        recipe.category.toLowerCase() === category.toLowerCase()
    );
}

// Get featured recipes (highest rated or most popular)
function getFeaturedRecipes(limit = 3) {
    return recipeDatabase.slice(0, limit);
}

// Search recipes
function searchRecipes(query) {
    const searchTerm = query.toLowerCase();
    return recipeDatabase.filter(recipe =>
        recipe.title.toLowerCase().includes(searchTerm) ||
        recipe.description.toLowerCase().includes(searchTerm) ||
        recipe.category.toLowerCase().includes(searchTerm) ||
        recipe.tags.some(tag => tag.toLowerCase().includes(searchTerm))
    );
}

// Get recipes by difficulty
function getRecipesByDifficulty(difficulty) {
    return recipeDatabase.filter(recipe => 
        recipe.difficulty.toLowerCase() === difficulty.toLowerCase()
    );
}

// Get quick recipes (under 30 minutes)
function getQuickRecipes() {
    return recipeDatabase.filter(recipe => {
        const time = parseInt(recipe.cookTime);
        return time <= 30;
    });
}

// Get recipe categories
function getRecipeCategories() {
    const categories = [...new Set(recipeDatabase.map(recipe => recipe.category))];
    return categories.sort();
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.getAllRecipes = getAllRecipes;
    window.getRecipeById = getRecipeById;
    window.getRecipesByCategory = getRecipesByCategory;
    window.getFeaturedRecipes = getFeaturedRecipes;
    window.searchRecipes = searchRecipes;
    window.getRecipesByDifficulty = getRecipesByDifficulty;
    window.getQuickRecipes = getQuickRecipes;
    window.getRecipeCategories = getRecipeCategories;
}

console.log(`✅ Recipe data loaded: ${recipeDatabase.length} recipes available`);