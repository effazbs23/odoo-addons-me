# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomDealsOfDay(models.Model):
    _name = 'kingdom.deals.of.day'
    _description = 'Kingdom Deal of the Day'
    _order = 'sequence, id'

    name = fields.Char(
        string='Deal Title',
        required=True,
        help='Shown on the homepage deal block (e.g. Cooking pan, Weekend Sale).',
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
        string='Deal Pricelist',
        required=True,
        ondelete='restrict',
        default=lambda self: self.env['product.pricelist'].search(
            [('company_id', 'in', [False, self.env.company.id])],
            limit=1,
        ),
        help='Deal products and prices are loaded from this pricelist '
             '(rules on products, variants, or categories).',
    )
    product_limit = fields.Integer(
        string='Max Products',
        default=24,
        help='Maximum number of products shown from the pricelist.',
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

    @api.model
    def _pricelist_item_is_active(self, item, now=None):
        now = now or fields.Datetime.now()
        if item.date_start and item.date_start > now:
            return False
        if item.date_end and item.date_end < now:
            return False
        return True

    def _templates_from_pricelist_item(self, item):
        """Return published product templates referenced by a pricelist rule."""
        ProductTemplate = self.env['product.template']
        if item.applied_on == '1_product' and item.product_tmpl_id:
            return item.product_tmpl_id
        if item.applied_on == '0_product_variant' and item.product_id:
            return item.product_id.product_tmpl_id
        if item.applied_on == '2_product_category' and item.categ_id:
            return ProductTemplate.search([
                ('sale_ok', '=', True),
                ('website_published', '=', True),
                ('categ_id', 'child_of', item.categ_id.id),
            ])
        return ProductTemplate.browse()

    def _get_offer_products(self):
        """Products shown in the deal carousel (from the deal pricelist)."""
        self.ensure_one()
        if not self.pricelist_id:
            return self.env['product.template']

        now = fields.Datetime.now()
        limit = self.product_limit or 24
        seen = set()
        products = self.env['product.template'].browse()

        for item in self.pricelist_id.item_ids:
            if not self._pricelist_item_is_active(item, now):
                continue
            for template in self._templates_from_pricelist_item(item):
                if template.id in seen:
                    continue
                if not template.sale_ok or not template.website_published:
                    continue
                seen.add(template.id)
                products |= template
                if len(products) >= limit:
                    return products
        return products

    def get_deal_pricelist(self):
        """Pricelist used to price deal products on the storefront."""
        self.ensure_one()
        return self.pricelist_id

    @api.model
    def _website_deal_domain(self):
        now = fields.Datetime.now()
        return [
            ('active', '=', True),
            ('date_start', '<=', now),
            ('date_end', '>=', now),
            ('pricelist_id', '!=', False),
        ]

    @api.model
    def get_preview_deal(self):
        """Fallback deal for the website editor when no offer is currently active."""
        return self.sudo().search(
            [('pricelist_id', '!=', False)],
            order='sequence asc, id asc',
            limit=1,
        )

    @api.model
    def get_website_deal(self):
        """Active deal for the storefront (date range + weekday)."""
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
