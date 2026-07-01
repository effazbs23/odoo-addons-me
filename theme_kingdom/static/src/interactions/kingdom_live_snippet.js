import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';

const PRODUCT_ROW_SWIPER_OPTS = {
    spaceBetween: 14,
    slidesPerView: 2,
    pagination: { clickable: true },
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
            return parsed;
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
        'section.s_category_dual_carousels[data-snippet]',
        'section.s_category_slider[data-snippet]',
        'section.dealoftheday-wrapper[data-snippet]',
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

    async willStart() {
        if (document.body.classList.contains('editor_enable')) {
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
        if (freshSection.classList.contains('d-none') && !this.el.classList.contains('d-none')) {
            this.el.classList.add('d-none');
        } else if (!freshSection.classList.contains('d-none')) {
            this.el.classList.remove('d-none');
        }
        this.services['public.interactions'].stopInteractions(container);
        container.replaceWith(freshContainer);
        if (snippetKey === 's_deal_of_the_day') {
            this._initDealSnippet();
        } else if (
            snippetKey === 's_product_carousel'
            || snippetKey === 's_category_dual_carousels'
        ) {
            this._initProductCarousels();
        } else if (snippetKey === 's_category_slider') {
            this._initCategorySwiper();
        } else {
            this._initProductSwiper();
        }
        await this.waitFor(
            this.services['public.interactions'].startInteractions(this.el)
        );
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
        if (typeof Swiper === 'undefined') {
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
                watchOverflow: true,
                preventClicks: false,
                preventClicksPropagation: false,
                navigation: {
                    prevEl: nav && nav.querySelector('.swiper-button-prev'),
                    nextEl: nav && nav.querySelector('.swiper-button-next'),
                },
            })
        );
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
}

registry
    .category('public.interactions')
    .add('theme_kingdom.kingdom_live_snippet', KingdomLiveSnippet);
