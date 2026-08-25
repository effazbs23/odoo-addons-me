/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { insertThousandsSep } from '@web/core/utils/numbers';
import { localization } from '@web/core/l10n/localization';

const GRID_CLASS = 'o_wsale_products_opt_layout_catalog';
const LIST_CLASS = 'o_wsale_products_opt_layout_list';

/**
 * Normalize shop action icons: cart → compare → wishlist → quick view.
 * Also pulls wishlist into the action row (core injects it as a sibling).
 */
function normalizeProductActionIcons(root) {
    if (!root) {
        return;
    }

    root.querySelectorAll('.o_wsale_product_btn').forEach((btnWrap) => {
        const row = btnWrap.querySelector(':scope > .o_wsale_product_action_row');
        if (!row) {
            return;
        }

        const wishlist =
            btnWrap.querySelector(':scope > .o_add_wishlist') ||
            row.querySelector('.o_add_wishlist');
        const cart = row.querySelector('.o_wsale_product_btn_primary');
        const compare = row.querySelector('.o_add_compare');
        const quickview = row.querySelector('.kingdom-quickview-btn');

        // Drop invisible compare placeholders so they cannot steal 1st slot.
        row.querySelectorAll('.o_add_compare_placeholder').forEach((el) => el.remove());

        [cart, compare, wishlist, quickview].filter(Boolean).forEach((el) => {
            row.appendChild(el);
        });
    });
}

function formatCurrencyValue(amount, precision = 2) {
    const fixed = Number(amount || 0).toFixed(precision).split('.');
    fixed[0] = insertThousandsSep(fixed[0], localization.thousandsSep, localization.grouping);
    return precision ? fixed.join(localization.decimalPoint) : fixed[0];
}

/**
 * Shop grid/list layout switcher for Kingdom product toolbar.
 */
export class KingdomShopLayoutSwitch extends Interaction {
    static selector = '.k-shop-layout-switch';

    dynamicContent = {
        '.k-shop-layout-switch__btn': {
            't-on-click.prevent': this.onLayoutClick,
        },
    };

    setup() {
        this._grid = this.el.closest('#o_wsale_container')?.querySelector('#o_wsale_products_grid');
    }

    start() {
        this._restoreSavedLayout();
        this._syncButtonsFromGrid();
        normalizeProductActionIcons(this._grid);
        return super.start(...arguments);
    }

    _restoreSavedLayout() {
        if (!this._grid) {
            return;
        }
        let saved = null;
        try {
            saved = window.sessionStorage.getItem('kingdom_shop_layout');
        } catch (_err) {
            saved = null;
        }
        if (saved === 'list') {
            this._grid.classList.remove(GRID_CLASS);
            this._grid.classList.add(LIST_CLASS);
        } else if (saved === 'grid') {
            this._grid.classList.remove(LIST_CLASS);
            this._grid.classList.add(GRID_CLASS);
        }
    }

    _syncButtonsFromGrid() {
        if (!this._grid) {
            return;
        }
        const isList = this._grid.classList.contains(LIST_CLASS);
        this.el.querySelectorAll('.k-shop-layout-switch__btn').forEach((btn) => {
            const layout = btn.dataset.kShopLayout;
            const active = isList ? layout === 'list' : layout === 'grid';
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });
    }

    onLayoutClick(ev) {
        const button = ev.currentTarget;
        const layout = button.dataset.kShopLayout;
        if (!layout || !this._grid) {
            return;
        }

        if (layout === 'list') {
            this._grid.classList.remove(GRID_CLASS);
            this._grid.classList.add(LIST_CLASS);
        } else {
            this._grid.classList.remove(LIST_CLASS);
            this._grid.classList.add(GRID_CLASS);
        }

        this.el.querySelectorAll('.k-shop-layout-switch__btn').forEach((btn) => {
            const active = btn === button;
            btn.classList.toggle('is-active', active);
            btn.setAttribute('aria-pressed', active ? 'true' : 'false');
        });

        try {
            window.sessionStorage.setItem('kingdom_shop_layout', layout);
        } catch (_err) {
            // Ignore private-mode / storage errors.
        }

        normalizeProductActionIcons(this._grid);
    }
}

