# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class KingdomDealsOfDay(models.Model):
    _name = 'kingdom.deals.of.day'
    _inherit = ['kingdom.website.cache.mixin']
    _description = 'Kingdom Deal of the Day'
    _order = 'sequence, id'

    name = fields.Char(
        string='Deal Title',
        required=True,
        help='Shown on the homepage deal block (e.g. Weekend Sale, Cooking pan).',
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    date_start = fields.Datetime(
        string='Offer Start',
        required=True,
        default=fields.Datetime.now,
        help='When this offer becomes visible on the website.',
    )
    date_end = fields.Datetime(
        string='Offer End',
        required=True,
        help='Countdown ends at this date/time; offer is hidden after this moment.',
    )
    deal_end_time = fields.Datetime(
        related='date_end',
        string='Countdown End',
        readonly=False,
    )

    duration_days = fields.Integer(
        string='Duration (days)',
        compute='_compute_duration_days',
        store=True,
    )
    state = fields.Selection(
        selection=[
            ('scheduled', 'Scheduled'),
            ('running', 'Running'),
            ('expired', 'Expired'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
    )

    pricelist_id = fields.Many2one(
        comodel_name='product.pricelist',
        string='Offer Pricelist',
        ondelete='restrict',
        default=lambda self: self.env['product.pricelist'].search(
            [('company_id', 'in', [False, self.env.company.id])],
            limit=1,
        ),
        help='Pricelist with offer rules. Used for storefront prices via Odoo pricelist engine. '
             'Auto-filled from the linked promotion when available.',
    )
    promotion_id = fields.Many2one(
        comodel_name='loyalty.program',
        string='Promotion Program',
        ondelete='set null',
        domain="[('program_type', 'in', ('promotion', 'promo_code', 'buy_x_get_y')), ('active', '=', True)]",
        help='Optional link to Sales → Promotions. Reuses product targeting and pricelist from Odoo.',
    )
    product_source = fields.Selection(
        selection=[
            ('pricelist', 'All products on pricelist'),
            ('promotion', 'Products from promotion'),
            ('selected', 'Pick products from pricelist'),
        ],
        string='Products on Website',
        default='pricelist',
        required=True,
        help='Pricelist: all active rules on the offer pricelist. '
             'Promotion: products from the linked promotion program. '
             'Pick products: choose specific products from the pricelist.',
    )
    allowed_product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        compute='_compute_allowed_product_tmpl_ids',
        string='Products on Offer Pricelist',
    )
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        relation='kingdom_deals_of_day_product_rel',
        column1='deal_id',
        column2='product_tmpl_id',
        string='Selected Products',
        domain="[('id', 'in', allowed_product_tmpl_ids)]",
        help='Pick one or more products that have an offer line on the pricelist.',
    )
    item_count = fields.Integer(
        string='Products',
        compute='_compute_item_count',
    )
    product_limit = fields.Integer(
        string='Max Products',
        default=24,
        help='Maximum number of products shown on the homepage carousel.',
    )

    weekday_mon = fields.Boolean(string='Monday', default=True)
    weekday_tue = fields.Boolean(string='Tuesday', default=True)
    weekday_wed = fields.Boolean(string='Wednesday', default=True)
    weekday_thu = fields.Boolean(string='Thursday', default=True)
    weekday_fri = fields.Boolean(string='Friday', default=True)
    weekday_sat = fields.Boolean(string='Saturday', default=True)
    weekday_sun = fields.Boolean(string='Sunday', default=True)

    banner_image = fields.Image(
        string='Sidebar Banner',
        max_width=800,
        max_height=600,
    )
    sale_percent = fields.Char(
        string='Sale Highlight',
        default='25',
    )
    sale_subtitle = fields.Char(
        string='Sale Subtitle',
        default='% OFF',
    )
    show_sidebar_sale = fields.Boolean(
        string='Show Sidebar Sale Block',
        default=True,
    )

    @api.depends('product_tmpl_ids', 'product_source', 'pricelist_id', 'pricelist_id.item_ids', 'promotion_id')
    def _compute_item_count(self):
        for deal in self:
            deal.item_count = len(deal._get_offer_products())

    @api.depends('pricelist_id', 'pricelist_id.item_ids', 'promotion_id', 'promotion_id.reward_ids')
    def _compute_allowed_product_tmpl_ids(self):
        for deal in self:
            deal.allowed_product_tmpl_ids = deal._collect_allowed_templates()

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for deal in self:
            if deal.date_start and deal.date_end and deal.date_end < deal.date_start:
                raise ValidationError('Offer end must be after offer start.')

    @api.constrains('pricelist_id', 'product_tmpl_ids', 'product_source', 'promotion_id')
    def _check_offer_configuration(self):
        for deal in self:
            if deal.product_source == 'promotion' and not deal.promotion_id:
                raise ValidationError('Select a promotion program or change the product source.')
            if deal.product_source == 'selected' and deal.product_tmpl_ids:
                allowed = deal._collect_allowed_templates()
                invalid = deal.product_tmpl_ids - allowed
                if invalid:
                    raise ValidationError(
                        'These products are not on the offer pricelist or promotion: %s'
                        % ', '.join(invalid.mapped('name'))
                    )
            if deal.product_source in ('pricelist', 'selected') and not deal.pricelist_id:
                raise ValidationError('An offer pricelist is required for this product source.')

    @api.onchange('promotion_id')
    def _onchange_promotion_id(self):
        if not self.promotion_id:
            return
        promotion_pl = self.promotion_id.get_promotion_pricelist()
        if promotion_pl:
            self.pricelist_id = promotion_pl
        if self.product_source == 'promotion':
            self.product_tmpl_ids = False

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        if self.pricelist_id and self.product_tmpl_ids:
            allowed = self._collect_allowed_templates()
            self.product_tmpl_ids = self.product_tmpl_ids & allowed

    @api.depends('date_start', 'date_end')
    def _compute_duration_days(self):
        for deal in self:
            if deal.date_start and deal.date_end and deal.date_end >= deal.date_start:
                delta = deal.date_end - deal.date_start
                deal.duration_days = delta.days + (1 if delta.seconds or not delta.days else 0)
            else:
                deal.duration_days = 0

    @api.depends('date_start', 'date_end', 'active')
    def _compute_state(self):
        now = fields.Datetime.now()
        for deal in self:
            if not deal.active:
                deal.state = 'expired'
            elif deal.date_start and now < deal.date_start:
                deal.state = 'scheduled'
            elif deal.date_end and now > deal.date_end:
                deal.state = 'expired'
            else:
                deal.state = 'running'

    @api.model
    def _cron_process_deal_schedule(self):
        """Scheduled action: refresh deal status and homepage when start/end is reached."""
        now = fields.Datetime.now()
        deals = self.sudo().search([('active', '=', True)])
        if not deals:
            return

        old_states = {deal.id: deal.state for deal in deals}
        self.env.add_to_compute(self._fields['state'], deals)
        deals.mapped('state')

        changed = deals.filtered(lambda d: old_states.get(d.id) != d.state)
        if changed:
            changed._invalidate_kingdom_website_cache()
            return

        margin = timedelta(minutes=5)
        boundary = self.sudo().search([
            ('active', '=', True),
            '|',
            '&', ('date_start', '>', now - margin), ('date_start', '<=', now),
            '&', ('date_end', '>=', now - margin), ('date_end', '<', now),
        ])
        if boundary:
            boundary._invalidate_kingdom_website_cache()

    def action_open_pricelist(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offer Pricelist',
            'res_model': 'product.pricelist',
            'res_id': self.pricelist_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_bulk_add_pricelist_products(self):
        self.ensure_one()
        if not self.pricelist_id:
            raise ValidationError('Select an offer pricelist first.')
        return self.pricelist_id.action_bulk_add_products()

    def action_open_promotion(self):
        self.ensure_one()
        if not self.promotion_id:
            raise ValidationError('No promotion program linked.')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Promotion Program',
            'res_model': 'loyalty.program',
            'res_id': self.promotion_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _offer_runs_today(self):
        """True if today is an allowed weekday (or no weekday filter is set)."""
        self.ensure_one()
        flags = [
            self.weekday_mon,
            self.weekday_tue,
            self.weekday_wed,
            self.weekday_thu,
            self.weekday_fri,
            self.weekday_sat,
            self.weekday_sun,
        ]
        if not any(flags):
            return True
        today = fields.Date.context_today(self)
        weekday = today.weekday()
        by_day = {
            0: self.weekday_mon,
            1: self.weekday_tue,
            2: self.weekday_wed,
            3: self.weekday_thu,
            4: self.weekday_fri,
            5: self.weekday_sat,
            6: self.weekday_sun,
        }
        return by_day.get(weekday, True)

    def _collect_allowed_templates(self):
        """Products allowed from linked pricelist and/or promotion."""
        self.ensure_one()
        templates = self.env['product.template']
        if self.pricelist_id:
            templates |= self.pricelist_id.get_offer_product_templates(active_only=False)
        if self.promotion_id:
            templates |= self.promotion_id.get_promotion_product_templates()
        return templates.filtered(lambda p: p.sale_ok and p.is_published)

    def _get_products_from_selected_products(self):
        """Products explicitly picked on the deal."""
        self.ensure_one()
        limit = self.product_limit or 24
        products = self.product_tmpl_ids.filtered(
            lambda p: p.sale_ok and p.is_published
        )
        return products[:limit]

    def _get_products_from_pricelist(self, include_scheduled=False):
        """All products from rules on the offer pricelist."""
        self.ensure_one()
        if not self.pricelist_id:
            return self.env['product.template']
        limit = self.product_limit or 24
        products = self.pricelist_id.get_offer_product_templates(
            active_only=True,
            limit=limit,
        )
        if not products and include_scheduled:
            products = self.pricelist_id.get_offer_product_templates(
                active_only=False,
                limit=limit,
            )
        return products

    def _get_products_from_promotion(self):
        """Products from the linked Odoo promotion program."""
        self.ensure_one()
        if not self.promotion_id:
            return self.env['product.template']
        if not self.promotion_id.is_promotion_active_today():
            return self.env['product.template']
        limit = self.product_limit or 24
        products = self.promotion_id.get_promotion_product_templates(limit=limit)
        if not products and self.pricelist_id:
            # Order-wide promos (e.g. "10% on orders") have no product list;
            # show products from the linked offer pricelist instead.
            products = self._get_products_from_pricelist(include_scheduled=True)
        return products

    def _get_offer_products(self):
        """Products shown in the deal carousel."""
        self.ensure_one()
        if self.product_source == 'selected':
            return self._get_products_from_selected_products()
        if self.product_source == 'promotion':
            return self._get_products_from_promotion()
        return self._get_products_from_pricelist(include_scheduled=True)

    def get_deal_pricelist(self):
        """Pricelist used to price deal products on the storefront."""
        self.ensure_one()
        if self.promotion_id:
            promotion_pl = self.promotion_id.get_promotion_pricelist()
            if promotion_pl:
                return promotion_pl
        return self.pricelist_id

    @api.model
    def _website_deal_domain(self):
        now = fields.Datetime.now()
        return [
            ('active', '=', True),
            ('date_start', '<=', now),
            ('date_end', '>=', now),
            '|',
            ('pricelist_id', '!=', False),
            ('promotion_id', '!=', False),
        ]

    @api.model
    def get_preview_deal(self):
        """Fallback deal for the website editor when no offer is currently active."""
        return self.sudo().search(
            ['|', ('pricelist_id', '!=', False), ('promotion_id', '!=', False)],
            order='sequence asc, id asc',
            limit=1,
        )

    @api.model
    def get_website_deal(self):
        """Active deal for the storefront (date range + weekday + products)."""
        deals = self.sudo().search(
            self._website_deal_domain(),
            order='sequence asc, id asc',
        )
        for deal in deals:
            if deal._offer_runs_today() and deal._get_offer_products():
                return deal
        return self.browse()

    def get_countdown_end_ms(self):
        """UTC epoch ms for JS countdown (Odoo stores datetimes in UTC)."""
        self.ensure_one()
        if not self.date_end:
            return 0
        return int(self.date_end.timestamp() * 1000)

    def get_countdown_iso(self):
        """ISO string in the visitor timezone for data-deal-countdown."""
        self.ensure_one()
        if not self.date_end:
            return ''
        dt_local = fields.Datetime.context_timestamp(self, self.date_end)
        return dt_local.isoformat()
