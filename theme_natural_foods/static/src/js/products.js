// Product data and functionality

// Sample product data (this would typically come from an API)
function getAllProducts() {
    return [
        // VEGETABLES
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
            isNew: false,
            sale: true,
            specifications: ["Organic", "Fresh", "Locally Grown", "High in Iron"],
            colors: ["Green"],
            sizes: ["5oz", "10oz", "1lb"]
        },
        {
            id: 2,
            name: "Organic Carrots",
            price: 2.99,
            image: "https://images.unsplash.com/photo-1445282768818-728615cc910a?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Root & Vine",
            description: "Fresh organic carrots, perfect for cooking or snacking. Sweet and crunchy with natural orange color.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Fresh", "Vitamin A Rich", "No Pesticides"],
            colors: ["Orange"],
            sizes: ["1lb", "2lb", "5lb"]
        },
        {
            id: 3,
            name: "Organic Broccoli Crowns",
            price: 3.49,
            originalPrice: 4.49,
            image: "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Green Valley",
            description: "Premium organic broccoli crowns. Fresh, crispy, and packed with nutrients. Great for steaming or stir-frying.",
            rating: 4.6,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Fresh", "High Fiber", "Vitamin C Rich"],
            colors: ["Green"],
            sizes: ["1 Head", "2 Heads"]
        },
        {
            id: 4,
            name: "Organic Bell Peppers Mix",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1525607551340-4864c4162d29?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Rainbow Harvest",
            description: "Colorful mix of organic bell peppers - red, yellow, and green. Sweet, crispy, and perfect for any dish.",
            rating: 4.7,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Mixed Colors", "Sweet Variety", "Non-GMO"],
            colors: ["Red", "Yellow", "Green"],
            sizes: ["3-pack", "6-pack"]
        },
        {
            id: 5,
            name: "Organic Kale",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1557844352-761f2565b576?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Leafy Greens Co",
            description: "Fresh organic kale leaves. Superfood packed with vitamins K, A, and C. Perfect for salads and smoothies.",
            rating: 4.4,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Superfood", "High in Antioxidants", "Fresh"],
            colors: ["Dark Green"],
            sizes: ["1 Bunch", "2 Bunches"]
        },
        {
            id: 37,
            name: "Organic Cherry Tomatoes",
            price: 4.49,
            image: "https://images.unsplash.com/photo-1592841200221-21e72d082a43?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Garden Fresh",
            description: "Sweet organic cherry tomatoes. Perfect for salads, snacking, or cooking. Bursting with flavor.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Sweet", "Vine Ripened", "Antioxidant Rich"],
            colors: ["Red"],
            sizes: ["1 pint", "2 pints"]
        },
        {
            id: 38,
            name: "Organic Cucumber",
            price: 2.49,
            originalPrice: 3.49,
            image: "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Fresh Garden",
            description: "Crisp organic cucumbers. Great for salads, pickles, or refreshing snacks. Hydrating and nutritious.",
            rating: 4.3,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Crisp", "Hydrating", "Low Calorie"],
            colors: ["Green"],
            sizes: ["Each", "3-pack"]
        },
        {
            id: 39,
            name: "Organic Sweet Potatoes",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Root Harvest",
            description: "Organic sweet potatoes rich in vitamins and minerals. Perfect for roasting, baking, or making fries.",
            rating: 4.6,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Vitamin A Rich", "High Fiber", "Naturally Sweet"],
            colors: ["Orange"],
            sizes: ["2lb", "5lb"]
        },
        {
            id: 61,
            name: "Organic Brussels Sprouts",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Green Valley",
            description: "Fresh organic Brussels sprouts. High in vitamins C and K. Perfect for roasting or sautéing.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "High Vitamin C", "High Vitamin K", "Fresh"],
            colors: ["Green"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 62,
            name: "Organic Red Onions",
            price: 2.99,
            image: "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Farm Fresh",
            description: "Organic red onions with mild, sweet flavor. Perfect for salads, grilling, or caramelizing.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Sweet Flavor", "Versatile", "Fresh"],
            colors: ["Red"],
            sizes: ["2lb", "3lb"]
        },
        {
            id: 63,
            name: "Organic Zucchini",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1459411621453-7b03977f4bfc?w=300&h=300&fit=crop",
            category: "vegetables",
            brand: "Garden Select",
            description: "Fresh organic zucchini. Tender and versatile vegetable perfect for grilling, baking, or spiralizing.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Tender", "Versatile", "Low Calorie"],
            colors: ["Green"],
            sizes: ["2-pack", "4-pack"]
        },

        // FRUITS
        {
            id: 6,
            name: "Organic Honey Crisp Apples",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Orchard Fresh",
            description: "Sweet and crispy organic honey crisp apples. Perfect for snacking or baking. Grown without pesticides.",
            rating: 4.9,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Sweet", "Crispy", "No Pesticides"],
            colors: ["Red", "Yellow"],
            sizes: ["1lb", "2lb", "5lb"]
        },
        {
            id: 7,
            name: "Organic Blueberries",
            price: 6.99,
            originalPrice: 8.99,
            image: "https://images.unsplash.com/photo-1498557850523-fd3d118b962e?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Berry Best",
            description: "Sweet organic blueberries packed with antioxidants. Fresh picked and perfect for breakfast or snacking.",
            rating: 4.8,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Antioxidant Rich", "Fresh", "Sweet"],
            colors: ["Blue"],
            sizes: ["6oz", "12oz", "1lb"]
        },
        {
            id: 8,
            name: "Organic Bananas",
            price: 2.49,
            image: "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Tropical Fresh",
            description: "Organic bananas, perfectly ripe and sweet. Great source of potassium and natural energy.",
            rating: 4.6,
            isNew: false,
            sale: false,
            specifications: ["Organic", "High Potassium", "Natural Energy", "Fair Trade"],
            colors: ["Yellow"],
            sizes: ["1 Bunch", "2 Bunches"]
        },
        {
            id: 9,
            name: "Organic Strawberries",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Berry Fresh",
            description: "Sweet, juicy organic strawberries. Perfect for desserts, smoothies, or eating fresh. Locally grown.",
            rating: 4.7,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Sweet", "Locally Grown", "Vitamin C Rich"],
            colors: ["Red"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 10,
            name: "Organic Avocados",
            price: 7.99,
            image: "https://images.unsplash.com/photo-1549324797-371fa825d0da?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Green Gold",
            description: "Perfectly ripe organic avocados. Creamy texture and rich flavor. Great source of healthy fats.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Healthy Fats", "Creamy", "Ready to Eat"],
            colors: ["Green"],
            sizes: ["2-pack", "4-pack", "6-pack"]
        },
        {
            id: 40,
            name: "Organic Lemons",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1590502593747-42a996133562?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Citrus Grove",
            description: "Fresh organic lemons. Perfect for cooking, baking, or making fresh lemonade. High in vitamin C.",
            rating: 4.4,
            isNew: false,
            sale: false,
            specifications: ["Organic", "High Vitamin C", "Fresh", "Zesty"],
            colors: ["Yellow"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 41,
            name: "Organic Pineapple",
            price: 6.99,
            originalPrice: 8.99,
            image: "https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Tropical Paradise",
            description: "Sweet organic pineapple. Tropical flavor and natural enzymes. Great for snacking or smoothies.",
            rating: 4.6,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Tropical", "Natural Enzymes", "Sweet"],
            colors: ["Yellow"],
            sizes: ["Whole", "Pre-cut"]
        },
        {
            id: 42,
            name: "Organic Oranges",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1547514701-42782101795e?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Sunshine Citrus",
            description: "Juicy organic oranges. Perfect for fresh juice or snacking. Packed with vitamin C and fiber.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Juicy", "Vitamin C Rich", "High Fiber"],
            colors: ["Orange"],
            sizes: ["3lb", "5lb"]
        },
        {
            id: 64,
            name: "Organic Grapes",
            price: 5.99,
            originalPrice: 7.49,
            image: "https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Vineyard Select",
            description: "Sweet organic grapes. Perfect for snacking or adding to fruit salads. Seedless variety.",
            rating: 4.7,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Seedless", "Sweet", "Fresh"],
            colors: ["Green", "Red"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 65,
            name: "Organic Peaches",
            price: 5.49,
            image: "https://images.unsplash.com/photo-1629826036135-d5bfec2b3b5b?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Stone Fruit Co",
            description: "Juicy organic peaches. Sweet and fragrant stone fruit perfect for desserts or fresh eating.",
            rating: 4.8,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Juicy", "Sweet", "Stone Fruit"],
            colors: ["Orange"],
            sizes: ["2lb", "3lb"]
        },
        {
            id: 66,
            name: "Organic Raspberries",
            price: 7.99,
            image: "https://images.unsplash.com/photo-1577003833619-76bfe0022b37?w=300&h=300&fit=crop",
            category: "fruits",
            brand: "Berry Bliss",
            description: "Fresh organic raspberries. Delicate and sweet with antioxidant properties. Perfect for desserts.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Antioxidants", "Delicate", "Sweet"],
            colors: ["Red"],
            sizes: ["6oz", "12oz"]
        },

        // DAIRY
        {
            id: 11,
            name: "Organic Whole Milk",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Pure Dairy",
            description: "Fresh organic whole milk from grass-fed cows. Rich, creamy, and naturally delicious.",
            rating: 4.7,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Grass-Fed", "No Hormones", "Fresh"],
            colors: ["White"],
            sizes: ["1/2 Gallon", "1 Gallon"]
        },
        {
            id: 12,
            name: "Free Range Eggs",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Happy Hens",
            description: "Fresh free-range eggs from pasture-raised hens. Rich in omega-3 and protein. Ethically sourced.",
            rating: 4.7,
            isNew: false,
            sale: true,
            specifications: ["Free Range", "Pasture Raised", "No Hormones", "Omega-3 Rich"],
            colors: ["Brown", "White"],
            sizes: ["6 count", "12 count", "18 count"]
        },
        {
            id: 13,
            name: "Organic Greek Yogurt",
            price: 5.49,
            image: "https://images.unsplash.com/photo-1571212515416-cd73c6b48529?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Pure Greek",
            description: "Creamy organic Greek yogurt with live cultures. High in protein and probiotics. Perfect for breakfast.",
            rating: 4.8,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Probiotic", "High Protein", "Live Cultures"],
            colors: ["White"],
            sizes: ["6oz", "32oz"]
        },
        {
            id: 14,
            name: "Organic Cheddar Cheese",
            price: 6.99,
            originalPrice: 8.99,
            image: "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Artisan Cheese Co",
            description: "Sharp organic cheddar cheese. Aged to perfection with rich, bold flavor. Made from grass-fed milk.",
            rating: 4.6,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Grass-Fed", "Aged", "Sharp Flavor"],
            colors: ["Yellow"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 43,
            name: "Organic Butter",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Farm Fresh Dairy",
            description: "Creamy organic butter from grass-fed cows. Perfect for baking, cooking, or spreading on toast.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Grass-Fed", "Creamy", "Rich Flavor"],
            colors: ["Yellow"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 44,
            name: "Organic Cream Cheese",
            price: 4.49,
            originalPrice: 5.99,
            image: "https://images.unsplash.com/photo-1571068316344-75bc76f77890?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Artisan Dairy",
            description: "Smooth organic cream cheese. Perfect for bagels, baking, or cooking. Made with natural ingredients.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Smooth", "Natural", "Versatile"],
            colors: ["White"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 67,
            name: "Organic Mozzarella",
            price: 6.49,
            image: "https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Italian Fresh",
            description: "Fresh organic mozzarella cheese. Creamy texture and mild flavor. Perfect for pizza and caprese.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Fresh", "Creamy", "Mild Flavor"],
            colors: ["White"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 68,
            name: "Organic Heavy Cream",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1550583724-b2692b85b150?w=300&h=300&fit=crop",
            category: "dairy",
            brand: "Dairy Pure",
            description: "Rich organic heavy cream. Perfect for whipping, coffee, or cooking. From grass-fed cows.",
            rating: 4.6,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Rich", "Grass-Fed", "Versatile"],
            colors: ["White"],
            sizes: ["16oz", "32oz"]
        },

        // BAKERY
        {
            id: 15,
            name: "Artisan Sourdough Bread",
            price: 4.49,
            image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Baker's Choice",
            description: "Handcrafted sourdough bread with organic flour. Traditional recipe with tangy flavor and perfect crust.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic Flour", "Handcrafted", "No Preservatives", "Traditional Recipe"],
            colors: ["Brown"],
            sizes: ["1 Loaf"]
        },
        {
            id: 16,
            name: "Gluten-Free Oat Bread",
            price: 6.99,
            originalPrice: 8.49,
            image: "https://images.unsplash.com/photo-1586444248902-2f64eddc13df?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Healthy Grains",
            description: "Nutritious gluten-free bread made with organic oats. Soft texture and nutty flavor. Perfect for toast.",
            rating: 4.4,
            isNew: true,
            sale: true,
            specifications: ["Gluten Free", "Organic Oats", "High Fiber", "No Artificial Additives"],
            colors: ["Brown"],
            sizes: ["1 Loaf"]
        },
        {
            id: 17,
            name: "Organic Whole Wheat Bagels",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1551024506-0bccd828d307?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Morning Fresh",
            description: "Fresh organic whole wheat bagels. Chewy texture and wholesome flavor. Perfect for breakfast.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Whole Wheat", "Fresh Baked", "No Preservatives"],
            colors: ["Brown"],
            sizes: ["6-pack"]
        },
        {
            id: 18,
            name: "Organic Croissants",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1555507036-ab794f87c728?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "French Bakery",
            description: "Buttery organic croissants made with organic butter and flour. Flaky, light, and delicious.",
            rating: 4.8,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Buttery", "Flaky", "Fresh Baked"],
            colors: ["Golden"],
            sizes: ["4-pack", "8-pack"]
        },
        {
            id: 45,
            name: "Organic Dinner Rolls",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Home Bakery",
            description: "Soft organic dinner rolls. Perfect for meals or sandwiches. Made with organic flour and natural ingredients.",
            rating: 4.6,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Soft", "Fresh Baked", "Natural Ingredients"],
            colors: ["Golden"],
            sizes: ["8-pack", "12-pack"]
        },
        {
            id: 69,
            name: "Organic Baguette",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "French Artisan",
            description: "Traditional organic French baguette. Crispy crust and soft interior. Perfect for sandwiches or soup.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Traditional", "Crispy Crust", "Fresh Daily"],
            colors: ["Golden"],
            sizes: ["1 Loaf"]
        },
        {
            id: 70,
            name: "Organic Muffins Variety Pack",
            price: 7.99,
            originalPrice: 9.99,
            image: "https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=300&h=300&fit=crop",
            category: "bakery",
            brand: "Sweet Treats",
            description: "Assorted organic muffins - blueberry, banana nut, and chocolate chip. Perfect for breakfast or snack.",
            rating: 4.5,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Variety Pack", "Fresh Baked", "No Artificial Flavors"],
            colors: ["Mixed"],
            sizes: ["6-pack", "12-pack"]
        },

        // SEAFOOD
        {
            id: 19,
            name: "Wild Caught Salmon",
            price: 12.99,
            originalPrice: 15.99,
            image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Ocean Fresh",
            description: "Premium wild-caught Atlantic salmon fillets. Rich in omega-3 fatty acids. Sustainably sourced.",
            rating: 4.9,
            isNew: false,
            sale: true,
            specifications: ["Wild Caught", "Sustainable", "High Omega-3", "Fresh"],
            colors: ["Pink"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 20,
            name: "Organic Shrimp",
            price: 14.99,
            image: "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Coastal Catch",
            description: "Large organic shrimp, peeled and deveined. Sweet flavor and firm texture. Perfect for grilling or sautéing.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Peeled & Deveined", "Large Size", "Sweet Flavor"],
            colors: ["Pink"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 46,
            name: "Wild Cod Fillets",
            price: 11.99,
            image: "https://images.unsplash.com/photo-1599084993091-1cb5c0721cc6?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Northern Waters",
            description: "Fresh wild-caught cod fillets. Mild flavor and flaky texture. Perfect for baking or pan-frying.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Wild Caught", "Mild Flavor", "Flaky Texture", "Sustainable"],
            colors: ["White"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 71,
            name: "Wild Tuna Steaks",
            price: 16.99,
            originalPrice: 19.99,
            image: "https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Pacific Fresh",
            description: "Premium wild-caught tuna steaks. Perfect for grilling or searing. Rich in protein and omega-3.",
            rating: 4.8,
            isNew: true,
            sale: true,
            specifications: ["Wild Caught", "Premium", "High Protein", "Omega-3 Rich"],
            colors: ["Red"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 72,
            name: "Fresh Scallops",
            price: 22.99,
            image: "https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=300&h=300&fit=crop",
            category: "seafood",
            brand: "Bay Harvest",
            description: "Large fresh sea scallops. Sweet and tender. Perfect for pan-searing or grilling.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Fresh", "Large Size", "Sweet", "Tender"],
            colors: ["White"],
            sizes: ["1lb"]
        },

        // PANTRY STAPLES
        {
            id: 21,
            name: "Organic Quinoa",
            price: 7.99,
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Ancient Grains",
            description: "Premium organic quinoa. Complete protein and gluten-free. Nutty flavor and fluffy texture.",
            rating: 4.7,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Complete Protein", "Gluten Free", "Ancient Grain"],
            colors: ["Beige"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 22,
            name: "Organic Brown Rice",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Grain Harvest",
            description: "Long grain organic brown rice. Nutty flavor and chewy texture. High in fiber and nutrients.",
            rating: 4.5,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Long Grain", "High Fiber", "Whole Grain"],
            colors: ["Brown"],
            sizes: ["2lb", "5lb"]
        },
        {
            id: 23,
            name: "Organic Olive Oil",
            price: 12.99,
            image: "https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Mediterranean Gold",
            description: "Extra virgin organic olive oil. Cold pressed and unfiltered. Rich flavor perfect for cooking and dressing.",
            rating: 4.8,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Extra Virgin", "Cold Pressed", "Unfiltered"],
            colors: ["Golden"],
            sizes: ["500ml", "1L"]
        },
        {
            id: 24,
            name: "Organic Pasta",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Pasta Perfection",
            description: "Organic durum wheat pasta. Traditional Italian recipe. Perfect al dente texture every time.",
            rating: 4.6,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Durum Wheat", "Italian Recipe", "Perfect Texture"],
            colors: ["Yellow"],
            sizes: ["1lb"]
        },
        {
            id: 47,
            name: "Organic Coconut Oil",
            price: 8.99,
            originalPrice: 11.99,
            image: "https://images.unsplash.com/photo-1471943311424-646960669fbc?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Tropical Oils",
            description: "Virgin organic coconut oil. Great for cooking, baking, and beauty applications. Natural and pure.",
            rating: 4.6,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Virgin", "Multi-Purpose", "Natural"],
            colors: ["White"],
            sizes: ["16oz", "32oz"]
        },
        {
            id: 48,
            name: "Organic Chia Seeds",
            price: 9.99,
            image: "https://images.unsplash.com/photo-1517467139951-f5a925c9cd04?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Super Seeds",
            description: "Organic chia seeds packed with omega-3, fiber, and protein. Perfect for smoothies and puddings.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "High Omega-3", "High Fiber", "Superfood"],
            colors: ["Black"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 73,
            name: "Organic Black Beans",
            price: 2.99,
            originalPrice: 3.99,
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Bean Co",
            description: "Organic black beans. High in protein and fiber. Perfect for soups, salads, and Mexican dishes.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "High Protein", "High Fiber", "Versatile"],
            colors: ["Black"],
            sizes: ["15oz", "30oz"]
        },
        {
            id: 74,
            name: "Organic Almonds",
            price: 11.99,
            image: "https://images.unsplash.com/photo-1589118949207-c0c2bec417c5?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Nut Harvest",
            description: "Raw organic almonds. Rich in healthy fats, protein, and vitamin E. Perfect for snacking or baking.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Raw", "Healthy Fats", "Vitamin E"],
            colors: ["Brown"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 75,
            name: "Organic Oats",
            price: 5.99,
            image: "https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop",
            category: "pantry",
            brand: "Oat Fields",
            description: "Organic rolled oats. Perfect for breakfast, baking, or smoothies. High in fiber and nutrients.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Rolled Oats", "High Fiber", "Versatile"],
            colors: ["Beige"],
            sizes: ["32oz", "64oz"]
        },

        // BEVERAGES
        {
            id: 25,
            name: "Organic Green Tea",
            price: 8.99,
            originalPrice: 10.99,
            image: "https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Pure Tea Co",
            description: "Premium organic green tea with antioxidants. Smooth flavor and natural energy boost.",
            rating: 4.7,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Antioxidants", "Natural Energy", "Smooth Flavor"],
            colors: ["Green"],
            sizes: ["20 bags", "50 bags"]
        },
        {
            id: 26,
            name: "Fresh Orange Juice",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Citrus Fresh",
            description: "100% pure orange juice. No added sugar, preservatives, or artificial flavors. Fresh squeezed.",
            rating: 4.8,
            isNew: false,
            sale: false,
            specifications: ["100% Pure", "No Added Sugar", "Fresh Squeezed", "Vitamin C Rich"],
            colors: ["Orange"],
            sizes: ["16oz", "32oz", "64oz"]
        },
        {
            id: 27,
            name: "Organic Coffee Beans",
            price: 12.99,
            originalPrice: 15.99,
            image: "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Mountain Roast",
            description: "Fair trade organic coffee beans. Medium roast with rich flavor and smooth finish.",
            rating: 4.9,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Fair Trade", "Medium Roast", "Rich Flavor"],
            colors: ["Brown"],
            sizes: ["12oz", "1lb", "2lb"]
        },
        {
            id: 49,
            name: "Organic Herbal Tea Mix",
            price: 7.99,
            image: "https://images.unsplash.com/photo-1564890273350-56d38bf2d9b9?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Herbal Blends",
            description: "Soothing organic herbal tea blend. Chamomile, lavender, and lemon balm. Perfect for relaxation.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Herbal Blend", "Caffeine Free", "Relaxing"],
            colors: ["Mixed"],
            sizes: ["20 bags", "40 bags"]
        },
        {
            id: 50,
            name: "Organic Almond Milk",
            price: 3.99,
            originalPrice: 4.99,
            image: "https://images.unsplash.com/photo-1563636619-e9143da7973b?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Nut Milk Co",
            description: "Creamy organic almond milk. Dairy-free and enriched with vitamins. Perfect for cereals and smoothies.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Dairy Free", "Vitamin Enriched", "Creamy"],
            colors: ["White"],
            sizes: ["32oz", "64oz"]
        },
        {
            id: 76,
            name: "Organic Coconut Water",
            price: 6.99,
            image: "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Tropical Pure",
            description: "Pure organic coconut water. Natural electrolytes and refreshing taste. Perfect post-workout drink.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Natural Electrolytes", "Pure", "Refreshing"],
            colors: ["Clear"],
            sizes: ["16oz", "32oz"]
        },
        {
            id: 77,
            name: "Organic Kombucha",
            price: 4.49,
            originalPrice: 5.99,
            image: "https://images.unsplash.com/photo-1564890273350-56d38bf2d9b9?w=300&h=300&fit=crop",
            category: "beverages",
            brand: "Probiotic Brew",
            description: "Organic kombucha with live cultures. Ginger and lemon flavor. Great for digestive health.",
            rating: 4.3,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Live Cultures", "Probiotic", "Digestive Health"],
            colors: ["Amber"],
            sizes: ["16oz", "32oz"]
        },

        // SNACKS
        {
            id: 28,
            name: "Organic Mixed Nuts",
            price: 9.99,
            image: "https://images.unsplash.com/photo-1589118949207-c0c2bec417c5?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Nutty Goodness",
            description: "Premium mix of organic nuts. Almonds, walnuts, cashews, and pecans. Perfect healthy snack.",
            rating: 4.6,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Mixed Nuts", "Healthy Snack", "No Salt Added"],
            colors: ["Mixed"],
            sizes: ["8oz", "16oz", "32oz"]
        },
        {
            id: 29,
            name: "Organic Dark Chocolate",
            price: 6.99,
            originalPrice: 8.99,
            image: "https://images.unsplash.com/photo-1481391243133-f96216dcb5d2?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Pure Chocolate",
            description: "70% organic dark chocolate. Rich, smooth, and made with sustainably sourced cocoa.",
            rating: 4.8,
            isNew: true,
            sale: true,
            specifications: ["Organic", "70% Cocoa", "Sustainably Sourced", "Rich Flavor"],
            colors: ["Dark Brown"],
            sizes: ["3.5oz", "7oz"]
        },
        {
            id: 30,
            name: "Organic Granola Bars",
            price: 7.49,
            image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Nature's Energy",
            description: "Organic granola bars with oats, honey, and mixed berries. Perfect on-the-go snack.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Oats & Honey", "Mixed Berries", "On-the-Go"],
            colors: ["Brown"],
            sizes: ["6-pack", "12-pack"]
        },
        {
            id: 51,
            name: "Organic Popcorn",
            price: 5.49,
            image: "https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Pop Organic",
            description: "Air-popped organic popcorn. Light, fluffy, and seasoned with sea salt. Perfect movie snack.",
            rating: 4.3,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Air Popped", "Sea Salt", "Light & Fluffy"],
            colors: ["Yellow"],
            sizes: ["5oz", "10oz"]
        },
        {
            id: 52,
            name: "Organic Trail Mix",
            price: 8.99,
            originalPrice: 10.99,
            image: "https://images.unsplash.com/photo-1621939514649-280e2985fb31?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Adventure Snacks",
            description: "Organic trail mix with nuts, seeds, and dried fruits. Perfect for hiking or energy boost.",
            rating: 4.6,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Mixed Nuts", "Dried Fruits", "Energy Boost"],
            colors: ["Mixed"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 78,
            name: "Organic Crackers",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Crunch Co",
            description: "Organic whole grain crackers. Perfect with cheese or dips. Made with simple ingredients.",
            rating: 4.4,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Whole Grain", "Simple Ingredients", "Versatile"],
            colors: ["Brown"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 79,
            name: "Organic Fruit Leather",
            price: 3.99,
            originalPrice: 5.49,
            image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop",
            category: "snacks",
            brand: "Fruit Pure",
            description: "Organic fruit leather made from real fruit. No added sugar or preservatives. Kid-friendly snack.",
            rating: 4.2,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Real Fruit", "No Added Sugar", "Kid-Friendly"],
            colors: ["Mixed"],
            sizes: ["6-pack", "12-pack"]
        },

        // HERBS & SPICES
        {
            id: 31,
            name: "Organic Basil",
            price: 2.99,
            image: "https://images.unsplash.com/photo-1618375569909-3c8616cf7733?w=300&h=300&fit=crop",
            category: "herbs",
            brand: "Garden Fresh",
            description: "Fresh organic basil leaves. Aromatic and perfect for cooking or making pesto.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Fresh", "Aromatic", "Perfect for Pesto"],
            colors: ["Green"],
            sizes: ["1 bunch", "2 bunches"]
        },
        {
            id: 32,
            name: "Organic Turmeric Powder",
            price: 5.99,
            originalPrice: 7.49,
            image: "https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop",
            category: "herbs",
            brand: "Spice World",
            description: "Premium organic turmeric powder. Anti-inflammatory properties and golden color.",
            rating: 4.8,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Anti-inflammatory", "Premium Quality", "Golden Color"],
            colors: ["Golden"],
            sizes: ["4oz", "8oz"]
        },
        {
            id: 53,
            name: "Organic Oregano",
            price: 3.49,
            image: "https://images.unsplash.com/photo-1594736797933-d0ce65d6776a?w=300&h=300&fit=crop",
            category: "herbs",
            brand: "Mediterranean Herbs",
            description: "Dried organic oregano. Perfect for Italian dishes, pizza, and Mediterranean cooking.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Dried", "Mediterranean", "Aromatic"],
            colors: ["Green"],
            sizes: ["1oz", "2oz"]
        },
        {
            id: 54,
            name: "Organic Ginger Root",
            price: 4.99,
            image: "https://images.unsplash.com/photo-1599735815516-b8a0e8c5d8db?w=300&h=300&fit=crop",
            category: "herbs",
            brand: "Fresh Roots",
            description: "Fresh organic ginger root. Perfect for teas, cooking, and natural remedies. Immune boosting.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Fresh", "Immune Boosting", "Natural"],
            colors: ["Tan"],
            sizes: ["4oz", "8oz"]
        },
        {
            id: 80,
            name: "Organic Rosemary",
            price: 3.99,
            image: "https://images.unsplash.com/photo-1618375569909-3c8616cf7733?w=300&h=300&fit=crop",
            category: "herbs",
            brand: "Herb Garden",
            description: "Fresh organic rosemary sprigs. Perfect for roasting meats and vegetables. Aromatic and flavorful.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Fresh", "Aromatic", "Perfect for Roasting"],
            colors: ["Green"],
            sizes: ["1 bunch", "2 bunches"]
        },

        // FROZEN
        {
            id: 33,
            name: "Organic Frozen Berries",
            price: 8.99,
            image: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop",
            category: "frozen",
            brand: "Frozen Fresh",
            description: "Mix of organic frozen berries. Strawberries, blueberries, and raspberries. Perfect for smoothies.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Mixed Berries", "Frozen Fresh", "Perfect for Smoothies"],
            colors: ["Mixed"],
            sizes: ["10oz", "32oz"]
        },
        {
            id: 34,
            name: "Organic Frozen Vegetables",
            price: 5.99,
            originalPrice: 7.99,
            image: "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=300&h=300&fit=crop",
            category: "frozen",
            brand: "Frozen Garden",
            description: "Organic mixed vegetables. Broccoli, carrots, and green beans. Flash frozen for freshness.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Mixed Vegetables", "Flash Frozen", "Fresh"],
            colors: ["Mixed"],
            sizes: ["16oz", "32oz"]
        },
        {
            id: 55,
            name: "Organic Frozen Mango",
            price: 6.99,
            image: "https://images.unsplash.com/photo-1553279764-3325c6256d41?w=300&h=300&fit=crop",
            category: "frozen",
            brand: "Tropical Frozen",
            description: "Organic frozen mango chunks. Sweet tropical flavor, perfect for smoothies and desserts.",
            rating: 4.7,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Tropical", "Sweet", "Smoothie Ready"],
            colors: ["Orange"],
            sizes: ["16oz", "32oz"]
        },
        {
            id: 81,
            name: "Organic Frozen Spinach",
            price: 3.99,
            originalPrice: 5.49,
            image: "https://images.unsplash.com/photo-1490818387583-1baba5e638af?w=300&h=300&fit=crop",
            category: "frozen",
            brand: "Green Frozen",
            description: "Organic frozen spinach. Chopped and ready to use. Perfect for smoothies, soups, and dishes.",
            rating: 4.3,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Chopped", "Ready to Use", "Versatile"],
            colors: ["Green"],
            sizes: ["10oz", "16oz"]
        },

        // CONDIMENTS
        {
            id: 35,
            name: "Organic Honey",
            price: 9.99,
            image: "https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=300&h=300&fit=crop",
            category: "condiments",
            brand: "Pure Honey Co",
            description: "Raw organic honey from local beekeepers. Pure, unfiltered, and full of natural enzymes.",
            rating: 4.9,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Raw", "Unfiltered", "Local"],
            colors: ["Golden"],
            sizes: ["12oz", "24oz"]
        },
        {
            id: 36,
            name: "Organic Apple Cider Vinegar",
            price: 4.99,
            originalPrice: 6.49,
            image: "https://images.unsplash.com/photo-1609501676725-7186f522c2c5?w=300&h=300&fit=crop",
            category: "condiments",
            brand: "Orchard Vinegar",
            description: "Organic apple cider vinegar with the mother. Great for cooking and health benefits.",
            rating: 4.7,
            isNew: false,
            sale: true,
            specifications: ["Organic", "With Mother", "Health Benefits", "Cooking"],
            colors: ["Amber"],
            sizes: ["16oz", "32oz"]
        },
        {
            id: 56,
            name: "Organic Maple Syrup",
            price: 11.99,
            image: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop",
            category: "condiments",
            brand: "Maple Grove",
            description: "Pure organic maple syrup. Grade A, dark robust flavor. Perfect for pancakes and baking.",
            rating: 4.8,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Grade A", "Pure", "Robust Flavor"],
            colors: ["Amber"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 57,
            name: "Organic Hot Sauce",
            price: 6.99,
            originalPrice: 8.49,
            image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop",
            category: "condiments",
            brand: "Fire Garden",
            description: "Organic hot sauce made with fresh peppers. Medium heat with great flavor. No artificial additives.",
            rating: 4.5,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Fresh Peppers", "Medium Heat", "No Additives"],
            colors: ["Red"],
            sizes: ["5oz", "10oz"]
        },
        {
            id: 82,
            name: "Organic Mustard",
            price: 4.49,
            image: "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=300&h=300&fit=crop",
            category: "condiments",
            brand: "Artisan Condiments",
            description: "Organic Dijon mustard. Smooth and tangy flavor. Perfect for sandwiches and cooking.",
            rating: 4.4,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Dijon", "Smooth", "Tangy Flavor"],
            colors: ["Yellow"],
            sizes: ["8oz", "12oz"]
        },

        // SPECIALTY & SUPERFOODS
        {
            id: 58,
            name: "Organic Spirulina Powder",
            price: 19.99,
            image: "https://images.unsplash.com/photo-1517467139951-f5a925c9cd04?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Green Power",
            description: "Pure organic spirulina powder. Superfood packed with protein, vitamins, and minerals.",
            rating: 4.6,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Superfood", "High Protein", "Nutrient Dense"],
            colors: ["Green"],
            sizes: ["4oz", "8oz"]
        },
        {
            id: 59,
            name: "Organic Acai Powder",
            price: 24.99,
            originalPrice: 29.99,
            image: "https://images.unsplash.com/photo-1562679160-e873c6e41b5c?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Amazon Superfoods",
            description: "Freeze-dried organic acai powder. Rich in antioxidants and perfect for smoothie bowls.",
            rating: 4.7,
            isNew: true,
            sale: true,
            specifications: ["Organic", "Freeze Dried", "High Antioxidants", "Smoothie Bowl"],
            colors: ["Purple"],
            sizes: ["4oz", "8oz"]
        },
        {
            id: 60,
            name: "Organic Protein Powder",
            price: 34.99,
            image: "https://images.unsplash.com/photo-1593095948071-474c5cc2989d?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Plant Power",
            description: "Plant-based organic protein powder. Pea and hemp protein blend. Great for post-workout.",
            rating: 4.5,
            isNew: false,
            sale: false,
            specifications: ["Organic", "Plant Based", "Pea & Hemp", "Post Workout"],
            colors: ["Beige"],
            sizes: ["1lb", "2lb"]
        },
        {
            id: 83,
            name: "Organic Wheatgrass Powder",
            price: 16.99,
            originalPrice: 21.99,
            image: "https://images.unsplash.com/photo-1517467139951-f5a925c9cd04?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Green Life",
            description: "Pure organic wheatgrass powder. Detoxifying and energizing superfood. Rich in chlorophyll.",
            rating: 4.4,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Detoxifying", "Energizing", "High Chlorophyll"],
            colors: ["Green"],
            sizes: ["4oz", "8oz"]
        },
        {
            id: 84,
            name: "Organic Maca Powder",
            price: 18.99,
            image: "https://images.unsplash.com/photo-1517467139951-f5a925c9cd04?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Andes Nutrition",
            description: "Organic maca root powder. Adaptogenic superfood for energy and vitality. Nutty flavor.",
            rating: 4.5,
            isNew: true,
            sale: false,
            specifications: ["Organic", "Adaptogenic", "Energy Boost", "Nutty Flavor"],
            colors: ["Cream"],
            sizes: ["8oz", "16oz"]
        },
        {
            id: 85,
            name: "Organic Cacao Powder",
            price: 12.99,
            originalPrice: 15.99,
            image: "https://images.unsplash.com/photo-1517467139951-f5a925c9cd04?w=300&h=300&fit=crop",
            category: "superfoods",
            brand: "Raw Cacao Co",
            description: "Raw organic cacao powder. Rich in antioxidants and minerals. Perfect for smoothies and baking.",
            rating: 4.6,
            isNew: false,
            sale: true,
            specifications: ["Organic", "Raw", "High Antioxidants", "Rich in Minerals"],
            colors: ["Brown"],
            sizes: ["8oz", "16oz"]
        }
    ];
}