/**
 * Wishlist placement + live list-view price update when quantity changes
 * (stock WebsiteSale only refreshes price on `.js_main_product`).
 */
export class KingdomShopProductActions extends Interaction {
    static selector = '#o_wsale_products_grid';

    dynamicContent = {
        'form.oe_product_cart input[name="add_qty"]': {
            't-on-change': this.locked(this.onQtyChange),
        },
        'form.oe_product_cart .o_product_variant_preview': {
            't-on-click.prevent.stop': this.onVariantPreviewClick,
        },
    };

    start() {
        normalizeProductActionIcons(this.el);
        return super.start(...arguments);
    }

    async onVariantPreviewClick(ev) {
        const link = ev.currentTarget;
        const form = link.closest('form.oe_product_cart');
        if (!form) {
            return;
        }

        form.querySelectorAll('.o_product_variant_preview').forEach((preview) => {
            preview.classList.toggle('is-active', preview === link);
        });

        const variantImage = link.dataset.variantImage;
        const productImg =
            form.querySelector('.oe_product_image_img_wrapper_primary img') ||
            form.querySelector('.oe_product_image img');
        if (variantImage && productImg) {
            productImg.src = variantImage;
        }

        const imageLink = form.querySelector('a.oe_product_image_link');
        const variantUrl = link.dataset.variantUrl || link.getAttribute('href');
        if (imageLink && variantUrl && variantUrl !== '#') {
            imageLink.href = variantUrl;
        }

        const productId =
            parseInt(link.dataset.productId, 10) ||
            parseInt((variantImage || '').match(/product\.product\/(\d+)\//)?.[1], 10) ||
            0;
        const productIdInput = form.querySelector('input[name="product_id"]');
        if (productId && productIdInput) {
            productIdInput.value = String(productId);
        }

        const productTemplateId = parseInt(
            form.querySelector('input[name="product_template_id"]')?.value,
            10
        );
        const addQty = parseFloat(form.querySelector('input[name="add_qty"]')?.value) || 1;
        if (!productTemplateId) {
            return;
        }

        const info = await this.waitFor(
            rpc('/website_sale/get_combination_info', {
                product_template_id: productTemplateId,
                product_id: productId,
                combination: [],
                add_qty: addQty,
            })
        );
        this._updateCardPrice(form, info);
        if (info?.product_id && productIdInput) {
            productIdInput.value = String(info.product_id);
        }
    }

    async onQtyChange(ev) {
        const form = ev.currentTarget.closest('form.oe_product_cart');
        if (!form) {
            return;
        }

        const productTemplateId = parseInt(
            form.querySelector('input[name="product_template_id"]')?.value,
            10
        );
        const productId = parseInt(form.querySelector('input[name="product_id"]')?.value, 10) || 0;
        const addQty = parseFloat(ev.currentTarget.value) || 1;
        if (!productTemplateId) {
            return;
        }

        const info = await this.waitFor(
            rpc('/website_sale/get_combination_info', {
                product_template_id: productTemplateId,
                product_id: productId,
                combination: [],
                add_qty: addQty,
            })
        );
        this._updateCardPrice(form, info);
    }

    _updateCardPrice(form, info) {
        if (!info) {
            return;
        }
        const precision = info.currency_precision ?? 2;
        const saleValue =
            form.querySelector('.product_price [aria-label="Sale price"] .oe_currency_value') ||
            form.querySelector('.product_price > span .oe_currency_value') ||
            form.querySelector('.product_price .oe_currency_value');
        if (saleValue) {
            saleValue.textContent = formatCurrencyValue(info.price, precision);
        }

        const baseValue = form.querySelector('.product_price del .oe_currency_value');
        if (baseValue && info.list_price != null) {
            baseValue.textContent = formatCurrencyValue(info.list_price, precision);
            const baseWrap = baseValue.closest('[name="product_base_price"], del');
            if (baseWrap) {
                baseWrap.classList.toggle('d-none', !info.has_discounted_price);
            }
        }
    }
}

registry
    .category('public.interactions')
    .add('theme_kingdom.shop_layout_switch', KingdomShopLayoutSwitch);

registry
    .category('public.interactions')
    .add('theme_kingdom.shop_product_actions', KingdomShopProductActions);
