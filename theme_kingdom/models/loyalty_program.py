# -*- coding: utf-8 -*-
from odoo import fields, models


class LoyaltyProgram(models.Model):
    _inherit = 'loyalty.program'

    def get_promotion_pricelist(self):
        """Pricelist linked to this promotion, if any."""
        self.ensure_one()
        return self.pricelist_ids[:1]

    def get_promotion_product_templates(self, limit=None):
        """Published products targeted by this promotion program."""
        self.ensure_one()
        ProductTemplate = self.env['product.template']
        templates = ProductTemplate.browse()

        for reward in self.reward_ids.filtered(lambda r: r.active):
            if reward.reward_type == 'product':
                templates |= reward.reward_product_ids.product_tmpl_id
                if reward.reward_product_id:
                    templates |= reward.reward_product_id.product_tmpl_id
            elif reward.reward_type == 'discount':
                if reward.discount_applicability == 'specific':
                    templates |= reward.all_discount_product_ids.product_tmpl_id
                elif reward.discount_product_category_id:
                    templates |= ProductTemplate.search([
                        ('sale_ok', '=', True),
                        ('is_published', '=', True),
                        ('categ_id', 'child_of', reward.discount_product_category_id.id),
                    ])
                elif reward.discount_product_tag_id:
                    templates |= reward.discount_product_tag_id.product_ids.product_tmpl_id

        for rule in self.rule_ids.filtered('active'):
            if rule.product_ids:
                templates |= rule.product_ids.product_tmpl_id
            elif rule.product_category_id:
                templates |= ProductTemplate.search([
                    ('sale_ok', '=', True),
                    ('is_published', '=', True),
                    ('categ_id', 'child_of', rule.product_category_id.id),
                ])

        templates = templates.filtered(lambda t: t.sale_ok and t.is_published)
        if limit:
            return templates[:limit]
        return templates

    def promotion_has_specific_products(self):
        """True when the program targets explicit products (not order-wide only)."""
        self.ensure_one()
        return bool(self.get_promotion_product_templates())

    def is_promotion_active_today(self, now=None):
        """True when the program is active within its configured date range."""
        self.ensure_one()
        if not self.active:
            return False
        today = fields.Date.context_today(self)
        if self.date_from and today < self.date_from:
            return False
        if self.date_to and today > self.date_to:
            return False
        return True
