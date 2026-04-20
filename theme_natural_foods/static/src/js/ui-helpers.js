// UI Helper Functions - Notifications and other UI utilities

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification fixed top-6 right-6 z-50 max-w-sm bg-white border border-gray-200 rounded-xl shadow-xl p-4 transform translate-x-full transition-all duration-500 ease-out`;
    
    // Set notification style based on type
    let iconClass = 'text-blue-600';
    let bgClass = 'bg-blue-50';
    let borderClass = 'border-blue-200';
    let icon = 'info';
    
    switch (type) {
        case 'success':
            iconClass = 'text-green-600';
            bgClass = 'bg-green-50';
            borderClass = 'border-green-200';
            icon = 'check-circle';
            break;
        case 'error':
            iconClass = 'text-red-600';
            bgClass = 'bg-red-50';
            borderClass = 'border-red-200';
            icon = 'x-circle';
            break;
        case 'warning':
            iconClass = 'text-yellow-600';
            bgClass = 'bg-yellow-50';
            borderClass = 'border-yellow-200';
            icon = 'alert-triangle';
            break;
        default: // info
            iconClass = 'text-blue-600';
            bgClass = 'bg-blue-50';
            borderClass = 'border-blue-200';
            icon = 'info';
    }
    
    notification.innerHTML = `
        <div class="flex items-start gap-3">
            <div class="${bgClass} ${borderClass} p-2 rounded-full border">
                <i data-lucide="${icon}" class="h-4 w-4 ${iconClass}"></i>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-gray-900 font-medium leading-relaxed">${message}</p>
            </div>
            <button onclick="this.closest('.notification').remove()" 
                    class="text-gray-400 hover:text-gray-600 transition-colors p-1">
                <i data-lucide="x" class="h-4 w-4"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
        notification.classList.add('translate-x-0');
    }, 100);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.classList.remove('translate-x-0');
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    notification.remove();
                }
            }, 500);
        }
    }, 5000);
}

// Search functionality
function performSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    const query = searchInput.value.trim();
    
    if (query.length === 0) {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    // Simulate search (redirect to products page with search parameter)
    if (query.length > 0) {
        window.location.href = `products.html?search=${encodeURIComponent(query)}`;
    }
}

// Loading spinner utility
function showLoadingSpinner(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="col-span-full flex items-center justify-center py-12">
            <div class="text-center">
                <div class="w-12 h-12 border-4 border-green-200 border-t-green-600 rounded-full animate-spin mx-auto mb-4"></div>
                <p class="text-gray-600">Loading...</p>
            </div>
        </div>
    `;
}

// Error message utility
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <div class="max-w-md mx-auto">
                <div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i data-lucide="x-circle" class="h-8 w-8 text-red-600"></i>
                </div>
                <h3 class="text-xl font-bold text-gray-900 mb-2">Error</h3>
                <p class="text-gray-600 mb-6">${message}</p>
                <button onclick="location.reload()" class="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium transition-colors">
                    Try Again
                </button>
            </div>
        </div>
    `;
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Smooth scroll utility
function smoothScrollTo(targetId) {
    const target = document.getElementById(targetId);
    if (target) {
        target.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Format currency utility
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date utility
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
}

// Debounce utility for search
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Copy to clipboard utility
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Failed to copy to clipboard', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            showNotification('Failed to copy to clipboard', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Generate random ID utility
function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

// Validate email utility
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Image lazy loading utility
function lazyLoadImages() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Initialize animations utility
function initializeAnimations() {
    // Add entrance animations to elements as they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-slide-up');
                animationObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => animationObserver.observe(el));
}

// Resize utility for responsive handling
function handleResize() {
    // Update mobile menu visibility
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu && window.innerWidth >= 768) {
        mobileMenu.classList.add('hidden');
    }
    
    // Update grid columns for responsive layouts
    const responsiveGrids = document.querySelectorAll('.responsive-grid');
    responsiveGrids.forEach(grid => {
        if (window.innerWidth < 640) {
            grid.className = grid.className.replace(/grid-cols-\d+/, 'grid-cols-1');
        } else if (window.innerWidth < 1024) {
            grid.className = grid.className.replace(/grid-cols-\d+/, 'grid-cols-2');
        }
    });
}

// Local storage utilities
const storage = {
    get: (key) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : null;
        } catch (error) {
            console.error('Error reading from localStorage:', error);
            return null;
        }
    },
    
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Error writing to localStorage:', error);
            return false;
        }
    },
    
    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Error removing from localStorage:', error);
            return false;
        }
    },
    
    clear: () => {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.error('Error clearing localStorage:', error);
            return false;
        }
    }
};

// Initialize resize handler
if (typeof window !== 'undefined') {
    window.addEventListener('resize', debounce(handleResize, 250));
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.showNotification = showNotification;
    window.performSearch = performSearch;
    window.showLoadingSpinner = showLoadingSpinner;
    window.showError = showError;
    window.smoothScrollTo = smoothScrollTo;
    window.formatCurrency = formatCurrency;
    window.formatDate = formatDate;
    window.debounce = debounce;
    window.copyToClipboard = copyToClipboard;
    window.generateId = generateId;
    window.isValidEmail = isValidEmail;
    window.lazyLoadImages = lazyLoadImages;
    window.initializeAnimations = initializeAnimations;
    window.handleResize = handleResize;
    window.storage = storage;
}