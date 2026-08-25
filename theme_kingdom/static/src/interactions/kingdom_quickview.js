/** @odoo-module **/

import { Interaction } from '@web/public/interaction';
import { registry } from '@web/core/registry';
import { rpc } from '@web/core/network/rpc';
import { insertThousandsSep } from '@web/core/utils/numbers';
import { localization } from '@web/core/l10n/localization';
import wSaleUtils from '@website_sale/js/website_sale_utils';

/**
 * Kingdom product Quick View: fetches product HTML dynamically and supports
 * variant price/image updates plus Add to Cart via the cart service.
 *
 * Uses delegated listeners on #wrapwrap so buttons injected by live homepage
 * snippets (featured / best sale / tabs) keep working after DOM refresh.
 */
export class KingdomQuickView extends Interaction {
    static selector = '#wrapwrap';

    dynamicContent = {
        _root: {
            't-on-click': this.onRootClick,
            't-on-change': this.onRootChange,
        },
    };

    setup() {
        this._onDocumentKeydown = this.onDocumentKeydown.bind(this);
        this._activeRequest = 0;
        this._onQuickViewClickLocked = this.locked(this.onQuickViewClick);
        this._onVariantChangeLocked = this.locked(this.onVariantChange);
        this._onAddToCartClickLocked = this.locked(this.onAddToCartClick);
    }

    start() {
        document.addEventListener('keydown', this._onDocumentKeydown);
        return super.start(...arguments);
    }

    destroy() {
        document.removeEventListener('keydown', this._onDocumentKeydown);
        this.closeModal();
        return super.destroy(...arguments);
    }

    get modalEl() {
        return document.getElementById('kingdom_quickview_modal');
    }

    get modalBodyEl() {
        return this.modalEl?.querySelector('.kingdom-quickview-modal__body');
    }

    get productRootEl() {
        return this.modalEl?.querySelector('.js_product');
    }

    onRootClick(ev) {
        const quickViewBtn = ev.target.closest('.kingdom-quickview-btn');
        if (quickViewBtn) {
            ev.preventDefault();
            ev.stopPropagation();
            return this._onQuickViewClickLocked.call(this, {
                ...ev,
                currentTarget: quickViewBtn,
            });
        }

        if (!this.modalEl?.contains(ev.target)) {
            return;
        }

        if (ev.target.closest('[data-kingdom-quickview-close]')) {
            ev.preventDefault();
            return this.onCloseClick();
        }

        const qtyBtn = ev.target.closest('.kingdom-quickview__qty-btn');
        if (qtyBtn) {
            ev.preventDefault();
            return this.onQtyClick({
                ...ev,
                currentTarget: qtyBtn,
            });
        }

        if (ev.target.closest('.kingdom-quickview__add-to-cart')) {
            ev.preventDefault();
            return this._onAddToCartClickLocked.call(this, ev);
        }
    }

    onRootChange(ev) {
        if (!this.modalEl?.contains(ev.target)) {
            return;
        }
        const target = ev.target;
        if (
            target.classList.contains('js_variant_change')
            && !target.classList.contains('variant_custom_value')
        ) {
            return this._onVariantChangeLocked.call(this, ev);
        }
    }

    onDocumentKeydown(ev) {
        if (ev.key === 'Escape' && this.isOpen()) {
            this.closeModal();
        }
    }

    onCloseClick() {
        this.closeModal();
    }

    isOpen() {
        return this.modalEl && !this.modalEl.hasAttribute('hidden');
    }

    openModal() {
        const modal = this.modalEl;
        if (!modal) {
            return;
        }
        modal.hidden = false;
        modal.setAttribute('aria-hidden', 'false');
        document.documentElement.classList.add('kingdom-quickview-open');
        document.body.classList.add('kingdom-quickview-open');
    }

    closeModal() {
        const modal = this.modalEl;
        if (!modal) {
            return;
        }
        modal.hidden = true;
        modal.setAttribute('aria-hidden', 'true');
        document.documentElement.classList.remove('kingdom-quickview-open');
        document.body.classList.remove('kingdom-quickview-open');
    }

    async onQuickViewClick(ev) {
        const button = ev.currentTarget;
        const productTemplateId = parseInt(button.dataset.productTemplateId, 10);
        if (!productTemplateId || !this.modalBodyEl) {
            return;
        }

        this.modalBodyEl.innerHTML =
            '<div class="kingdom-quickview-modal__loading">Loading…</div>';
        this.openModal();

        const requestId = ++this._activeRequest;
        try {
            const data = await this.waitFor(
                rpc(`/shop/quickview/${productTemplateId}`, {})
            );
            if (requestId !== this._activeRequest) {
                return;
            }
            this.modalBodyEl.innerHTML = '';
            this.modalBodyEl.appendChild(this._htmlToElement(data.html));
        } catch (_error) {
            if (requestId !== this._activeRequest) {
                return;
            }
            this.modalBodyEl.innerHTML =
                '<div class="alert alert-danger m-3 mb-0">Unable to load product details.</div>';
        }
    }

