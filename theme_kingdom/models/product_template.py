# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.fields import Domain
from odoo.http import request


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    kingdom_brand_id = fields.Many2one(
        'kingdom.brand',
        string='Brand',
        index=True,
        ondelete='set null',
        help='Brand assigned to this product. Used when filtering the shop by brand.',
    )

    def _kingdom_request_website(self):
        """Website from the HTTP request, or current website as a safe fallback."""
        try:
            website = getattr(request, 'website', None)
        except RuntimeError:
            # No HTTP request bound (shell / some asset renders).
            website = None
        if website is not None:
            return website
        return self.env['website'].get_current_website()

    def _website_show_quick_add(self):
        """Safe when QWeb renders without request.website (builder / public asset)."""
        self.ensure_one()
        if not self.filtered_domain(self.env['website']._product_domain()):
            return False
        website = self._kingdom_request_website()
        if not website:
            return bool(self._get_contextual_price())
        return not website.prevent_zero_price_sale or self._get_contextual_price()

    def _search_get_detail(self, website, order, options):
        result = super()._search_get_detail(website, order, options)
        brand_id = options.get('kingdom_brand_id')
        if brand_id:
            result['base_domain'].append([('kingdom_brand_id', '=', int(brand_id))])
        return result

    def _kingdom_resolve_pricelist(self, website, pricelist=None):
        if pricelist:
            return pricelist.sudo()
        if website and hasattr(website, 'kingdom_get_current_pricelist'):
            return website.kingdom_get_current_pricelist()
        available = website.get_pricelist_available(show_visible=False) if website else False
        if available:
            return available[0].sudo()
        return self.env['product.pricelist'].sudo()

    def _kingdom_resolve_fiscal_position(self, website):
        try:
            request.session
            return website._get_and_cache_current_fiscal_position()
        except (RuntimeError, AttributeError):
            return self.env['account.fiscal.position'].sudo()._get_fiscal_position(
                website.partner_id
            )

    def _kingdom_compute_combination_prices(self, website, pricelist=None, quantity=1.0):
        """Price info for cards/snippets without relying on request.website."""
        self.ensure_one()
        pricelist = self._kingdom_resolve_pricelist(website, pricelist=pricelist)
        currency = pricelist.currency_id or website.currency_id
        date = fields.Date.context_today(self)
        uom = self.uom_id

        pricelist_price, pricelist_rule_id = pricelist._get_product_price_rule(
            product=self,
            quantity=quantity,
            uom=uom,
            currency=currency,
        )

        price_before_discount = pricelist_price
        pricelist_item = self.env['product.pricelist.item'].browse(pricelist_rule_id)
        if pricelist_item._show_discount_on_shop():
            price_before_discount = pricelist_item._compute_price_before_discount(
                product=self,
                quantity=quantity or 1.0,
                date=date,
                uom=uom,
                currency=currency,
            )

        has_discounted_price = currency.compare_amounts(price_before_discount, pricelist_price) == 1
        combination_info = {
            'list_price': max(pricelist_price, price_before_discount),
            'price': pricelist_price,
            'has_discounted_price': has_discounted_price,
        }

        if (
            not has_discounted_price
            and self.compare_list_price
            and self.env['res.groups']._is_feature_enabled(
                'website_sale.group_product_price_comparison'
            )
        ):
            combination_info['compare_list_price'] = self.currency_id._convert(
                from_amount=self.compare_list_price,
                to_currency=currency,
                company=self.env.company,
                date=date,
                round=False,
            )

        product_taxes = self.sudo().taxes_id._filter_taxes_by_company(self.env.company)
        if product_taxes:
            fiscal_position = self._kingdom_resolve_fiscal_position(website)
            taxes = fiscal_position.map_tax(product_taxes)
            for price_key in ('price', 'list_price'):
                combination_info[price_key] = self._apply_taxes_to_price(
                    combination_info[price_key],
                    currency,
                    product_taxes,
                    taxes,
                    self,
                    website=website,
                )

        return combination_info

    def kingdom_get_price_display(self, website=None, pricelist=None):
        """Normalized sale / base / discount fields for Kingdom product cards."""
        self.ensure_one()
        website = (
            website
            or self._kingdom_request_website()
            or self.env['website'].get_current_website()
        )
        if not website:
            price = self.list_price
            compare = self.compare_list_price or 0
            return self.kingdom_price_display_from_info({
                'price': price,
                'list_price': price,
                'has_discounted_price': False,
                'compare_list_price': compare if compare > price else 0,
            })

        combination_info = self._kingdom_compute_combination_prices(
            website,
            pricelist=pricelist,
        )
        return self.kingdom_price_display_from_info(combination_info)

    @api.model
    def kingdom_price_display_from_info(self, combination_info):
        """Build card price dict from website_sale combination_info."""
        price = combination_info.get('price') or 0.0
        base_price = False
        if combination_info.get('has_discounted_price'):
            base_price = combination_info.get('list_price') or 0.0
        else:
            compare = combination_info.get('compare_list_price') or 0.0
            if compare > price:
                base_price = compare
        has_discount = bool(base_price and base_price > price)
        discount_percent = 0
        if has_discount:
            discount_percent = int(round((1 - (price / base_price)) * 100))
        return {
            'price': price,
            'base_price': base_price,
            'has_discount': has_discount,
            'discount_percent': discount_percent,
        }

    def kingdom_get_related_products(self, limit=12):
        """Products for the product page related block.

        Uses manually configured alternatives when set; otherwise falls back to
        other published products in the same eCommerce categories.
        """
        self.ensure_one()
        alternatives = self._get_website_alternative_product()
        if alternatives:
            return alternatives[:limit]

        if not self.public_categ_ids:
            return self.env['product.template']

        website = self.env['website'].get_current_website()
        domain = website.sale_product_domain() & Domain([
            ('id', '!=', self.id),
            ('public_categ_ids', 'child_of', self.public_categ_ids.ids),
        ])
        return self.env['product.template'].search(
            domain,
            limit=limit,
            order='website_sequence desc, id desc',
        )

    def _kingdom_ribbon_price_vals(self, price_vals=None):
        """Price dict accepted by product.ribbon._is_applicable_for (sale ribbons)."""
        self.ensure_one()
        if price_vals:
            return price_vals
        try:
            price = self._get_contextual_price()
        except Exception:
            price = self.list_price
        compare = self.compare_list_price or 0.0
        return {
            'price_reduce': price,
            'base_price': compare if compare > price else price,
            'price': price,
            'compare_list_price': compare,
            'has_discounted_price': bool(compare and compare > price),
        }

    def kingdom_get_display_ribbons(self, price_vals=None):
        """All ribbons to stack on product cards (manual + applicable auto New/Sale).

        Unlike ``_get_ribbon`` (single ribbon), homepage cards show Top + New stacked
        like the Kingdom reference layout whenever both apply.
        """
        self.ensure_one()
        ProductRibbon = self.env['product.ribbon'].sudo()
        variant = self.product_variant_id.sudo()
        ribbons = ProductRibbon.browse()

        manual = (variant.variant_ribbon_id if variant else ProductRibbon) or self.sudo().website_ribbon_id
        if manual:
            ribbons |= manual

        price_vals = self._kingdom_ribbon_price_vals(price_vals)
        auto_ribbons = ProductRibbon.search([('assign', '!=', 'manual')], order='sequence, id')
        for ribbon in auto_ribbons:
            if ribbon in ribbons:
                continue
            try:
                if variant and ribbon._is_applicable_for(variant, price_vals):
                    ribbons |= ribbon
            except Exception:
                continue

        # Visual order like the reference: Top/Sale above, New below.
        return ribbons.sorted(
            key=lambda r: (
                1 if 'new' in ((r.assign or '') + ' ' + (r.name or '')).lower() else 0,
                r.sequence,
                r.id,
            )
        )
