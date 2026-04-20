/**
 * Mobile Menu Enhancement - Independent Collapse/Expand
 * Each submenu works independently without affecting others
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 Mobile Menu Enhancement Initialized');
    
    // Handle all submenu triggers independently
    document.querySelectorAll('[data-submenu-target]').forEach(trigger => {
        setupIndependentSubmenu(trigger);
    });
    
    // Handle mobile menu open/close
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        mobileMenu.addEventListener('show.bs.offcanvas', onMobileMenuOpen);
        mobileMenu.addEventListener('hide.bs.offcanvas', onMobileMenuClose);
    }
});

function setupIndependentSubmenu(trigger) {
    // Add click listener
    trigger.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const targetId = this.getAttribute('data-submenu-target');
        const target = document.querySelector(targetId);
        
        if (target) {
            const isOpen = target.classList.contains('show');
            
            if (isOpen) {
                // Close the submenu
                closeSubmenu(this, target);
            } else {
                // Open the submenu
                openSubmenu(this, target);
            }
        }
    });
}

function openSubmenu(trigger, target) {
    // Add show class to target
    target.classList.add('show');
    
    // Update trigger attributes
    trigger.setAttribute('aria-expanded', 'true');
    trigger.classList.add('submenu-open');
    
    console.log('📱 Submenu opened:', trigger.textContent.trim());
}

function closeSubmenu(trigger, target) {
    // Remove show class from target
    target.classList.remove('show');
    
    // Update trigger attributes
    trigger.setAttribute('aria-expanded', 'false');
    trigger.classList.remove('submenu-open');
    
    console.log('📱 Submenu closed:', trigger.textContent.trim());
}


function onMobileMenuOpen() {
    console.log('📱 Mobile menu opened');
    document.body.classList.add('mobile-menu-open');
}

function onMobileMenuClose() {
    console.log('📱 Mobile menu closed');
    document.body.classList.remove('mobile-menu-open');
    
    // Close all submenus when mobile menu closes
    document.querySelectorAll('.collapse.show').forEach(collapse => {
        collapse.classList.remove('show');
    });
    
    // Reset all triggers
    document.querySelectorAll('[data-submenu-target]').forEach(trigger => {
        trigger.setAttribute('aria-expanded', 'false');
        trigger.classList.remove('submenu-open');
        trigger.style.backgroundColor = '';
    });
}

// Global functions for external access
window.toggleMobileMenu = function() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        const bsOffcanvas = new bootstrap.Offcanvas(mobileMenu);
        bsOffcanvas.toggle();
    }
};

window.closeMobileMenu = function() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        const bsOffcanvas = new bootstrap.Offcanvas(mobileMenu);
        bsOffcanvas.hide();
    }
};