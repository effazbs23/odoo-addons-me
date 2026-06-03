function initAllSwipers() {
    if (typeof Swiper === 'undefined') {
        setTimeout(initAllSwipers, 50);
        return;
    }

    function initShopCategorySwipers() {
        document.querySelectorAll('.shop-category-swiper').forEach((swiperEl) => {
            if (swiperEl.swiper) {
                return;
            }

            const sectionEl = swiperEl.closest('.categories, .category-carousel') || swiperEl.parentElement;
            const prevEl = sectionEl ? sectionEl.querySelector('.shop-category-prev') : null;
            const nextEl = sectionEl ? sectionEl.querySelector('.shop-category-next') : null;

            const config = {
                slidesPerView: 2,
                spaceBetween: 12,
                loop: false,
                watchOverflow: true,
                observer: true,
                observeParents: true,
                breakpoints: {
                    576: { slidesPerView: 2, spaceBetween: 14 },
                    768: { slidesPerView: 3, spaceBetween: 16 },
                    992: { slidesPerView: 4, spaceBetween: 18 },
                    1200: { slidesPerView: 5, spaceBetween: 20 },
                },
            };

            if (prevEl && nextEl) {
                config.navigation = {
                    prevEl,
                    nextEl,
                };
            }

            new Swiper(swiperEl, config);
        });
    }

    function initIfExists(swiperSelector, prevSelector, nextSelector, options) {
        const swiperEl = document.querySelector(swiperSelector);
        if (!swiperEl || swiperEl.swiper) {
            return;
        }
        const config = Object.assign(
            {
                slidesPerView: 'auto',
                spaceBetween: 0,
                loop: true,
            },
            options || {}
        );
        if (prevSelector && nextSelector && document.querySelector(prevSelector) && document.querySelector(nextSelector)) {
            config.navigation = {
                prevEl: prevSelector,
                nextEl: nextSelector,
            };
        }
        new Swiper(swiperEl, config);
    }

    initShopCategorySwipers();
    initIfExists('#swiper-12345', '#prev-12345', '#next-12345');
    initIfExists('#swiper-dil', '#prev-dil', '#next-dil');
    initIfExists('#swiper-best', '#prev-best', '#next-best');
    initIfExists('#swiper-featured', '#prev-featured', '#next-featured');
    initIfExists('#swiper-brands', '#prev-brands', '#next-brands');
    initIfExists('#swiper-new-arrival', '#prev-new-arrival', '#next-new-arrival', {
        slidesPerView: 2,
        spaceBetween: 16,
        loop: true,
        watchOverflow: false,
        observer: true,
        observeParents: true,
        breakpoints: {
            576: { slidesPerView: 2 },
            768: { slidesPerView: 3 },
            992: { slidesPerView: 4 },
            1200: { slidesPerView: 5 },
        },
    });
}

function normalizeBootstrapCarouselIndicators() {
    document.querySelectorAll('.carousel').forEach((carouselEl) => {
        const itemEls = carouselEl.querySelectorAll('.carousel-inner .carousel-item');
        const indicatorEls = carouselEl.querySelectorAll('.carousel-indicators button, .carousel-indicators li');
        if (!indicatorEls.length) {
            return;
        }
        if (!itemEls.length) {
            indicatorEls.forEach((el) => el.classList.add('d-none'));
            return;
        }
        const maxIndex = itemEls.length - 1;
        indicatorEls.forEach((indicatorEl, idx) => {
            indicatorEl.dataset.bsSlideTo = String(Math.min(idx, maxIndex));
        });
    });
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.category-products').forEach((el) => {
        if (el.swiper) {
            return;
        }
        new Swiper(el, {
            slidesPerView: 4,
            spaceBetween: 30,
            loop: false,
            breakpoints: {
                320: {slidesPerView: 2},
                768: {slidesPerView: 3},
                1200: {slidesPerView: 4}
            }
        });
    });

});

document.addEventListener('DOMContentLoaded', initAllSwipers);
window.addEventListener('load', initAllSwipers);
document.addEventListener('DOMContentLoaded', normalizeBootstrapCarouselIndicators);
window.addEventListener('load', normalizeBootstrapCarouselIndicators);