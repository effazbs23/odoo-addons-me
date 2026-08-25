import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';

export class FeaturedProductCard extends Interaction {
    static selector = '.featured-product-card:not(.featured-product-card--soldout)';

    dynamicContent = {
        _root: { 't-on-click': this.onCardClick },
    };

    start() {
        const buyBtn = this.el.querySelector('.s_add_to_cart_btn');
        const activeSwatch = this.el.querySelector(
            '.featured-product-swatch.is-active[data-variant-id]'
        );
        if (buyBtn && activeSwatch) {
            buyBtn.dataset.productVariantId = activeSwatch.dataset.variantId;
        }
    }

    onCardClick(ev) {
        if (ev.target.closest('.kingdom-product-actions, .kingdom-quickview-btn, .o_add_wishlist, .o_add_compare, .s_add_to_cart_btn')) {
            return;
        }
        const swatch = ev.target.closest('.featured-product-swatch[data-ptav-id]');
        if (!swatch) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();

        const card = this.el;
        const buyBtn = card.querySelector('.s_add_to_cart_btn');
        const productTemplateId = parseInt(
            buyBtn?.dataset.productTemplateId || card.dataset.productTemplateId,
            10
        );
        const ptavId = parseInt(swatch.dataset.ptavId, 10);
        if (!productTemplateId || !ptavId) {
            return;
        }

        this._activateSwatch(swatch, card);
        this._updatePreview(card, swatch);
        if (buyBtn && swatch.dataset.variantId) {
            buyBtn.dataset.productVariantId = swatch.dataset.variantId;
        }

        this.services['cart'].add(
            {
                productTemplateId,
                ptavs: [ptavId],
                isCombo: buyBtn?.dataset.productType === 'combo',
            },
            {
                showQuantity: false,
            }
        );
    }

    _activateSwatch(swatch, card) {
        swatch.classList.add('is-active');
        swatch.setAttribute('aria-pressed', 'true');
        card.querySelectorAll('.featured-product-swatch').forEach((item) => {
            if (item !== swatch) {
                item.classList.remove('is-active');
                item.setAttribute('aria-pressed', 'false');
            }
        });
    }

    _updatePreview(card, swatch) {
        const variantImage = swatch.dataset.variantImage;
        const variantUrl = swatch.dataset.variantUrl;
        const pictureLink = card.querySelector('.featured-product-picture');
        const titleLink = card.querySelector('.featured-product-body h3 a');
        const img = card.querySelector('.featured-product-picture img');

        if (variantImage && img) {
            img.src = variantImage;
        }
        if (variantUrl) {
            if (pictureLink) {
                pictureLink.href = variantUrl;
            }
            if (titleLink) {
                titleLink.href = variantUrl;
            }
        }
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.featured_product_card', FeaturedProductCard);
