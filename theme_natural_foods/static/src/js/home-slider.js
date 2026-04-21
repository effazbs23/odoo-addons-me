// Home Page Slider Functionality
class HomeSlider {
    constructor() {
        this.currentSlide = 0;
        this.slides = [];
        this.dots = [];
        this.totalSlides = 0;
        this.autoPlayInterval = null;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.slides = document.querySelectorAll('.slider-slide');
        this.dots = document.querySelectorAll('.slider-dot');
        this.totalSlides = this.slides.length;

        if (this.totalSlides === 0) {
            console.warn('No slider slides found');
            return;
        }

        // Start auto-play
        //this.startAutoPlay();

        console.log(`✅ Home slider initialized with ${this.totalSlides} slides`);
    }

    showSlide(index) {
        if (index < 0 || index >= this.totalSlides) return;

        // Update slides
        this.slides.forEach((slide, i) => {
            slide.classList.remove('active', 'prev');
            if (i === index) {
                slide.classList.add('active');
            } else if (i < index) {
                slide.classList.add('prev');
            }
        });

        // Update dots
        this.dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
        });

        this.currentSlide = index;
    }

    nextSlide() {
        const next = (this.currentSlide + 1) % this.totalSlides;
        this.showSlide(next);
    }

    previousSlide() {
        const prev = (this.currentSlide - 1 + this.totalSlides) % this.totalSlides;
        this.showSlide(prev);
    }

    goToSlide(index) {
        this.showSlide(index);
        this.resetAutoPlay();
    }

    startAutoPlay() {
        this.autoPlayInterval = setInterval(() => {
            this.nextSlide();
        }, 5000);
    }

    stopAutoPlay() {
        if (this.autoPlayInterval) {
            clearInterval(this.autoPlayInterval);
            this.autoPlayInterval = null;
        }
    }

    resetAutoPlay() {
        this.stopAutoPlay();
        //this.startAutoPlay();
    }

    destroy() {
        this.stopAutoPlay();
    }
}

// Global slider instance
let homeSlider = null;

// Global functions for HTML onclick handlers
function nextSlide() {
    if (homeSlider) {
        homeSlider.nextSlide();
        homeSlider.resetAutoPlay();
    }
}

function previousSlide() {
    if (homeSlider) {
        homeSlider.previousSlide();
        homeSlider.resetAutoPlay();
    }
}

function goToSlide(index) {
    if (homeSlider) {
        homeSlider.goToSlide(index);
    }
}

// Initialize slider when script loads
document.addEventListener('DOMContentLoaded', function() {
    homeSlider = new HomeSlider();
});

// Make functions globally available
window.nextSlide = nextSlide;
window.previousSlide = previousSlide;
window.goToSlide = goToSlide;

console.log('✅ Home slider script loaded');