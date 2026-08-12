/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';

/**
 * Kingdom premium product detail page: bulk tier qty, share link,
 * promo copy/details, and utility wishlist/compare delegates.
 */
export class KingdomProductDetail extends Interaction {
    static selector = '.kingdom-product-page';

    dynamicContent = {
        '.kingdom-pdp-bulk__tier': {
            't-on-click': this.onBulkTierClick,
        },
        '.js_kingdom_pdp_share': {
            't-on-click.prevent': this.onShareClick,
        },
        '.js_kingdom_pdp_wishlist': {
            't-on-click.prevent': this.onWishlistClick,
        },
        '.js_kingdom_pdp_compare': {
            't-on-click.prevent': this.onCompareClick,
        },
        '.js_kingdom_pdp_copy_code': {
            't-on-click.prevent': this.onCopyCodeClick,
        },
        '.js_kingdom_pdp_offer_toggle': {
            't-on-click.prevent': this.onOfferToggleClick,
        },
    };

    onBulkTierClick(ev) {
        const tier = ev.currentTarget;
        const minQty = tier.dataset.minQty;
        if (!minQty) {
            return;
        }
        this.el.querySelectorAll('.kingdom-pdp-bulk__tier').forEach((node) => {
            node.classList.toggle('is-active', node === tier);
        });
        const qtyInput = this.el.querySelector('input[name="add_qty"]');
        if (qtyInput) {
            qtyInput.value = minQty;
            qtyInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    onShareClick() {
        const url = window.location.href;
        if (navigator.share) {
            navigator.share({ title: document.title, url }).catch(() => {});
            return;
        }
        this._copyText(url, _t('Link copied to clipboard.'));
    }

    onCopyCodeClick(ev) {
        const code = ev.currentTarget.dataset.promoCode;
        if (!code) {
            return;
        }
        this._copyText(code, _t('Promo code copied: %s', code));
    }

    onOfferToggleClick(ev) {
        const btn = ev.currentTarget;
        const item = btn.closest('.kingdom-pdp-offers__item');
        const panel = item?.querySelector('.kingdom-pdp-offers__panel');
        if (!panel) {
            return;
        }
        const open = panel.classList.toggle('d-none') === false;
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        btn.classList.toggle('is-open', open);
        const label = btn.querySelector('span');
        if (label) {
            label.textContent = open ? _t('Hide <') : _t('Details >');
        }
    }

    onWishlistClick() {
        const target = this.el.querySelector(
            '#product_option_block .o_add_wishlist_dyn, #product_option_block [data-action="o_wishlist"]'
        );
        if (!target) {
            return;
        }
        target.style.pointerEvents = 'auto';
        target.click();
        target.style.pointerEvents = '';
    }

    onCompareClick() {
        const target = this.el.querySelector(
            '#product_option_block .o_add_compare_dyn, #product_option_block [data-action="o_comparelist"]'
        );
        if (!target) {
            return;
        }
        target.style.pointerEvents = 'auto';
        target.click();
        target.style.pointerEvents = '';
    }

    _copyText(text, successMessage) {
        const notify = () => {
            this.services.notification?.add(successMessage, { type: 'success' });
        };
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(notify).catch(() => {
                window.prompt(_t('Copy this code'), text);
            });
            return;
        }
        window.prompt(_t('Copy this code'), text);
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.product_detail', KingdomProductDetail);
