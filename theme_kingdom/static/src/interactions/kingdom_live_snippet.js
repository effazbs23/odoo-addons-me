import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

const PRODUCT_ROW_SWIPER_OPTS = {
    spaceBetween: 14,
    slidesPerView: 2,
    breakpoints: {
        576: { slidesPerView: 2 },
        768: { slidesPerView: 3 },
        992: { slidesPerView: 4 },
        1200: { slidesPerView: 5 },
        1400: { slidesPerView: 6 },
    },
};

function padCountdown(n) {
    return String(n).padStart(2, '0');
}

function parseDealEndMs(root) {
    const msAttr = root.getAttribute('data-deal-end-ms');
    if (msAttr) {
        const parsed = parseInt(msAttr, 10);
        if (!Number.isNaN(parsed) && parsed > 0) {
            // BuilderDateTimePicker stores unix seconds; deals use epoch ms.
            return parsed < 1e12 ? parsed * 1000 : parsed;
        }
    }
    const iso = root.getAttribute('data-deal-countdown') || '';
    if (iso) {
        const fromIso = Date.parse(iso.replace(' ', 'T'));
        if (!Number.isNaN(fromIso)) {
            return fromIso;
        }
    }
    return 0;
}

export class KingdomLiveSnippet extends Interaction {
    static selector = [
        '[data-kingdom-live-snippet]',
        'section.s_featured_products[data-snippet]',
        'section.s_bestsale_products[data-snippet]',
        'section.s_product_carousel[data-snippet]',
        'section.product-carousel-section[data-snippet]',
        '.product-carousel-section[data-snippet="s_product_carousel"]',
        '.product-carousel-section[data-snippet="theme_kingdom.s_product_carousel"]',
        'section.s_category_dual_carousels[data-snippet]',
        'section.category-dual-section[data-snippet]',
        'section.s_category_slider[data-snippet]',
        'section.dealoftheday-wrapper[data-snippet]',
        'section.s_manufacturers[data-snippet]',
        'section.s_dynamic_product_tabs[data-snippet]',
        'section.k-dyn-tabs[data-snippet]',
        'section.s_coming_soon[data-snippet]',
    ].join(', ');

    _dealCountdownInterval = null;

    _getSnippetKey() {
        if (this.el.dataset.kingdomLiveSnippet) {
            return this.el.dataset.kingdomLiveSnippet;
        }
        const dataSnippet = this.el.dataset.snippet || '';
        if (dataSnippet.startsWith('theme_kingdom.')) {
            return dataSnippet.slice('theme_kingdom.'.length);
        }
        return dataSnippet;
    }

    /**
     * Live refresh must not run in Website Builder. `editor_enable` is added
     * late (onMounted), so also detect the website preview iframe early —
     * otherwise branded QWeb HTML can be injected and then saved into #wrap,
     * which disables all Blocks.
     */
    _isWebsiteEditorContext() {
        if (document.body.classList.contains('editor_enable')) {
            return true;
        }
        const params = new URLSearchParams(window.location.search);
        if (params.has('enable_editor') || params.has('edit_translations')) {
            return true;
        }
        try {
            if (window.parent !== window) {
                const parentDoc = window.parent.document;
                if (
                    parentDoc &&
                    parentDoc.querySelector(
                        '.o_website_preview, .o_website_fullscreen, .o-snippets-menu'
                    )
                ) {
                    return true;
                }
            }
        } catch {
            // Cross-origin parent: if framed, skip live DOM mutation.
            if (window.frameElement || window.parent !== window) {
                return true;
            }
        }
        return false;
    }

    _stripViewBranding(rootEl) {
        if (!rootEl) {
            return;
        }
        const attrs = [
            'data-oe-model',
            'data-oe-id',
            'data-oe-field',
            'data-oe-xpath',
            'data-oe-source-id',
        ];
        for (const el of [rootEl, ...rootEl.querySelectorAll('*')]) {
            if (el.getAttribute('data-oe-model') !== 'ir.ui.view') {
                continue;
            }
            for (const attr of attrs) {
                el.removeAttribute(attr);
            }
        }
    }

