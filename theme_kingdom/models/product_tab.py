# -*- coding: utf-8 -*-
from odoo import api, fields, models


class KingdomProductTab(models.Model):
    _name = 'kingdom.product.tab'
    _inherit = ['kingdom.website.cache.mixin']
    _description = 'Kingdom Product Tab'
    _order = 'id'

    name = fields.Char(
        string='Tab Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Technical order field (hidden). Records are ordered by id.',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    show_in_homepage = fields.Boolean(
        string='Dual carousel column',
        default=False,
        help='Technical flag synced from Show in = Dual Carousel.',
    )
    show_in_product_carousel = fields.Boolean(
        string='Product carousel snippet',
        default=False,
        help='Technical flag synced from Show in = Product Carousel.',
    )
    snippet_placement = fields.Selection(
        [
            ('none', 'None'),
            ('product_carousel', '1st Dual'),
            ('dual_carousel', '2nd Dual'),
        ],
        string='Show in',
        default='none',
        required=True,
        help='Internal placement. Prefer the Show in field on each menu form.',
    )
    # Dual Carousel menu form — static options (context selection is unreliable in OWL).
    dual_placement = fields.Selection(
        [
            ('none', 'None'),
            ('dual_carousel', 'Show in 2nd Dual'),
        ],
        string='Show in',
        compute='_compute_menu_placement',
        inverse='_inverse_dual_placement',
    )
    # Product Carousel menu form
    product_placement = fields.Selection(
        [
            ('none', 'None'),
            ('product_carousel', 'Show in 1st Dual'),
        ],
        string='Show in',
        compute='_compute_menu_placement',
        inverse='_inverse_product_placement',
    )

    @api.depends('snippet_placement')
    def _compute_menu_placement(self):
        for tab in self:
            tab.dual_placement = (
                'dual_carousel' if tab.snippet_placement == 'dual_carousel' else 'none'
            )
            tab.product_placement = (
                'product_carousel' if tab.snippet_placement == 'product_carousel' else 'none'
            )

    def _inverse_dual_placement(self):
        for tab in self:
            tab.snippet_placement = (
                'dual_carousel' if tab.dual_placement == 'dual_carousel' else 'none'
            )

    def _inverse_product_placement(self):
        for tab in self:
            tab.snippet_placement = (
                'product_carousel' if tab.product_placement == 'product_carousel' else 'none'
            )

    use_as_carousel_banner = fields.Boolean(
        string='Carousel left banner',
        default=False,
        help='Use this tab’s Feature Banner (image, label, URL) as the left promo '
             'in the Product Carousel. Only one tab should be enabled; if none, '
             'the first carousel tab is used.',
    )
    products_per_slide = fields.Integer(
        string='Products per slide',
        default=10,
        help='How many products per carousel slide (reference layout is 10 = 5×2). '
             'Taken from the banner tab, or the first Product Carousel tab.',
    )
    subtab_new_label = fields.Char(
        string='First tab label name',
        default='New Arrivals',
        help='Label for the first product tab inside Dual Carousel columns (default: New Arrivals).',
    )
    subtab_best_label = fields.Char(
        string='Second tab label name',
        default='Best Sellers',
        help='Label for the second product tab inside Dual Carousel columns (default: Best Sellers).',
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
        default=20,
        help='Max products loaded for this tab. Product Carousel also uses Products per slide.',
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

    def _sync_snippet_placement_vals(self, vals):
        """Keep Show in + legacy boolean flags in sync (one placement only)."""
        if 'snippet_placement' in vals:
            place = vals.get('snippet_placement') or 'none'
            vals['show_in_product_carousel'] = place == 'product_carousel'
            vals['show_in_homepage'] = place == 'dual_carousel'
            return vals
        product = vals.get('show_in_product_carousel')
        dual = vals.get('show_in_homepage')
        if product is None and dual is None:
            return vals
        # Boolean toggles from older UI / RPC — map to single placement.
        if dual:
            vals['snippet_placement'] = 'dual_carousel'
            vals['show_in_product_carousel'] = False
            vals['show_in_homepage'] = True
        elif product:
            vals['snippet_placement'] = 'product_carousel'
            vals['show_in_product_carousel'] = True
            vals['show_in_homepage'] = False
        else:
            # Explicit False on the flag being written.
            if product is False and dual is False:
                vals['snippet_placement'] = 'none'
            elif product is False and dual is None:
                vals.setdefault('snippet_placement', 'none')
            elif dual is False and product is None:
                vals.setdefault('snippet_placement', 'none')
        return vals

    def _ensure_single_carousel_banner(self):
        """Only one tab may own the Product Carousel left banner."""
        banners = self.filtered('use_as_carousel_banner')
        if not banners:
            return
        others = self.sudo().search([
            ('use_as_carousel_banner', '=', True),
            ('id', 'not in', banners.ids),
        ])
        if others:
            others.write({'use_as_carousel_banner': False})

    @api.model_create_multi
    def create(self, vals_list):
        synced = [self._sync_snippet_placement_vals(dict(vals)) for vals in vals_list]
        records = super().create(synced)
        records._ensure_single_carousel_banner()
        return records

    def write(self, vals):
        vals = self._sync_snippet_placement_vals(dict(vals))
        res = super().write(vals)
        if vals.get('use_as_carousel_banner'):
            self._ensure_single_carousel_banner()
        return res

    @api.model
    def _migrate_snippet_placement(self):
        """Fill snippet_placement from legacy boolean flags (upgrade-safe)."""
        for tab in self.sudo().search([]):
            if tab.show_in_homepage:
                desired = 'dual_carousel'
            elif tab.show_in_product_carousel:
                desired = 'product_carousel'
            else:
                desired = 'none'
            if tab.snippet_placement == desired:
                continue
            # Set all three so flags stay consistent without recursive sync surprises.
            models.Model.write(tab, {
                'snippet_placement': desired,
                'show_in_product_carousel': desired == 'product_carousel',
                'show_in_homepage': desired == 'dual_carousel',
            })
        return True

    @api.model
    def ensure_default_tabs(self):
        """Seed Featured / New Arrivals / Best Sellers (safe on install + upgrade)."""
        Tab = self.sudo()
        defaults = [
            {
                'name': 'New Arrivals',
                'tab_type': 'new_arrival',
                'show_in_header_menu': False,
                'snippet_placement': 'product_carousel',
                'use_as_carousel_banner': True,
                'sequence': 10,
            },
            {
                'name': 'Best Sellers',
                'tab_type': 'best_seller',
                'show_in_header_menu': False,
                'snippet_placement': 'product_carousel',
                'sequence': 20,
            },
            {
                'name': 'Featured',
                'tab_type': 'featured',
                'show_in_header_menu': False,
                'snippet_placement': 'none',
                'sequence': 5,
            },
        ]
        for vals in defaults:
            existing = Tab.search([('tab_type', '=', vals['tab_type'])], limit=1)
            if not existing:
                Tab.create(vals)
            else:
                write_vals = {}
                # Do not force Header menu entries — those duplicate Website menus
                # and stay English until translated separately.
                if (
                    vals.get('snippet_placement') == 'product_carousel'
                    and existing.snippet_placement == 'none'
                    and existing.tab_type in ('new_arrival', 'best_seller')
                ):
                    write_vals['snippet_placement'] = 'product_carousel'
                if write_vals:
                    existing.write(write_vals)
        # Older seeds forced Header menu entries for New Arrivals / Best Sellers,
        # which duplicated Website menus and left English clones after translate.
        legacy_header = Tab.search([('show_in_header_menu', '=', True)])
        if legacy_header:
            legacy_header.write({'show_in_header_menu': False})
        Tab._migrate_snippet_placement()
        # Prefer New Arrivals as banner when none is set.
        if not Tab.search([('use_as_carousel_banner', '=', True)], limit=1):
            banner = Tab.search([
                ('active', '=', True),
                ('show_in_product_carousel', '=', True),
            ], order='id asc', limit=1)
            if banner:
                banner.write({'use_as_carousel_banner': True})
        if hasattr(Tab, '_sync_header_menus'):
            Tab.search([])._sync_header_menus()
        return True

    @api.model
    def get_website_dual_carousel_tabs(self, limit=2):
        """Up to two active tabs for the category dual carousel snippet."""
        return self.sudo().search(
            [
                ('active', '=', True),
                ('show_in_homepage', '=', True),
            ],
            order='id asc',
            limit=limit,
        )

    @api.model
    def get_product_carousel_tabs(self):
        """All active tabs enabled for the Product Carousel (ordered)."""
        return self.sudo().search(
            [
                ('active', '=', True),
                ('show_in_product_carousel', '=', True),
            ],
            order='id asc',
        )

    @api.model
    def get_product_carousel_banner_tab(self):
        """Tab whose Feature Banner drives the Product Carousel left promo."""
        banner = self.sudo().search(
            [
                ('active', '=', True),
                ('use_as_carousel_banner', '=', True),
            ],
            order='id asc',
            limit=1,
        )
        if banner:
            return banner
        return self.get_product_carousel_tabs()[:1]

    @api.model
    def get_product_carousel_per_slide(self):
        """Products per slide for Product Carousel (from banner / first tab)."""
        tab = self.get_product_carousel_banner_tab()
        if not tab:
            tab = self.get_product_carousel_tabs()[:1]
        per = tab.products_per_slide if tab else 10
        return max(1, min(int(per or 10), 40))

    @api.model
    def get_tab_by_type(self, tab_type, product_carousel=False):
        """First active tab for a given tab type (labels, carousels, menus)."""
        if not tab_type:
            return self.browse()
        domain = [('active', '=', True), ('tab_type', '=', tab_type)]
        if product_carousel:
            domain.append(('show_in_product_carousel', '=', True))
        return self.sudo().search(domain, order='id asc', limit=1)

    @api.model
    def get_product_carousel_tab(self, tab_type):
        """Tab for the Product Carousel snippet (QWeb-safe, no keyword args)."""
        return self.get_tab_by_type(tab_type, product_carousel=True)

    @api.model
    def get_carousel_subtab_label(self, tab_type):
        """Display name for New Arrivals / Best Sellers sub-tabs from Product Tabs."""
        Tab = self.sudo()
        # Prefer Product Carousel tabs (user renames those for global labels).
        tab = Tab.search(
            [
                ('active', '=', True),
                ('tab_type', '=', tab_type),
                ('show_in_product_carousel', '=', True),
            ],
            order='id asc',
            limit=1,
        )
        if not tab:
            tab = Tab.search(
                [('active', '=', True), ('tab_type', '=', tab_type)],
                order='write_date desc, id desc',
                limit=1,
            )
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
        """Title on the Dual Carousel banner — Tab Name first so renames show up."""
        self.ensure_one()
        if self.name:
            return self.name
        category = self._get_category()
        return category.name if category else ''

    def get_dual_new_label(self):
        """New Arrivals label for this Dual column (or global fallback)."""
        self.ensure_one()
        return (self.subtab_new_label or '').strip() or self.sudo().get_carousel_subtab_label('new_arrival')

    def get_dual_best_label(self):
        """Best Sellers label for this Dual column (or global fallback)."""
        self.ensure_one()
        return (self.subtab_best_label or '').strip() or self.sudo().get_carousel_subtab_label('best_seller')
    def get_subcategory_links(self, limit=6):
        """Child public categories for the dual-carousel banner links."""
        self.ensure_one()
        category = self._get_category()
        if not category:
            return self.env['product.public.category']
        return self.env['product.public.category'].sudo().search(
            [('parent_id', '=', category.id)],
            order='sequence, name, id',
            limit=limit or 6,
        )
