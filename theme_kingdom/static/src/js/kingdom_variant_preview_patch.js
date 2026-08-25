/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { ProductVariantPreviewImageHover } from '@website_sale/interactions/product/product_variant_preview_hover';
import { rpc } from '@web/core/network/rpc';
import { insertThousandsSep } from '@web/core/utils/numbers';
import { localization } from '@web/core/l10n/localization';

function formatCurrencyValue(amount, precision = 2) {
    const fixed = Number(amount || 0).toFixed(precision).split('.');
    fixed[0] = insertThousandsSep(fixed[0], localization.thousandsSep, localization.grouping);
    return precision ? fixed.join(localization.decimalPoint) : fixed[0];
}

function updateCardPrice(form, info) {
    if (!form || !info) {
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

/**
 * Stock only preventDefaults variant clicks on mobile, so desktop always opens
 * the product page. Keep shoppers on /shop and select the variant instead.
 */
patch(ProductVariantPreviewImageHover.prototype, {
    setup() {
        this.productImg =
            this.el.querySelector('.oe_product_image_img_wrapper_primary img') ||
            this.el.querySelector('.oe_product_image img');
        this.originalImgSrc = this.productImg?.getAttribute('src') || '';
    },

    _setImgSrc(imageSrc) {
        if (this.productImg && imageSrc) {
            this.productImg.src = imageSrc;
        }
    },

    /**
     * @override
     */
    _onClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();

        const targetElement = ev.target.closest('.o_product_variant_preview');
        const productCard = ev.target.closest('.oe_product_cart');
        if (!targetElement || !productCard) {
            return;
        }

        productCard.querySelectorAll('.o_product_variant_preview').forEach((preview) => {
            preview.classList.toggle('is-active', preview === targetElement);
        });

        const variantUrl =
            targetElement.dataset.variantUrl || targetElement.getAttribute('href') || '';
        const imageLink = productCard.querySelector('.oe_product_image_link');
        if (imageLink && variantUrl && variantUrl !== '#') {
            imageLink.href = variantUrl;
        }

        const titleLink = productCard.querySelector(
            '.o_wsale_product_information a[href], .o_wsale_products_item_title a'
        );
        if (titleLink && variantUrl && variantUrl !== '#') {
            titleLink.href = variantUrl;
        }

        const variantImageSrc = targetElement.dataset.variantImage;
        if (variantImageSrc) {
            this._setImgSrc(variantImageSrc);
        }

        const productId =
            parseInt(targetElement.dataset.productId, 10) ||
            parseInt((variantImageSrc || '').match(/product\.product\/(\d+)\//)?.[1], 10) ||
            0;
        const productIdInput = productCard.querySelector('input[name="product_id"]');
        if (productId && productIdInput) {
            productIdInput.value = String(productId);
        }

        const productTemplateId = parseInt(
            productCard.querySelector('input[name="product_template_id"]')?.value,
            10
        );
        const addQty = parseFloat(productCard.querySelector('input[name="add_qty"]')?.value) || 1;
        if (!productTemplateId) {
            return;
        }

        rpc('/website_sale/get_combination_info', {
            product_template_id: productTemplateId,
            product_id: productId,
            combination: [],
            add_qty: addQty,
        }).then((info) => {
            updateCardPrice(productCard, info);
            if (info?.product_id && productIdInput) {
                productIdInput.value = String(info.product_id);
            }
        });
    },
});