// Get product by ID
function getProductById(id) {
    return getAllProducts().find(product => product.id === parseInt(id));
}

// Get filtered products
function getFilteredProducts(filters = {}) {
    let products = getAllProducts();
    
    // Filter by search term
    if (filters.search) {
        const searchTerm = filters.search.toLowerCase();
        products = products.filter(product =>
            product.name.toLowerCase().includes(searchTerm) ||
            product.description.toLowerCase().includes(searchTerm) ||
            product.category.toLowerCase().includes(searchTerm) ||
            product.brand.toLowerCase().includes(searchTerm)
        );
    }
    
    // Filter by category
    if (filters.category) {
        products = products.filter(product => product.category === filters.category);
    }
    
    // Filter by price range
    if (filters.minPrice !== undefined) {
        products = products.filter(product => product.price >= filters.minPrice);
    }
    if (filters.maxPrice !== undefined) {
        products = products.filter(product => product.price <= filters.maxPrice);
    }
    
    // Filter by sale
    if (filters.sale) {
        products = products.filter(product => product.sale);
    }
    
    // Filter by new
    if (filters.new) {
        products = products.filter(product => product.isNew);
    }
    
    // Sort products
    if (filters.sortBy) {
        switch (filters.sortBy) {
            case 'price-low':
                products.sort((a, b) => a.price - b.price);
                break;
            case 'price-high':
                products.sort((a, b) => b.price - a.price);
                break;
            case 'rating':
                products.sort((a, b) => b.rating - a.rating);
                break;
            case 'name':
                products.sort((a, b) => a.name.localeCompare(b.name));
                break;
            case 'newest':
                products.sort((a, b) => (b.isNew ? 1 : 0) - (a.isNew ? 1 : 0));
                break;
            case 'featured':
            default:
                // Keep original order for featured
                break;
        }
    }
    
    return products;
}

