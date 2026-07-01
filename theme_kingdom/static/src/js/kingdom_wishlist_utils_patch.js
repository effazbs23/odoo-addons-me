/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import wishlistUtils from '@website_sale_wishlist/js/website_sale_wishlist_utils';

function isKingdomWishlistBadge(el) {
    return Boolean(el.closest('.ico-wishlist, .mobile-navigation-drawer'));
}

/**
 * Kingdom header uses "Wishlist (N)" inside `.ico-wishlist` instead of Odoo's
 * navbar badge. Keep counts in sync with sessionStorage and always show zero.
 */
patch(wishlistUtils, {
    updateWishlistNavBar() {
        const wishlistProductIds = wishlistUtils.getWishlistProductIds();
        const count = wishlistProductIds.length;

        document.querySelectorAll('.o_wsale_my_wish').forEach((button) => {
            if (button.classList.contains('o_wsale_my_wish_hide_empty')) {
                button.classList.toggle('d-none', !count);
            }
            const qtyEl = button.querySelector('.my_wish_quantity');
            if (qtyEl) {
                qtyEl.textContent = String(count);
            }
        });

        document.querySelectorAll('.my_wish_quantity').forEach((quantity) => {
            quantity.textContent = String(count);
            if (isKingdomWishlistBadge(quantity)) {
                quantity.classList.remove('d-none');
                return;
            }
            quantity.classList.toggle('d-none', !count);
        });
    },
});
