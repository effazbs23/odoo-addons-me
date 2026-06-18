from odoo import api, fields, models


class KingdomProductTab(models.Model):
    _name = 'kingdom.product.tab'
    _description = 'Kingdom Product Tab'
    _order = 'sequence, id'

    name = fields.Char(
        string='Tab Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    show_in_homepage = fields.Boolean(
        string='Category dual carousel',
        default=False,
        help='Show as one column in the homepage category dual carousel snippet (max 2).',
    )
    tab_type = fields.Selection([
        ('new_arrival', 'New Arrivals'),
        ('best_seller', 'Best Sellers'),
        ('featured',    'Featured'),
        ('on_sale',     'On Sale'),
        ('category',    'By Category'),
    ],
        string='Tab Type',
        required=True,
        default='new_arrival',
    )
    category_id = fields.Many2one(
        'product.public.category',
        string='Category',
        help='Used when Tab Type is By Category',
    )
    product_limit = fields.Integer(
        string='Product Limit',
        default=16,
    )
    feature_image = fields.Image(
        string='Feature Image',
        max_width=500,
        max_height=500,
    )
    feature_label = fields.Char(
        string='Feature Label',
        default='Shop Now',
    )
    feature_url = fields.Char(
        string='Feature URL',
        default='/shop',
    )

    @api.model
    def get_website_dual_carousel_tabs(self, limit=2):
        """Up to two active tabs for the category dual carousel snippet."""
        return self.sudo().search(
            [
                ('active', '=', True),
                ('show_in_homepage', '=', True),
            ],
            order='sequence asc, id asc',
            limit=limit,
        )

    def _product_domain(self):
        self.ensure_one()
        domain = [('sale_ok', '=', True), ('is_published', '=', True)]
        if self.category_id:
            domain.append(('public_categ_ids', 'child_of', self.category_id.id))
        return domain

    def get_new_arrival_products(self):
        self.ensure_one()
        return self.env['product.template'].sudo().search(
            self._product_domain(),
            order='create_date desc',
            limit=self.product_limit or 16,
        )

    def get_best_seller_products(self):
        self.ensure_one()
        return self.env['product.template'].sudo().search(
            self._product_domain(),
            order='website_sequence desc, id desc',
            limit=self.product_limit or 16,
        )

    def get_feature_href(self):
        self.ensure_one()
        if self.feature_url and self.feature_url != '#':
            return self.feature_url
        if self.category_id:
            return self.category_id.website_url or '/shop'
        return '/shop'

    def get_feature_bg_url(self):
        self.ensure_one()
        if self.feature_image:
            return '/web/image/kingdom.product.tab/%s/feature_image' % self.id
        if self.category_id.image_1920:
            return '/web/image/product.public.category/%s/image_1920' % self.category_id.id
        return '/theme_kingdom/static/src/images/categories/cat-1.jpg'

    def get_feature_ribbon(self):
        self.ensure_one()
        return self.feature_label or self.name or 'Shop'