// Get categories
function getCategories() {
    return [
        { id: 'vegetables', name: 'Vegetables', icon: '🥬', description: 'Fresh organic vegetables' },
        { id: 'fruits', name: 'Fruits', icon: '🍎', description: 'Sweet organic fruits' },
        { id: 'dairy', name: 'Dairy', icon: '🥛', description: 'Fresh dairy products' },
        { id: 'bakery', name: 'Bakery', icon: '🍞', description: 'Fresh baked goods' },
        { id: 'seafood', name: 'Seafood', icon: '🐟', description: 'Fresh & sustainable seafood' },
        { id: 'pantry', name: 'Pantry', icon: '🌾', description: 'Pantry essentials' },
        { id: 'beverages', name: 'Beverages', icon: '🥤', description: 'Healthy drinks' },
        { id: 'snacks', name: 'Snacks', icon: '🥜', description: 'Healthy snacks' },
        { id: 'herbs', name: 'Herbs & Spices', icon: '🌿', description: 'Fresh herbs & spices' },
        { id: 'frozen', name: 'Frozen', icon: '❄️', description: 'Frozen organic foods' },
        { id: 'condiments', name: 'Condiments', icon: '🍯', description: 'Sauces & condiments' },
        { id: 'superfoods', name: 'Superfoods', icon: '💚', description: 'Nutrient-dense superfoods' }
    ];
}

