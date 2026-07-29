(function () {
    "use strict";

    function getCategoryProducts() {
        return document.querySelectorAll(".category-products");
    }

    function getSlideInfoEl() {
        return document.getElementById("slide-info");
    }

    function updateSlideInfo(swiperInstance) {
        var slideInfo = getSlideInfoEl();
        if (!slideInfo || !swiperInstance) {
            return;
        }
        var total = swiperInstance.slides.length || 1;
        var current = (swiperInstance.activeIndex || 0) + 1;
        slideInfo.textContent = "Slide " + current + " of " + total;
    }

    function bindSlideChange(swiperInstance) {
        if (!swiperInstance || swiperInstance.__slideInfoBound) {
            return;
        }
        swiperInstance.on("slideChange", function () {
            updateSlideInfo(swiperInstance);
        });
        swiperInstance.__slideInfoBound = true;
    }

    function getActiveSwiper() {
        var products = getCategoryProducts();
        for (var i = 0; i < products.length; i++) {
            var div = products[i];
            if (div.style.display !== "none" && div.swiper) {
                return div.swiper;
            }
        }
        return null;
    }

    function updateCategoryImage(categoryId) {
        var categoryImageEl = document.getElementById("category-image");
        if (!categoryImageEl) {
            return;
        }
        var activeInput = document.querySelector('input.category-tab[data-category="' + categoryId + '"]');
        var src = activeInput ? activeInput.getAttribute("data-image-src") || "" : "";
        var alt = activeInput ? activeInput.getAttribute("data-image-alt") || "Category Image" : "Category Image";
        if (src) {
            categoryImageEl.src = src;
            categoryImageEl.alt = alt;
        }
    }

    function activateCategory(categoryId) {
        updateCategoryImage(categoryId);

        getCategoryProducts().forEach(function (div) {
            var isActive = div.dataset.category === categoryId;
            div.style.display = isActive ? "block" : "none";
            if (isActive && div.swiper) {
                div.swiper.update();
                div.swiper.slideTo(0, 0);
                bindSlideChange(div.swiper);
                updateSlideInfo(div.swiper);
            }
        });
    }

    function activateCurrent() {
        var firstChecked = document.querySelector("input.category-tab:checked");
        if (firstChecked) {
            activateCategory(firstChecked.dataset.category);
        }
    }

    function bindOnce() {
        document.querySelectorAll("input.category-tab").forEach(function (input) {
            if (input.dataset.nfTabBound) {
                return;
            }
            input.dataset.nfTabBound = "1";
            input.addEventListener("change", function () {
                if (this.checked) {
                    activateCategory(this.dataset.category);
                }
            });
        });

        var prevButton = document.getElementById("prev-slide");
        if (prevButton && !prevButton.dataset.nfBound) {
            prevButton.dataset.nfBound = "1";
            prevButton.addEventListener("click", function () {
                var swiperInstance = getActiveSwiper();
                if (swiperInstance) {
                    swiperInstance.slidePrev();
                    updateSlideInfo(swiperInstance);
                }
            });
        }

        var nextButton = document.getElementById("next-slide");
        if (nextButton && !nextButton.dataset.nfBound) {
            nextButton.dataset.nfBound = "1";
            nextButton.addEventListener("click", function () {
                var swiperInstance = getActiveSwiper();
                if (swiperInstance) {
                    swiperInstance.slideNext();
                    updateSlideInfo(swiperInstance);
                }
            });
        }
    }

    function init() {
        if (!document.querySelectorAll("input.category-tab").length) {
            return;
        }
        bindOnce();
        activateCurrent();
    }

    // Called by nf-dynamic-snippets.js after the Our Products slider is refreshed.
    window.nfRefreshProductTabs = function () {
        bindOnce();
        activateCurrent();
    };

    document.addEventListener("DOMContentLoaded", init);
})();
