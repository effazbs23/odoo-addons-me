document.addEventListener('DOMContentLoaded', function () {
    const tabInputs = document.querySelectorAll('input.category-tab');
    const categoryProducts = document.querySelectorAll('.category-products');
    const categoryImageEl = document.getElementById('category-image');
    const prevButton = document.getElementById('prev-slide');
    const nextButton = document.getElementById('next-slide');
    const slideInfo = document.getElementById('slide-info');

    if (!tabInputs.length || !categoryProducts.length) {
        return;
    }

    function getActiveSwiper() {
        for (const div of categoryProducts) {
            if (div.style.display !== 'none' && div.swiper) {
                return div.swiper;
            }
        }
        return null;
    }

    function updateSlideInfo(swiperInstance) {
        if (!slideInfo || !swiperInstance) {
            return;
        }
        const total = swiperInstance.slides.length || 1;
        const current = (swiperInstance.activeIndex || 0) + 1;
        slideInfo.textContent = `Slide ${current} of ${total}`;
    }

    function bindSlideChange(swiperInstance) {
        if (!swiperInstance || swiperInstance.__slideInfoBound) {
            return;
        }
        swiperInstance.on('slideChange', function () {
            updateSlideInfo(swiperInstance);
        });
        swiperInstance.__slideInfoBound = true;
    }

    function updateCategoryImage(categoryId) {
        if (!categoryImageEl) {
            return;
        }
        const activeInput = document.querySelector(`input.category-tab[data-category="${categoryId}"]`);
        const src = activeInput ? (activeInput.getAttribute('data-image-src') || '') : '';
        const alt = activeInput ? (activeInput.getAttribute('data-image-alt') || 'Category Image') : 'Category Image';
        if (src) {
            categoryImageEl.src = src;
            categoryImageEl.alt = alt;
        }
    }

    function activateCategory(categoryId) {
        updateCategoryImage(categoryId);

        categoryProducts.forEach(function (div) {
            const isActive = div.dataset.category === categoryId;
            div.style.display = isActive ? 'block' : 'none';
            if (isActive && div.swiper) {
                div.swiper.update();
                div.swiper.slideTo(0, 0);
                bindSlideChange(div.swiper);
                updateSlideInfo(div.swiper);
            }
        });
    }

    tabInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            if (this.checked) {
                activateCategory(this.dataset.category);
            }
        });
    });

    const firstChecked = document.querySelector('input.category-tab:checked');
    if (firstChecked) {
        activateCategory(firstChecked.dataset.category);
    }

    if (prevButton) {
        prevButton.addEventListener('click', function () {
            const swiperInstance = getActiveSwiper();
            if (swiperInstance) {
                swiperInstance.slidePrev();
                updateSlideInfo(swiperInstance);
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', function () {
            const swiperInstance = getActiveSwiper();
            if (swiperInstance) {
                swiperInstance.slideNext();
                updateSlideInfo(swiperInstance);
            }
        });
    }
});
