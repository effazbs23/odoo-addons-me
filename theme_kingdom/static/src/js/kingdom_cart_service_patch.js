/** @odoo-module **/

import { markup } from '@odoo/owl';
import { browser } from '@web/core/browser/browser';
import { patch } from '@web/core/utils/patch';
import { setElementContent } from '@web/core/utils/html';
import { CartService } from '@website_sale/js/cart_service';
import websiteSaleUtils from '@website_sale/js/website_sale_utils';

/**
 * Kingdom header uses #topcartlink instead of the default Odoo navbar cart.
 * Odoo's CartService assumes `li.o_wsale_my_cart` exists globally; guard all
 * cart icon updates so missing markup never crashes add-to-cart flows.
 */
function getKingdomCartIconElement() {
    return (
        document.querySelector('li.o_wsale_my_cart') ||
        document.querySelector('#topcartlink') ||
        document.querySelector('.my_cart_quantity')?.closest('li')
    );
}

function notifyKingdomFlyoutCart(open = false) {
    document.dispatchEvent(
        new CustomEvent('kingdom-flyout-cart-refresh', { detail: { open } })
    );
}

function updateKingdomCartQuantityBadges(cartQuantity) {
    browser.sessionStorage.setItem('website_sale_cart_quantity', cartQuantity);
    const cartIconElement = getKingdomCartIconElement();
    const cartQuantityElements = document.querySelectorAll('.my_cart_quantity');

    if (!cartQuantityElements.length) {
        cartIconElement?.classList.toggle('d-none', cartQuantity === 0);
        return;
    }

    for (const cartQuantityElement of cartQuantityElements) {
        if (cartQuantity === 0) {
            cartQuantityElement.classList.add('d-none');
            continue;
        }
        const parentCartIcon =
            cartQuantityElement.closest('li.o_wsale_my_cart') ||
            cartQuantityElement.closest('#topcartlink') ||
            cartIconElement;
        parentCartIcon?.classList.remove('d-none');
        cartQuantityElement.classList.remove('d-none');
        cartQuantityElement.classList.add('o_mycart_zoom_animation');
        setTimeout(() => {
            cartQuantityElement.textContent = cartQuantity;
            cartQuantityElement.classList.remove('o_mycart_zoom_animation');
        }, 300);
    }
}

patch(CartService.prototype, {
    _updateCartIcon(cartQuantity) {
        updateKingdomCartQuantityBadges(cartQuantity);
        if (cartQuantity > 0) {
            notifyKingdomFlyoutCart(true);
        }
    },

    /**
     * Kingdom uses the sidebar flyout cart instead of Odoo's add-to-cart toast.
     */
    _showCartNotification(props, options = {}) {
        if (props.warning) {
            return super._showCartNotification({ warning: props.warning }, options);
        }
    },
});

patch(websiteSaleUtils, {
    updateCartNavBar(data) {
        updateKingdomCartQuantityBadges(data.cart_quantity);

        $(".js_cart_lines").first().before(data['website_sale.cart_lines']).end().remove();

        if (data['website_sale.shorter_cart_summary']) {
            const shorterCartSummaryEl = document.querySelector('.o_wsale_shorter_cart_summary');
            if (shorterCartSummaryEl) {
                setElementContent(shorterCartSummaryEl, markup(data['website_sale.shorter_cart_summary']));
            }
        }
        if (data['website_sale.total']) {
            document.querySelectorAll('div.o_cart_total').forEach(
                (div) => { div.innerHTML = data['website_sale.total']; }
            );
        }

        document.querySelector('.oe_cart')?.classList.toggle('col-lg-7', !!data.cart_quantity);

        const mainButton = document.querySelector("a[name='website_sale_main_button']");
        if (data.cart_ready) {
            mainButton?.classList.remove('disabled');
        } else {
            mainButton?.classList.add('disabled');
        }
    },
});