    async onVariantChange(ev) {
        const parent = this.productRootEl;
        if (!parent || ev.target.classList.contains('variant_custom_value')) {
            return;
        }

        const combination = wSaleUtils.getSelectedAttributeValues(parent);
        const productTemplateId = parseInt(
            parent.querySelector('.product_template_id')?.value,
            10
        );
        const productId = parseInt(parent.querySelector('.product_id')?.value, 10) || 0;
        const addQty = parseFloat(parent.querySelector('input[name="add_qty"]')?.value) || 1;

        const combinationInfo = await this.waitFor(
            rpc('/website_sale/get_combination_info', {
                product_template_id: productTemplateId,
                product_id: productId,
                combination,
                add_qty: addQty,
            })
        );
        this._applyCombinationInfo(parent, combinationInfo);
    }

    onQtyClick(ev) {
        const parent = this.productRootEl;
        const input = parent?.querySelector('input[name="add_qty"]');
        if (!input) {
            return;
        }
        const delta = parseInt(ev.currentTarget.dataset.kingdomQty, 10) || 0;
        const next = Math.max(1, (parseInt(input.value, 10) || 1) + delta);
        input.value = String(next);
        input.dispatchEvent(new Event('change', { bubbles: true }));
        // Refresh price when qty-dependent pricelist rules apply.
        parent.querySelector('.js_variant_change')?.dispatchEvent(
            new Event('change', { bubbles: true })
        );
    }

    async onAddToCartClick() {
        const root = this.modalEl?.querySelector('.kingdom-quickview');
        const parent = this.productRootEl;
        if (!root || !parent) {
            return;
        }
        if (root.dataset.needsFullPage === '1') {
            window.location = root.querySelector('.kingdom-quickview__details-link')?.href || '/shop';
            return;
        }

        const productTemplateId = parseInt(root.dataset.productTemplateId, 10);
        const productId = parseInt(parent.querySelector('.product_id')?.value, 10) || undefined;
        const quantity = parseFloat(parent.querySelector('input[name="add_qty"]')?.value) || 1;
        const ptavs = wSaleUtils.getSelectedAttributeValues(parent);
        const isCombo = root.dataset.productType === 'combo';

        const unavailable = parent.classList.contains('css_not_available');
        if (unavailable) {
            return;
        }

        await this.waitFor(
            this.services.cart.add(
                {
                    productTemplateId,
                    productId,
                    quantity,
                    ptavs,
                    isCombo,
                },
                {
                    // Skip optional-product configurator; add the main product only.
                    isBuyNow: true,
                    redirectToCart: false,
                    isConfigured: true,
                    showQuantity: false,
                }
            )
        );
        this.closeModal();
    }

    _htmlToElement(html) {
        const template = document.createElement('template');
        // Server-rendered QWeb from our own controller (trusted same-origin HTML).
        template.innerHTML = typeof html === 'string' ? html : String(html ?? '');
        return template.content.firstElementChild || document.createElement('div');
    }

    _applyCombinationInfo(parent, info) {
        const productIdInput = parent.querySelector('.product_id');
        if (productIdInput && info.product_id) {
            productIdInput.value = info.product_id;
        }

        const image = this.modalEl.querySelector('.kingdom-quickview__image');
        if (image && info.product_id && !info.no_product_change) {
            image.src = `/web/image/product.product/${info.product_id}/image_1024`;
        }

        this._updatePrice(parent, info);

        const isPossible = !!info.is_combination_possible;
        parent.classList.toggle('css_not_available', !isPossible);
        const msg = parent.querySelector('.css_not_available_msg');
        msg?.classList.toggle('d-none', isPossible);

        const addBtn = parent.querySelector('.kingdom-quickview__add-to-cart');
        if (addBtn) {
            addBtn.disabled = !isPossible || !!info.prevent_zero_price_sale;
        }

        const priceRoot = parent.querySelector('.product_price');
        priceRoot?.classList.toggle('d-none', !!info.prevent_zero_price_sale);
    }

    _updatePrice(parent, info) {
        const precision = info.currency_precision ?? 2;
        const format = (amount) => {
            const fixed = Number(amount || 0).toFixed(precision).split('.');
            fixed[0] = insertThousandsSep(
                fixed[0],
                localization.thousandsSep,
                localization.grouping
            );
            return precision ? fixed.join(localization.decimalPoint) : fixed[0];
        };

        const priceValue = parent.querySelector('.oe_price .oe_currency_value');
        if (priceValue) {
            priceValue.textContent = format(info.price);
        }

        const listPriceWrapper = parent.querySelector('.oe_default_price');
        const listPriceValue = listPriceWrapper?.querySelector('.oe_currency_value');
        if (listPriceValue) {
            listPriceValue.textContent = format(info.list_price);
            listPriceWrapper.classList.toggle('d-none', !info.has_discounted_price);
        }
    }
}

registry.category('public.interactions').add('theme_kingdom.quickview', KingdomQuickView);
