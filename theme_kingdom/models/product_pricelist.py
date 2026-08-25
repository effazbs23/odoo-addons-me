# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    def action_bulk_add_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Multiple Products',
            'res_model': 'kingdom.pricelist.bulk.products',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pricelist_id': self.id,
            },
        }

    @api.model
    def _templates_from_pricelist_item(self, item):
        """Published templates covered by one pricelist rule (Odoo core semantics)."""
        ProductTemplate = self.env['product.template']
        if item.applied_on == '1_product' and item.product_tmpl_id:
            return item.product_tmpl_id
        if item.applied_on == '0_product_variant' and item.product_id:
            return item.product_id.product_tmpl_id
        if item.applied_on == '2_product_category' and item.categ_id:
            return ProductTemplate.search([
                ('sale_ok', '=', True),
                ('is_published', '=', True),
                ('categ_id', 'child_of', item.categ_id.id),
            ])
        return ProductTemplate.browse()

    @api.model
    def _pricelist_item_is_active(self, item, now=None):
        now = now or fields.Datetime.now()
        if item.date_start and item.date_start > now:
            return False
        if item.date_end and item.date_end < now:
            return False
        return True

    def get_offer_product_templates(self, active_only=True, limit=None):
        """Product templates referenced by rules on this pricelist."""
        self.ensure_one()
        now = fields.Datetime.now() if active_only else None
        seen = set()
        products = self.env['product.template'].browse()

        for item in self.item_ids:
            if active_only and not self._pricelist_item_is_active(item, now):
                continue
            for template in self._templates_from_pricelist_item(item):
                if template.id in seen:
                    continue
                if not template.sale_ok or not template.is_published:
                    continue
                seen.add(template.id)
                products |= template
                if limit and len(products) >= limit:
                    return products
        return products

    def get_product_offer_price(self, product, quantity=1.0, date=None):
        """Sale price for a product using Odoo's pricelist engine."""
        self.ensure_one()
        product = product.product_tmpl_id if product._name == 'product.product' else product
        variant = product.product_variant_id
        return self._get_product_price(
            variant,
            quantity,
            uom=variant.uom_id,
            date=date or fields.Datetime.now(),
        )
