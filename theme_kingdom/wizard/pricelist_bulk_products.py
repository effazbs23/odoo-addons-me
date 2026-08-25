# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class KingdomPricelistBulkProducts(models.TransientModel):
    _name = 'kingdom.pricelist.bulk.products'
    _description = 'Add Multiple Products to Pricelist'

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Pricelist',
        required=True,
        ondelete='cascade',
    )
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        string='Products',
        domain="[('sale_ok', '=', True)]",
        help='Select all products that should get the same offer rule.',
    )
    compute_price = fields.Selection(
        selection=[
            ('percentage', 'Discount'),
            ('formula', 'Formula'),
            ('fixed', 'Fixed Price'),
        ],
        string='Price Type',
        default='formula',
        required=True,
    )
    base = fields.Selection(
        selection=[
            ('list_price', 'Sales Price'),
            ('standard_price', 'Cost'),
            ('pricelist', 'Other Pricelist'),
        ],
        string='Based on',
        default='list_price',
        required=True,
    )
    percent_price = fields.Float(
        string='Discount (%)',
        default=20.0,
    )
    price_discount = fields.Float(
        string='Discount (%)',
        default=20.0,
        digits=(16, 2),
    )
    price_round = fields.Float(
        string='Round off to',
        default=0.0,
    )
    price_surcharge = fields.Float(
        string='Extra Fee',
        default=0.0,
    )
    fixed_price = fields.Float(
        string='Fixed Price',
        default=0.0,
    )
    min_quantity = fields.Float(
        string='Min. Quantity',
        default=0.0,
    )
    date_start = fields.Datetime(string='Start Date')
    date_end = fields.Datetime(string='End Date')
    skip_existing = fields.Boolean(
        string='Skip products already on pricelist',
        default=True,
        help='Do not create a duplicate rule if the product already has a line on this pricelist.',
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get('pricelist_id'):
            return res
        active_id = self.env.context.get('active_id')
        active_model = self.env.context.get('active_model')
        if active_model == 'product.pricelist' and active_id:
            res['pricelist_id'] = active_id
        elif self.env.context.get('default_pricelist_id'):
            res['pricelist_id'] = self.env.context['default_pricelist_id']
        return res

    def _existing_product_tmpl_ids(self):
        self.ensure_one()
        return set(
            self.pricelist_id.item_ids.filtered(
                lambda item: item.applied_on == '1_product' and item.product_tmpl_id
            ).mapped('product_tmpl_id').ids
        )

    def _prepare_item_vals(self, product_tmpl):
        self.ensure_one()
        vals = {
            'pricelist_id': self.pricelist_id.id,
            'applied_on': '1_product',
            'display_applied_on': '1_product',
            'product_tmpl_id': product_tmpl.id,
            'compute_price': self.compute_price,
            'base': self.base,
            'min_quantity': self.min_quantity,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        if self.compute_price == 'percentage':
            vals['percent_price'] = self.percent_price
        elif self.compute_price == 'formula':
            vals.update({
                'price_discount': self.price_discount,
                'price_round': self.price_round,
                'price_surcharge': self.price_surcharge,
            })
        else:
            vals['fixed_price'] = self.fixed_price
        return vals

    def action_apply(self):
        self.ensure_one()
        if not self.product_tmpl_ids:
            raise UserError(_('Select at least one product.'))

        existing = self._existing_product_tmpl_ids() if self.skip_existing else set()
        to_create = []
        skipped = 0
        for product_tmpl in self.product_tmpl_ids:
            if product_tmpl.id in existing:
                skipped += 1
                continue
            to_create.append(self._prepare_item_vals(product_tmpl))

        if not to_create:
            raise UserError(
                _('All selected products already have a rule on this pricelist.')
            )

        self.env['product.pricelist.item'].create(to_create)

        message = _('%s product rule(s) added.') % len(to_create)
        if skipped:
            message += ' ' + _('%s skipped (already on pricelist).') % skipped

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Pricelist updated'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
