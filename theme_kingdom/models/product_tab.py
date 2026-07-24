# -*- coding: utf-8 -*-
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
        string='Product tabs snippet',
        default=False,
        help='Show as one column in the Category Dual Carousels snippet (max 2 active tabs). '
             'Each column shows category image, subcategory links, and New Arrivals / Best Sellers.',
    )
    show_in_product_carousel = fields.Boolean(
        string='Product carousel snippet',
        default=True,
        help='Use this tab in the Product Carousel snippet (New Arrivals / Best Sellers types).',
    )
    show_in_dynamic_tabs = fields.Boolean(
        string='Dynamic Product Tabs',
        default=True,
        help='Show this tab in the Dynamic Product Tabs website snippet. '
             'Tabs load products via AJAX when clicked.',
    )
    tab_type = fields.Selection([
        ('new_arrival', 'New Arrivals'),
        ('best_seller', 'Best Sellers'),
        ('featured', 'Featured'),
        ('on_sale', 'On Sale'),
        ('category', 'By Category'),
    ],
        string='Tab Type',
        required=True,
        default='new_arrival',
        help='How products are chosen when Product Source is Automatic.',
    )
    product_source = fields.Selection(
        [
            ('auto', 'Automatic (by Tab Type)'),
            ('manual', 'Manual selection'),
        ],
        string='Product Source',
        required=True,
        default='auto',
        help='Automatic: fill products from Tab Type rules. '
             'Manual: pick products yourself below.',
    )
    category_id = fields.Many2one(
        'product.public.category',
        string='Category',
        help='Used when Tab Type is By Category (automatic source).',
    )
    product_ids = fields.Many2many(
        'product.template',
        'kingdom_product_tab_product_rel',
        'tab_id',
        'product_id',
        string='Products',
        domain="[('sale_ok', '=', True)]",
        help='Products shown when Product Source is Manual. Drag to reorder is not supported; '
             'use Sequence on products or pick in preferred order.',
    )
    product_count = fields.Integer(
        string='Products',
        compute='_compute_product_count',
    )
    product_limit = fields.Integer(
        string='Product Limit',
        default=16,
        help='Max products to show for automatic tabs.',
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

    @api.depends('product_ids', 'product_source', 'tab_type', 'category_id', 'product_limit')
    def _compute_product_count(self):
        for tab in self:
            if tab.product_source == 'manual':
                tab.product_count = len(tab.product_ids)
            else:
                tab.product_count = len(tab.get_products())

    def action_view_products(self):
        self.ensure_one()
        products = self.get_products()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', products.ids)],
            'context': {'create': False},
        }

    @api.model
    def ensure_default_tabs(self):
        """Seed Featured / New Arrivals / Best Sellers (safe on install + upgrade)."""
        Tab = self.sudo()
        defaults = [
            {
                'name': 'New Arrivals',
                'tab_type': 'new_arrival',
                'show_in_header_menu': True,
                'show_in_product_carousel': True,
                'show_in_dynamic_tabs': True,
                'sequence': 10,
            },
            {
                'name': 'Best Sellers',
                'tab_type': 'best_seller',
                'show_in_header_menu': True,
                'show_in_product_carousel': True,
                'show_in_dynamic_tabs': True,
                'sequence': 20,
            },
            {
                'name': 'Featured',
                'tab_type': 'featured',
                'show_in_header_menu': False,
                'show_in_product_carousel': False,
                'show_in_dynamic_tabs': True,
                'sequence': 5,
            },
        ]
        for vals in defaults:
            existing = Tab.search([('tab_type', '=', vals['tab_type'])], limit=1)
            if not existing:
                Tab.create(vals)
            else:
                write_vals = {}
                if (
                    'show_in_header_menu' in existing._fields
                    and not existing.show_in_header_menu
                    and vals.get('show_in_header_menu')
                ):
                    write_vals['show_in_header_menu'] = True
                if not existing.show_in_dynamic_tabs and vals.get('show_in_dynamic_tabs'):
                    write_vals['show_in_dynamic_tabs'] = True
                if write_vals:
                    existing.write(write_vals)
        if hasattr(Tab, '_sync_header_menus'):
            Tab.search([])._sync_header_menus()
        return True

    @api.model
    def get_dynamic_tabs(self, limit=8):
        """Active tabs for the Dynamic Product Tabs snippet."""
        return self.sudo().search(
            [
                ('active', '=', True),
                ('show_in_dynamic_tabs', '=', True),
            ],
            order='sequence asc, id asc',
            limit=limit,
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
    def get_tab_by_type(self, tab_type, product_carousel=False):
        """First active tab for a given tab type (labels, carousels, menus)."""
        if not tab_type:
            return self.browse()
        domain = [('active', '=', True), ('tab_type', '=', tab_type)]
        if product_carousel:
            domain.append(('show_in_product_carousel', '=', True))
        return self.sudo().search(domain, order='sequence asc, id asc', limit=1)

    @api.model
    def get_product_carousel_tab(self, tab_type):
        """Tab for the Product Carousel snippet (QWeb-safe, no keyword args)."""
        return self.get_tab_by_type(tab_type, product_carousel=True)

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

    def _get_category_shop_url(self, category):
        if not category:
            return '/shop'
        return '/shop/category/%s' % category.id

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
        """Products for this tab according to product_source / tab_type."""
        self.ensure_one()
        Product = self.env['product.template'].sudo()
        limit = self.product_limit or 16

        if self.product_source == 'manual':
            # Keep configured order; only published/saleable products on website.
            return self.product_ids.filtered(
                lambda p: p.sale_ok and p.is_published
            )[:limit]

        domain = self._product_domain()
        if self.tab_type == 'new_arrival':
            return self.get_new_arrival_products()
        if self.tab_type == 'best_seller':
            return self.get_best_seller_products()
        if self.tab_type == 'featured':
            if 'featured.products' in self.env:
                featured = self.env['featured.products'].sudo().search([], limit=1)
                if featured and featured.product_tmpl_ids:
                    return featured.product_tmpl_ids.filtered_domain(domain)[:limit]
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
            return self._get_category_shop_url(self.category_id)
        return type_urls.get(self.tab_type, '/shop')

    def get_feature_href(self):
        self.ensure_one()
        if self.feature_url and self.feature_url != '#':
            return self.feature_url
        category = self._get_category()
        if category:
            return self._get_category_shop_url(category)
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

    def get_display_title(self):
        """Title shown on the product-tab picture overlay."""
        self.ensure_one()
        category = self._get_category()
        if category:
            return category.name
        return self.name or ''

    def get_subcategory_links(self, limit=6):
        """Child public categories for the tab sidebar links."""
        self.ensure_one()
        category = self._get_category()
        if not category:
            return self.env['product.public.category']
        children = self.env['product.public.category'].sudo().search(
            [('parent_id', '=', category.id)],
            order='sequence, name, id',
            limit=limit,
        )
        return children or category
