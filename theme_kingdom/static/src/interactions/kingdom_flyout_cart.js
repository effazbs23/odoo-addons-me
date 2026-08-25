/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { browser } from '@web/core/browser/browser';

export class KingdomFlyoutCart extends Interaction {
    static selector = '.js_kingdom_flyout_cart';

    dynamicContent = {
        '.js_kingdom_flyout_close': { 't-on-click.prevent': this.locked(this.onCloseClick) },
    };

    setup() {
        this._onDocumentKeydown = this.onDocumentKeydown.bind(this);
        this._onFlyoutRefresh = this.onFlyoutRefresh.bind(this);
    }

    start() {
        window.__kingdomFlyoutInteractionActive = true;
        this._removeLegacyFlyoutCarts();
        this._moveFlyoutToBody();
        document.addEventListener('keydown', this._onDocumentKeydown);
        document.addEventListener('kingdom-flyout-cart-refresh', this._onFlyoutRefresh);
        return super.start(...arguments);
    }

    destroy() {
        window.__kingdomFlyoutInteractionActive = false;
        document.removeEventListener('keydown', this._onDocumentKeydown);
        document.removeEventListener('kingdom-flyout-cart-refresh', this._onFlyoutRefresh);
        return super.destroy(...arguments);
    }

    _removeLegacyFlyoutCarts() {
        for (const legacyFlyout of document.querySelectorAll(
            '#flyout-cart, .flyout-cart:not(.js_kingdom_flyout_cart)'
        )) {
            legacyFlyout.remove();
        }
    }

    _moveFlyoutToBody() {
        const wrapper = document.getElementById('advance-cart-flyout-cart-wrapper');
        if (wrapper && wrapper.parentElement !== document.body) {
            document.body.appendChild(wrapper);
        }
    }

    onFlyoutRefresh(ev) {
        this.refresh({ open: Boolean(ev.detail?.open) });
    }

    onDocumentKeydown(ev) {
        if (ev.key === 'Escape' && this.isOpen()) {
            this.close();
        }
    }

    onCloseClick(ev) {
        ev.preventDefault();
        this.close();
    }

    isOpen() {
        return document.documentElement.classList.contains('flyout-cart-open')
            || document.body.classList.contains('flyout-cart-open');
    }

    open() {
        return this.refresh({ open: true });
    }

    close() {
        document.documentElement.classList.remove('flyout-cart-open');
        document.body.classList.remove('flyout-cart-open');
        this.el.setAttribute('aria-hidden', 'true');
    }

    async refresh({ open = false } = {}) {
        if (open) {
            document.documentElement.classList.add('flyout-cart-open');
            document.body.classList.add('flyout-cart-open');
            this.el.setAttribute('aria-hidden', 'false');
        }
        const data = await this.waitFor(rpc('/theme_kingdom/cart/flyout'));
        const itemsEl = this.el.querySelector('.js_kingdom_flyout_items');
        const subtotalEl = this.el.querySelector('.js_kingdom_flyout_subtotal');
        const totalProductsEl = this.el.querySelector('.js_kingdom_flyout_total_products');
        if (itemsEl) {
            itemsEl.innerHTML = data.html;
        }
        if (subtotalEl) {
            subtotalEl.textContent = data.amount_total_formatted;
        }
        if (totalProductsEl) {
            totalProductsEl.textContent = data.cart_quantity;
        }
        for (const amountEl of document.querySelectorAll('.cart-ammount')) {
            amountEl.textContent = data.amount_total_formatted;
        }
        for (const qtyEl of document.querySelectorAll('.my_cart_quantity')) {
            if (data.cart_quantity === 0) {
                qtyEl.classList.add('d-none');
            } else {
                qtyEl.classList.remove('d-none');
                qtyEl.textContent = data.cart_quantity;
            }
        }
        browser.sessionStorage.setItem('website_sale_cart_quantity', data.cart_quantity);
        if (open) {
            document.documentElement.classList.add('flyout-cart-open');
            document.body.classList.add('flyout-cart-open');
            this.el.setAttribute('aria-hidden', 'false');
        }
    }

}

registry
    .category('public.interactions')
    .add('theme_kingdom.kingdom_flyout_cart', KingdomFlyoutCart);
