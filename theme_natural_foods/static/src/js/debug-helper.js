// Debug Helper for Natural Foods Static HTML Version
console.log('🔍 Loading debug-helper.js...');

// Debug information collector
function collectDebugInfo() {
    const debugInfo = {
        timestamp: new Date().toISOString(),
        page: window.location.pathname,
        userAgent: navigator.userAgent,
        domReady: document.readyState,
        elementsCheck: {}
    };
    
    // Check for key DOM elements
    const keyElements = [
        'hot-deals',
        'new-arrivals', 
        'featured-products',
        'tab-products',
        'recipe-section',
        'tab-vegetables',
        'tab-fruits',
        'tab-dairy',
        'tab-bakery'
    ];
    
    keyElements.forEach(id => {
        const element = document.getElementById(id);
        debugInfo.elementsCheck[id] = {
            exists: !!element,
            innerHTML: element ? element.innerHTML.substring(0, 100) + '...' : null,
            hasContent: element ? element.children.length > 0 : false
        };
    });
    
    return debugInfo;
}

// Function to log debug info
function logDebugInfo() {
    const info = collectDebugInfo();
    console.log('🔍 DEBUG INFO:', info);
    
    // Check for missing elements
    const missingElements = Object.keys(info.elementsCheck).filter(id => 
        !info.elementsCheck[id].exists
    );
    
    if (missingElements.length > 0) {
        console.error('❌ Missing DOM elements:', missingElements);
    }
    
    // Check for empty elements
    const emptyElements = Object.keys(info.elementsCheck).filter(id => 
        info.elementsCheck[id].exists && !info.elementsCheck[id].hasContent
    );
    
    if (emptyElements.length > 0) {
        console.warn('⚠️ Empty DOM elements:', emptyElements);
    }
    
    return info;
}

// Function to check JavaScript dependencies
function checkJSDependencies() {
    console.log('🔍 Checking JavaScript dependencies...');
    
    const dependencies = [
        'lucide',
        'getAllProducts',
        'getAllRecipes',
        'initializeOrganicStore',
        'setActiveTab',
        'createProductCard',
        'createRecipeCard'
    ];
    
    const results = {};
    
    dependencies.forEach(dep => {
        results[dep] = {
            available: typeof window[dep] !== 'undefined',
            type: typeof window[dep]
        };
    });
    
    console.log('📊 Dependency check results:', results);
    
    const missing = Object.keys(results).filter(dep => !results[dep].available);
    if (missing.length > 0) {
        console.error('❌ Missing dependencies:', missing);
    }
    
    return results;
}

// Function to manually trigger initialization
function manualInit() {
    console.log('🔧 Manual initialization triggered...');
    
    try {
        // Force initialization
        if (typeof initializeOrganicStore === 'function') {
            initializeOrganicStore();
        } else {
            console.error('❌ initializeOrganicStore function not available');
        }
    } catch (error) {
        console.error('❌ Manual initialization failed:', error);
    }
}

// Function to test specific sections
function testSection(sectionName) {
    console.log(`🧪 Testing section: ${sectionName}`);
    
    switch (sectionName) {
        case 'products':
            if (typeof setActiveTab === 'function') {
                setActiveTab('vegetables');
            } else {
                console.error('❌ setActiveTab function not available');
            }
            break;
            
        case 'recipes':
            const container = document.getElementById('recipe-section');
            if (container) {
                container.innerHTML = '<div class="text-center">Testing recipes...</div>';
                console.log('✅ Recipe container updated');
            } else {
                console.error('❌ Recipe container not found');
            }
            break;
            
        default:
            console.log('❓ Unknown section:', sectionName);
    }
}

// Comprehensive page analysis
function analyzePage() {
    console.log('🔍 Analyzing page...');
    
    const analysis = {
        debugInfo: collectDebugInfo(),
        dependencies: checkJSDependencies(),
        scripts: Array.from(document.scripts).map(script => ({
            src: script.src,
            hasContent: script.innerHTML.length > 0
        })),
        stylesheets: Array.from(document.styleSheets).map(sheet => ({
            href: sheet.href,
            rules: sheet.cssRules ? sheet.cssRules.length : 0
        }))
    };
    
    console.log('📊 Complete page analysis:', analysis);
    return analysis;
}

// Auto-run debug on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Debug helper loaded, running initial checks...');
    
    setTimeout(() => {
        logDebugInfo();
        checkJSDependencies();
    }, 1000);
    
    // Run a more comprehensive check after 3 seconds
    setTimeout(() => {
        console.log('🔍 Running comprehensive analysis...');
        analyzePage();
    }, 3000);
});

// Make debug functions globally available
window.debugHelper = {
    collectDebugInfo,
    logDebugInfo,
    checkJSDependencies,
    manualInit,
    testSection,
    analyzePage
};

console.log('✅ Debug helper loaded');
console.log('💡 Use debugHelper.manualInit() to manually initialize');
console.log('💡 Use debugHelper.testSection("products") or debugHelper.testSection("recipes") to test specific sections');
console.log('💡 Use debugHelper.analyzePage() for comprehensive analysis');