// Get subcategories for mega menu
function getSubcategories() {
    return {
        vegetables: [
            { name: 'Leafy Greens', link: 'products.html?category=vegetables&type=leafy' },
            { name: 'Root Vegetables', link: 'products.html?category=vegetables&type=root' },
            { name: 'Tomatoes', link: 'products.html?category=vegetables&type=tomatoes' },
            { name: 'Peppers', link: 'products.html?category=vegetables&type=peppers' }
        ],
        fruits: [
            { name: 'Citrus Fruits', link: 'products.html?category=fruits&type=citrus' },
            { name: 'Berries', link: 'products.html?category=fruits&type=berries' },
            { name: 'Tropical Fruits', link: 'products.html?category=fruits&type=tropical' },
            { name: 'Stone Fruits', link: 'products.html?category=fruits&type=stone' }
        ],
        dairy: [
            { name: 'Milk & Cream', link: 'products.html?category=dairy&type=milk' },
            { name: 'Cheese', link: 'products.html?category=dairy&type=cheese' },
            { name: 'Yogurt', link: 'products.html?category=dairy&type=yogurt' },
            { name: 'Eggs', link: 'products.html?category=dairy&type=eggs' }
        ],
        beverages: [
            { name: 'Tea & Coffee', link: 'products.html?category=beverages&type=hot' },
            { name: 'Juices', link: 'products.html?category=beverages&type=juice' },
            { name: 'Plant Milks', link: 'products.html?category=beverages&type=plant' },
            { name: 'Health Drinks', link: 'products.html?category=beverages&type=health' }
        ],
        pantry: [
            { name: 'Grains & Rice', link: 'products.html?category=pantry&type=grains' },
            { name: 'Oils & Vinegars', link: 'products.html?category=pantry&type=oils' },
            { name: 'Pasta & Noodles', link: 'products.html?category=pantry&type=pasta' },
            { name: 'Seeds & Nuts', link: 'products.html?category=pantry&type=seeds' }
        ],
        superfoods: [
            { name: 'Protein Powders', link: 'products.html?category=superfoods&type=protein' },
            { name: 'Green Powders', link: 'products.html?category=superfoods&type=greens' },
            { name: 'Antioxidant Boost', link: 'products.html?category=superfoods&type=antioxidant' },
            { name: 'Energy & Vitality', link: 'products.html?category=superfoods&type=energy' }
        ]
    };
}

// Get brands
function getBrands() {
    const products = getAllProducts();
    return [...new Set(products.map(p => p.brand))].sort();
}

// Get specifications
function getSpecifications() {
    const products = getAllProducts();
    const specs = new Set();
    products.forEach(product => {
        if (product.specifications) {
            product.specifications.forEach(spec => specs.add(spec));
        }
    });
    return [...specs].sort();
}