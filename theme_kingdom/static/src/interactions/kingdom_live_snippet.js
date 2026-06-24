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

export class KingdomLiveSnippet extends Interaction {
    static selector = [
        '[data-kingdom-live-snippet]',
        'section.s_featured_products[data-snippet]',
        'section.s_bestsale_products[data-snippet]',
    ].join(', ');

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
        const freshContainer = temp.querySelector('.k-container');
        if (!freshContainer) {
            return;
        }
        this.services['public.interactions'].stopInteractions(container);
        container.replaceWith(freshContainer);
        this._initProductSwiper();
        await this.waitFor(
            this.services['public.interactions'].startInteractions(this.el)
        );
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
}

registry
    .category('public.interactions')
    .add('theme_kingdom.kingdom_live_snippet', KingdomLiveSnippet);