    async willStart() {
        if (this._isWebsiteEditorContext()) {
            return;
        }
        const snippetKey = this._getSnippetKey();
        if (!snippetKey) {
            return;
        }
        const html = await this.waitFor(
            rpc('/theme_kingdom/snippet/render', { snippet_key: snippetKey })
        );
        if (!html) {
            return;
        }
        // Editor may have started while the RPC was in flight.
        if (this._isWebsiteEditorContext()) {
            return;
        }
        const container = this.el.querySelector('.k-container');
        if (!container) {
            return;
        }
        const temp = document.createElement('div');
        temp.innerHTML = html;
        const freshSection = temp.querySelector('[data-kingdom-live-snippet], section[data-snippet]');
        const freshContainer = freshSection && freshSection.querySelector('.k-container');
        if (!freshContainer) {
            return;
        }
        this._stripViewBranding(freshContainer);
        if (freshSection.classList.contains('d-none') && !this.el.classList.contains('d-none')) {
            this.el.classList.add('d-none');
        } else if (!freshSection.classList.contains('d-none')) {
            this.el.classList.remove('d-none');
        }
        this.services['public.interactions'].stopInteractions(container);
        container.replaceWith(freshContainer);
        await this.waitFor(
            this.services['public.interactions'].startInteractions(this.el)
        );
    }

    start() {
        const snippetKey = this._getSnippetKey();
        if (!snippetKey) {
            return;
        }
        window.requestAnimationFrame(() => {
            this._initSnippetWidgets(snippetKey);
        });
    }

    destroy() {
        if (this._dealCountdownInterval) {
            window.clearInterval(this._dealCountdownInterval);
            this._dealCountdownInterval = null;
        }
        super.destroy();
    }

    _initSnippetWidgets(snippetKey) {
        if (snippetKey === 's_deal_of_the_day') {
            this._initDealSnippet();
        } else if (
            snippetKey === 's_product_carousel'
            || snippetKey === 's_category_dual_carousels'
        ) {
            this._initProductCarousels();
        } else if (snippetKey === 's_category_slider') {
            this._initCategorySwiper();
        } else if (
            snippetKey === 's_featured_products'
            || snippetKey === 's_bestsale_products'
        ) {
            this._initProductSwiper();
        } else if (snippetKey === 's_manufacturers') {
            this._initManufacturerCarousel();
        }
    }

    _initDealCountdown() {
        if (this._dealCountdownInterval) {
            window.clearInterval(this._dealCountdownInterval);
            this._dealCountdownInterval = null;
        }
        const roots = this.el.querySelectorAll(
            '[data-deal-countdown], [data-deal-end-ms], .carousel-countdown, .dealoftheday-counter'
        );
        if (!roots.length) {
            return;
        }
        const tick = () => {
            const now = Date.now();
            roots.forEach((root) => {
                const endMs = parseDealEndMs(root);
                if (!endMs) {
                    return;
                }
                const diff = Math.max(0, endMs - now);
                const totalSeconds = Math.floor(diff / 1000);
                const days = Math.floor(totalSeconds / 86400);
                let s = totalSeconds - days * 86400;
                const hours = Math.floor(s / 3600);
                s -= hours * 3600;
                const mins = Math.floor(s / 60);
                const secs = s - mins * 60;
                for (const [selector, value] of [
                    ['.cd-days', days],
                    ['.cd-hours', hours],
                    ['.cd-mins', mins],
                    ['.cd-secs', secs],
                ]) {
                    const el = root.querySelector(selector);
                    if (el) {
                        el.textContent = padCountdown(value);
                    }
                }
            });
        };
        tick();
        this._dealCountdownInterval = window.setInterval(tick, 1000);
    }

