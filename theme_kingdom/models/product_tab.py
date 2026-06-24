from odoo import api, fields, models


class KingdomProductTab(models.Model):
    _name = 'kingdom.product.tab'
    _inherit = ['kingdom.website.cache.mixin']
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

    @api.model
    def get_tab_by_type(self, tab_type):
        """First active tab for a given tab type (labels, carousels, menus)."""
        if not tab_type:
            return self.browse()
        return self.sudo().search(
            [('active', '=', True), ('tab_type', '=', tab_type)],
            order='sequence asc, id asc',
            limit=1,
        )

    @api.model
    def get_carousel_subtab_label(self, tab_type):
        """Display name for New Arrivals / Best Sellers sub-tabs from Product Tabs."""
        tab = self.get_tab_by_type(tab_type)
        if tab:
            return tab.name
        selection = dict(self._fields['tab_type'].selection)
        return selection.get(tab_type, tab_type)

    def _get_category(self):
        self.ensure_one()
        return self.sudo().category_id

    def _product_domain(self):
        self.ensure_one()
        domain = [('sale_ok', '=', True), ('is_published', '=', True)]
        category = self._get_category()
        if category:
            domain.append(('public_categ_ids', 'child_of', category.id))
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

    def get_products(self):
        """Products for this tab according to tab_type."""
        self.ensure_one()
        limit = self.product_limit or 16
        Product = self.env['product.template'].sudo()
        domain = self._product_domain()
        if self.tab_type == 'new_arrival':
            return self.get_new_arrival_products()
        if self.tab_type == 'best_seller':
            return self.get_best_seller_products()
        if self.tab_type == 'featured':
            return Product.search(
                domain,
                order='website_sequence desc, id desc',
                limit=limit,
            )
        if self.tab_type == 'on_sale':
            products = Product.search(domain, order='website_sequence desc, id desc', limit=limit * 3)
            return products.filtered(
                lambda p: p.compare_list_price and p.compare_list_price > p.list_price
            )[:limit]
        if self.tab_type == 'category':
            return self.get_new_arrival_products()
        return Product.browse()

    def get_menu_url(self):
        self.ensure_one()
        if self.feature_url and self.feature_url not in ('#', ''):
            return self.feature_url
        type_urls = {
            'new_arrival': '/shop?order=publish_date%20desc',
            'best_seller': '/shop?order=website_sequence%20desc',
            'featured': '/shop?order=website_sequence%20asc',
            'on_sale': '/shop',
        }
        if self.tab_type == 'category' and self.category_id:
            return self.category_id.website_url or '/shop'
        return type_urls.get(self.tab_type, '/shop')

    def get_feature_href(self):
        self.ensure_one()
        if self.feature_url and self.feature_url != '#':
            return self.feature_url
        category = self._get_category()
        if category:
            return category.website_url or '/shop'
        return '/shop'

    def get_feature_bg_url(self):
        self.ensure_one()
        if self.feature_image:
            return '/web/image/kingdom.product.tab/%s/feature_image' % self.id
        category = self._get_category()
        if category.image_1920:
            return '/web/image/product.public.category/%s/image_1920' % category.id
        return '/theme_kingdom/static/src/images/categories/cat-1.jpg'

    def get_feature_ribbon(self):
        self.ensure_one()
        return self.feature_label or self.name or 'Shop'