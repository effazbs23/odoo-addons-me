import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { ProductComparison } from '@website_sale_comparison/interactions/product_comparison';

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

function kingdomSwiperCanLoop(slideCount, maxSlidesPerView) {
    const max = Math.max(1, Math.ceil(Number(maxSlidesPerView) || 1));
    return slideCount > max;
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
        'section.s_brands[data-snippet]',
        'section.s_manufacturers[data-snippet]',
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
     * True while Website Builder is editing this page (iframe or parent).
     * Live RPC must not replace markup in the editor — widgets only.
     */
    _isWebsiteEditorContext() {
        if (typeof document === 'undefined') {
            return false;
        }
        if (document.body.classList.contains('editor_enable')) {
            return true;
        }
        if (document.getElementById('oe_snippets')) {
            return true;
        }
        if (this.el.closest('.o_editable, #wrapwrap.o_editable, #wrap.o_editable')) {
            return true;
        }
        try {
            if (window.parent && window.parent !== window) {
                const parentDoc = window.parent.document;
                if (
                    parentDoc.body.classList.contains('editor_enable')
                    || parentDoc.body.classList.contains('o_builder_open')
                    || parentDoc.querySelector('.o_website_preview, #oe_snippets')
                ) {
                    return true;
                }
            }
        } catch (_err) {
            // Cross-origin parent — treat as public.
        }
        return false;
    }

    /**
     * Prefer `.k-live-body` so section headings stay intact on public refresh;
     * fall back to `.k-container` for older saved markup.
     */
    _getLiveReplaceTarget(sectionEl, preferLiveBody = true) {
        if (!sectionEl) {
            return null;
        }
        if (preferLiveBody) {
            const liveBody = sectionEl.querySelector('.k-live-body');
            if (liveBody) {
                return liveBody;
            }
        }
        return sectionEl.querySelector('.k-container');
    }

    /**
     * Live refresh swaps product cards inside js_sale snippets but keeps the
     * section-level ProductComparison interaction. Re-bind compare click handlers
     * on the fresh .o_add_compare buttons (wishlist/cart bind per button).
     */
    _rebindProductComparisons() {
        const service = this.services['public.interactions'];
        if (!service?.interactions) {
            return;
        }
        const section = this.el;
        for (const colibri of service.interactions) {
            if (colibri.el !== section || colibri.isDestroyed || !colibri.hasStarted) {
                continue;
            }
            if (colibri.interaction?.constructor !== ProductComparison) {
                continue;
            }
            colibri.updateContent();
        }
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
        // Do not await snippet RPCs before first paint — that made every page with
        // Kingdom carousels feel sluggish. Refresh after mount instead.
    }

    start() {
        const snippetKey = this._getSnippetKey();
        if (!snippetKey) {
            return;
        }
        if (this._isWebsiteEditorContext()) {
            window.requestAnimationFrame(() => {
                this._initSnippetWidgets(snippetKey);
                this.el.dispatchEvent(new CustomEvent('kingdom-live-refreshed'));
            });
            return;
        }
        // Refresh first, then bind Swiper to the final DOM (arrows break if we
        // init on SSR nodes and then replace the container).
        this._refreshLiveSnippet(snippetKey);
    }

    async _refreshLiveSnippet(snippetKey) {
        let refreshed = false;
        try {
            const html = await this.waitFor(
                rpc('/theme_kingdom/snippet/render', { snippet_key: snippetKey })
            );
            if (html && !this._isWebsiteEditorContext()) {
                const temp = document.createElement('div');
                temp.innerHTML = html;
                const freshSection = temp.querySelector('[data-kingdom-live-snippet], section[data-snippet]');
                const useLiveBody = Boolean(this.el.querySelector('.k-live-body'));
                const liveTarget = this._getLiveReplaceTarget(this.el, useLiveBody);
                const freshTarget = this._getLiveReplaceTarget(freshSection, useLiveBody);
                if (liveTarget && freshTarget) {
                    this._stripViewBranding(freshTarget);
                    if (freshSection) {
                        if (freshSection.classList.contains('d-none') && !this.el.classList.contains('d-none')) {
                            this.el.classList.add('d-none');
                        } else if (!freshSection.classList.contains('d-none')) {
                            this.el.classList.remove('d-none');
                        }
                    }
                    this.services['public.interactions'].stopInteractions(liveTarget);
                    liveTarget.replaceWith(freshTarget);
                    await this.waitFor(
                        this.services['public.interactions'].startInteractions(this.el)
                    );
                    this._rebindProductComparisons();
                    refreshed = true;
                }
            }
        } catch (_error) {
            // Keep SSR content if refresh fails.
        }
        this._initSnippetWidgets(snippetKey);
        this.el.dispatchEvent(new CustomEvent('kingdom-live-refreshed'));
        return refreshed;
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
        } else if (snippetKey === 's_brands' || snippetKey === 's_manufacturers') {
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
        const inEditor = this._isWebsiteEditorContext();
        new Swiper(swiperEl, {
            slidesPerView: 'auto',
            observer: !inEditor,
            observeParents: !inEditor,
            lazy: true,
            loop: !inEditor && slideCount > 3,
            centeredSlides: false,
            initialSlide: 0,
            autoplay: inEditor
                ? false
                : {
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
                const swiperEl = this.el.querySelector('.featured-swiper, .bestsale-swiper');
                if (swiperEl && swiperEl.swiper) {
                    return;
                }
            }
            if (typeof Swiper === 'undefined') {
                window.setTimeout(run, 50);
                return;
            }
            const swiperEl = this.el.querySelector('.featured-swiper, .bestsale-swiper');
            if (!swiperEl || !swiperEl.querySelector('.swiper-slide')) {
                return;
            }
            if (swiperEl.swiper) {
                swiperEl.swiper.destroy(true, true);
            }
            const nav = this.el.querySelector('.featured-products-nav');
            const inEditor = this._isWebsiteEditorContext();
            new Swiper(
                swiperEl,
                Object.assign({}, PRODUCT_ROW_SWIPER_OPTS, {
                    observer: !inEditor,
                    observeParents: !inEditor,
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
        const roots = [];
        if (this.el.matches('.product-carousel-section')) {
            roots.push(this.el);
        }
        this.el.querySelectorAll('.product-carousel-section').forEach((root) => {
            if (!roots.includes(root)) {
                roots.push(root);
            }
        });
        roots.forEach((root) => {
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
        const swiperEl = this.el.querySelector('.brand-swiper, .manufacturer-swiper');
        const prevEl = this.el.querySelector('.brand-carousel-arrow.swiper-button-prev, .manufacturer-carousel-arrow.swiper-button-prev');
        const nextEl = this.el.querySelector('.brand-carousel-arrow.swiper-button-next, .manufacturer-carousel-arrow.swiper-button-next');
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
        const inEditor = this._isWebsiteEditorContext();
        // Fixed slidesPerView keeps logo tiles grid-sized; only gate loop.
        const config = {
            loop: !inEditor && kingdomSwiperCanLoop(slideCount, 8),
            speed: 450,
            spaceBetween: 15,
            slidesPerView: 3,
            watchOverflow: true,
            observer: !inEditor,
            observeParents: !inEditor,
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
