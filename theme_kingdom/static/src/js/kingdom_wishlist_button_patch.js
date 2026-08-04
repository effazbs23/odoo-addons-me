/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';
import {
    AddProductToWishlistButton,
} from '@website_sale_wishlist/interactions/add_product_to_wishlist_button';
import wishlistUtils from '@website_sale_wishlist/js/website_sale_wishlist_utils';

/**
 * Mark wishlist button(s) as active after add.
 * No toast — Odoo only updates the header count; the button state is the UX cue.
 */
function markWishlistButtonsActive(productId, sourceEl) {
    const selector = productId
        ? `.o_add_wishlist[data-product-product-id="${productId}"], .o_add_wishlist_dyn[data-product-product-id="${productId}"]`
        : null;
    const buttons = selector
        ? document.querySelectorAll(selector)
        : (sourceEl ? [sourceEl] : []);

    buttons.forEach((btn) => {
        wishlistUtils.updateDisabled(btn, true);
        btn.classList.add('o_in_wishlist');
        btn.setAttribute('title', _t('In your wishlist'));
        btn.setAttribute('aria-label', _t('In your wishlist'));
        btn.setAttribute('aria-pressed', 'true');
        const iconEl = btn.querySelector('.fa');
        if (iconEl) {
            iconEl.classList.remove('fa-heart-o');
            iconEl.classList.add('fa-heart');
        }
    });
}

patch(AddProductToWishlistButton.prototype, {
    /**
     * @param {Event} ev
     */
    async addProduct(ev) {
        const el = ev.currentTarget;
        const productIdBefore = parseInt(el.dataset.productProductId, 10);
        if (productIdBefore && wishlistUtils.getWishlistProductIds().includes(productIdBefore)) {
            markWishlistButtonsActive(productIdBefore, el);
            return;
        }

        const countBefore = wishlistUtils.getWishlistProductIds().length;
        await this.waitFor(super.addProduct(...arguments));

        const productId = parseInt(el.dataset.productProductId, 10) || productIdBefore;
        if (
            wishlistUtils.getWishlistProductIds().length > countBefore
            || (productId && wishlistUtils.getWishlistProductIds().includes(productId))
        ) {
            markWishlistButtonsActive(productId, el);
        }
    },
});
