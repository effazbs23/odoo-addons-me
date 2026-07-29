// Recipe details page functionality

let currentServings = 4;
let originalServings = 4;
let currentRecipe = null;

// Load recipe details from URL parameter
function loadRecipeDetails() {
    const urlParams = new URLSearchParams(window.location.search);
    const recipeId = urlParams.get('id');
    
    if (!recipeId) {
        console.error('No recipe ID provided');
        window.location.href = 'recipes.html';
        return;
    }
    
    currentRecipe = getRecipeById(recipeId);
    
    if (!currentRecipe) {
        console.error('Recipe not found');
        window.location.href = 'recipes.html';
        return;
    }
    
    originalServings = currentRecipe.servings;
    currentServings = originalServings;
    
    populateRecipeDetails();
    populateIngredients();
    populateInstructions();
    populateNutritionInfo();
    loadRelatedRecipes();
}

// Populate recipe header and hero section
function populateRecipeDetails() {
    if (!currentRecipe) return;
    
    // Update page title
    document.title = `${currentRecipe.title} - Natural Foods`;
    
    // Update breadcrumb
    document.getElementById('recipe-breadcrumb').textContent = currentRecipe.title;
    
    // Update hero section
    const heroSection = document.getElementById('recipe-hero');
    heroSection.style.backgroundImage = `url('${currentRecipe.image}')`;
    
    document.getElementById('recipe-category').textContent = currentRecipe.category.charAt(0).toUpperCase() + currentRecipe.category.slice(1);
    document.getElementById('recipe-difficulty').textContent = currentRecipe.difficulty;
    document.getElementById('recipe-title').textContent = currentRecipe.title;
    document.getElementById('recipe-description').textContent = currentRecipe.description;
    
    // Update rating
    const ratingContainer = document.getElementById('recipe-rating');
    ratingContainer.innerHTML = Array(5).fill().map((_, i) => 
        `<span class="${i < Math.floor(currentRecipe.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
    ).join('');
    document.getElementById('recipe-rating-text').textContent = `${currentRecipe.rating} (${Math.floor(Math.random() * 50) + 10} reviews)`;
    
    // Update quick info
    document.getElementById('recipe-total-time').textContent = `${currentRecipe.totalTime} min`;
    document.getElementById('recipe-servings').textContent = currentRecipe.servings;
    document.getElementById('recipe-calories').textContent = currentRecipe.nutrition.calories;
    document.getElementById('recipe-difficulty-text').textContent = currentRecipe.difficulty;
    
    // Update serving count display
    document.getElementById('serving-count').textContent = currentServings;
}

// Populate ingredients list
function populateIngredients() {
    if (!currentRecipe) return;
    
    const container = document.getElementById('ingredients-list');
    
    container.innerHTML = currentRecipe.ingredients.map((ingredient, index) => {
        const adjustedAmount = adjustIngredientAmount(ingredient.amount, currentServings, originalServings);
        
        return `
            <div class="ingredient-item flex items-center p-3 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors" data-index="${index}">
                <input type="checkbox" id="ingredient-${index}" class="w-5 h-5 text-green-600 rounded mr-3" onchange="toggleIngredient(${index})">
                <label for="ingredient-${index}" class="flex-1 cursor-pointer">
                    <span class="font-medium text-gray-800">${adjustedAmount}</span>
                    <span class="text-gray-600 ml-2">${ingredient.name}</span>
                </label>
                ${ingredient.productId ? `<button onclick="addIngredientToCart(${ingredient.productId})" class="ml-2 bg-green-100 hover:bg-green-200 text-green-700 px-3 py-1 rounded-lg text-sm transition-colors" title="Add to cart">
                    <i data-lucide="plus" class="h-4 w-4"></i>
                </button>` : ''}
            </div>
        `;
    }).join('');
    
    // Re-initialize Lucide icons
    lucide.createIcons();
}

// Populate cooking instructions
function populateInstructions() {
    if (!currentRecipe) return;
    
    const container = document.getElementById('instructions-list');
    
    container.innerHTML = currentRecipe.instructions.map((instruction, index) => `
        <div class="instruction-step flex gap-4 p-4 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors" data-step="${index + 1}">
            <div class="flex-shrink-0">
                <div class="w-8 h-8 bg-orange-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                    ${index + 1}
                </div>
            </div>
            <div class="flex-1">
                <p class="text-gray-800 leading-relaxed">${instruction}</p>
                <div class="mt-3">
                    <button onclick="toggleStepComplete(${index})" class="text-sm text-gray-500 hover:text-green-600 transition-colors">
                        <i data-lucide="check-circle" class="h-4 w-4 inline mr-1"></i>
                        Mark as complete
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    // Re-initialize Lucide icons
    lucide.createIcons();
}

// Populate nutrition information
function populateNutritionInfo() {
    if (!currentRecipe) return;
    
    const container = document.getElementById('nutrition-info');
    const nutrition = currentRecipe.nutrition;
    
    // Calculate adjusted nutrition values based on servings
    const multiplier = currentServings / originalServings;
    
    const nutritionItems = [
        { label: 'Calories', value: Math.round(parseInt(nutrition.calories) * multiplier), unit: '' },
        { label: 'Protein', value: Math.round(parseInt(nutrition.protein) * multiplier), unit: 'g' },
        { label: 'Carbs', value: Math.round(parseInt(nutrition.carbs) * multiplier), unit: 'g' },
        { label: 'Fat', value: Math.round(parseInt(nutrition.fat) * multiplier), unit: 'g' }
    ];
    
    container.innerHTML = nutritionItems.map(item => `
        <div class="text-center p-4 bg-gray-50 rounded-xl">
            <div class="text-2xl font-bold text-gray-800 mb-1">${item.value}${item.unit}</div>
            <div class="text-sm text-gray-600">${item.label}</div>
        </div>
    `).join('');
}

// Load related recipes
function loadRelatedRecipes() {
    if (!currentRecipe) return;
    
    const relatedRecipes = getRelatedRecipes(currentRecipe.id, currentRecipe.category, 2);
    const container = document.getElementById('related-recipes');
    
    if (relatedRecipes.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center col-span-2">No related recipes found.</p>';
        return;
    }
    
    container.innerHTML = relatedRecipes.map(recipe => `
        <div class="bg-gray-50 rounded-xl p-4 hover:bg-gray-100 transition-colors cursor-pointer border" onclick="navigateToRecipe(${recipe.id})">
            <img src="${recipe.image}" alt="${recipe.title}" class="w-full h-32 object-cover rounded-lg mb-3">
            <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">${recipe.title}</h3>
            <div class="flex items-center justify-between text-sm text-gray-500">
                <span class="flex items-center gap-1">
                    <i data-lucide="clock" class="h-3 w-3"></i>
                    ${recipe.totalTime}m
                </span>
                <div class="flex items-center gap-1">
                    <div class="flex text-yellow-400 text-xs">
                        ${Array(5).fill().map((_, i) => 
                            `<span class="${i < Math.floor(recipe.rating) ? 'text-yellow-400' : 'text-gray-300'}">★</span>`
                        ).join('')}
                    </div>
                    <span class="ml-1">${recipe.rating}</span>
                </div>
            </div>
        </div>
    `).join('');
    
    // Re-initialize Lucide icons
    lucide.createIcons();
}

// Adjust ingredient amounts based on servings
function adjustIngredientAmount(originalAmount, newServings, originalServings) {
    const multiplier = newServings / originalServings;
    
    // Extract number and unit from amount string
    const match = originalAmount.match(/^(\d+(?:\.\d+)?(?:\/\d+)?)\s*(.*)$/);
    
    if (!match) {
        return originalAmount; // Return original if we can't parse it
    }
    
    let [, numberPart, unitPart] = match;
    
    // Handle fractions
    if (numberPart.includes('/')) {
        const [numerator, denominator] = numberPart.split('/').map(Number);
        numberPart = numerator / denominator;
    } else {
        numberPart = parseFloat(numberPart);
    }
    
    const adjustedNumber = numberPart * multiplier;
    
    // Format the adjusted number nicely
    let formattedNumber;
    if (adjustedNumber < 1 && adjustedNumber > 0) {
        // Convert to fraction for small amounts
        const fraction = decimalToFraction(adjustedNumber);
        formattedNumber = fraction;
    } else if (adjustedNumber % 1 === 0) {
        formattedNumber = adjustedNumber.toString();
    } else {
        formattedNumber = adjustedNumber.toFixed(1);
    }
    
    return `${formattedNumber} ${unitPart}`.trim();
}

// Convert decimal to fraction (simplified)
function decimalToFraction(decimal) {
    const tolerance = 1.0E-6;
    let h1 = 1, h2 = 0, k1 = 0, k2 = 1;
    let b = decimal;
    
    do {
        let a = Math.floor(b);
        let aux = h1; h1 = a * h1 + h2; h2 = aux;
        aux = k1; k1 = a * k1 + k2; k2 = aux;
        b = 1 / (b - a);
    } while (Math.abs(decimal - h1 / k1) > decimal * tolerance);
    
    return k1 === 1 ? h1.toString() : `${h1}/${k1}`;
}

// Adjust servings
function adjustServings(change) {
    const newServings = currentServings + change;
    if (newServings < 1 || newServings > 20) return;
    
    currentServings = newServings;
    document.getElementById('serving-count').textContent = currentServings;
    
    populateIngredients();
    populateNutritionInfo();
}

// Toggle ingredient checked state
function toggleIngredient(index) {
    const ingredientItem = document.querySelector(`[data-index="${index}"]`);
    const checkbox = document.getElementById(`ingredient-${index}`);
    
    if (checkbox.checked) {
        ingredientItem.classList.add('ingredient-checked');
    } else {
        ingredientItem.classList.remove('ingredient-checked');
    }
}

// Toggle instruction step completion
function toggleStepComplete(stepIndex) {
    const stepElement = document.querySelector(`[data-step="${stepIndex + 1}"]`);
    const button = stepElement.querySelector('button');
    
    if (stepElement.classList.contains('step-completed')) {
        stepElement.classList.remove('step-completed');
        button.innerHTML = '<i data-lucide="check-circle" class="h-4 w-4 inline mr-1"></i>Mark as complete';
    } else {
        stepElement.classList.add('step-completed');
        button.innerHTML = '<i data-lucide="check-circle-2" class="h-4 w-4 inline mr-1"></i>Completed!';
    }
    
    // Re-initialize Lucide icons
    lucide.createIcons();
}

// Add ingredient to cart
function addIngredientToCart(productId) {
    if (typeof addToCart === 'function') {
        addToCart(productId);
        showNotification('Ingredient added to cart!', 'success');
    }
}

// Add all available ingredients to cart
function addAllIngredientsToCart() {
    let addedCount = 0;
    
    currentRecipe.ingredients.forEach(ingredient => {
        if (ingredient.productId) {
            if (typeof addToCart === 'function') {
                addToCart(ingredient.productId);
                addedCount++;
            }
        }
    });
    
    if (addedCount > 0) {
        showNotification(`Added ${addedCount} ingredients to cart!`, 'success');
    } else {
        showNotification('No ingredients available for purchase', 'info');
    }
}

// Navigate to another recipe
function navigateToRecipe(recipeId) {
    window.location.href = `recipe-details.html?id=${recipeId}`;
}

// Get related recipes
function getRelatedRecipes(currentId, category, limit = 2) {
    if (typeof getAllRecipes === 'function') {
        const allRecipes = getAllRecipes();
        return allRecipes.filter(recipe => 
            recipe.id !== currentId && 
            recipe.category.toLowerCase() === category.toLowerCase()
        ).slice(0, limit);
    }
    return [];
}

// Show notification function (if not available from other scripts)
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white font-medium z-50 transform translate-x-full transition-transform duration-300 ${
        type === 'success' ? 'bg-green-500' : 
        type === 'error' ? 'bg-red-500' : 
        'bg-blue-500'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}