    _initDealSwiper() {
        if (typeof Swiper === 'undefined') {
            return;
        }
        const swiperEl = this.el.querySelector('.deal-swiper');
        if (!swiperEl || !swiperEl.querySelector('.swiper-slide')) {
            return;
        }
        if (swiperEl.swiper) {
            swiperEl.swiper.destroy(true, true);
        }
        const slideCount = swiperEl.querySelectorAll('.swiper-slide').length;
        const nav = this.el.querySelector('.deal-swiper-nav');
        new Swiper(swiperEl, {
            slidesPerView: 'auto',
            observer: true,
            observeParents: true,
            lazy: true,
            loop: slideCount > 1,
            centeredSlides: false,
            initialSlide: 0,
            autoplay: {
                delay: 5000,
                disableOnInteraction: false,
                pauseOnMouseEnter: true,
            },
            pagination: {
                el: swiperEl.querySelector('.swiper-pagination'),
                clickable: true,
            },
            navigation: {
                nextEl: nav && nav.querySelector('.swiper-button-next'),
                prevEl: nav && nav.querySelector('.swiper-button-prev'),
            },
        });
    }

    _initDealSnippet() {
        this._initDealCountdown();
        this._initDealSwiper();
    }

    _initProductSwiper() {
        const run = () => {
            if (typeof window.KingdomInitProductRowSwiper === 'function') {
                window.KingdomInitProductRowSwiper(this.el);
                return;
            }
            if (typeof Swiper === 'undefined') {
                window.setTimeout(run, 50);
                return;
            }
            const swiperEl = this.el.querySelector('.featured-swiper, .bestsale-swiper');
            if (!swiperEl) {
                return;
            }
            if (swiperEl.swiper) {
                swiperEl.swiper.destroy(true, true);
            }
            const nav = this.el.querySelector('.featured-products-nav');
            new Swiper(
                swiperEl,
                Object.assign({}, PRODUCT_ROW_SWIPER_OPTS, {
                    observer: true,
                    observeParents: true,
                    watchOverflow: true,
                    preventClicks: false,
                    preventClicksPropagation: false,
                    navigation: {
                        prevEl: nav && nav.querySelector('.swiper-button-prev'),
                        nextEl: nav && nav.querySelector('.swiper-button-next'),
                    },
                })
            );
        };
        run();
    }

    _initProductCarousels() {
        if (typeof window.KingdomInitProductCarousel !== 'function') {
            return;
        }
        this.el.querySelectorAll('.product-carousel-section').forEach((root) => {
            window.KingdomInitProductCarousel(root);
        });
    }

    _initProductTabs() {
        if (typeof window.KingdomInitProductTab !== 'function') {
            return;
        }
        this.el.querySelectorAll('.product-tab-container').forEach((root) => {
            window.KingdomInitProductTab(root);
        });
    }

    _initCategorySwiper() {
        if (typeof window.KingdomInitCategorySwiper !== 'function') {
            return;
        }
        window.KingdomInitCategorySwiper(this.el);
    }

    _initManufacturerCarousel() {
        if (typeof Swiper === 'undefined' || this.el.classList.contains('d-none')) {
            return;
        }
        const carousel = this.el.querySelector('.carousel-container');
        const swiperEl = this.el.querySelector('.manufacturer-swiper');
        const prevEl = this.el.querySelector('.manufacturer-carousel-arrow.swiper-button-prev');
        const nextEl = this.el.querySelector('.manufacturer-carousel-arrow.swiper-button-next');
        if (!swiperEl || !carousel || !prevEl || !nextEl) {
            return;
        }
        if (!swiperEl.querySelector('.swiper-slide')) {
            return;
        }
        if (swiperEl.swiper) {
            swiperEl.swiper.destroy(true, true);
        }
        const slideCount = swiperEl.querySelectorAll('.swiper-slide').length;
        const config = {
            loop: slideCount > 3,
            speed: 450,
            spaceBetween: 15,
            slidesPerView: 3,
            watchOverflow: true,
            observer: true,
            observeParents: true,
            navigation: {
                prevEl,
                nextEl,
            },
            breakpoints: {
                576: { slidesPerView: 4, spaceBetween: 15 },
                992: { slidesPerView: 6, spaceBetween: 15 },
                1600: { slidesPerView: 8, spaceBetween: 15 },
            },
        };
        try {
            new Swiper(swiperEl, config);
        } catch {
            new Swiper(swiperEl, { ...config, loop: false });
        }
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.kingdom_live_snippet', KingdomLiveSnippet);
