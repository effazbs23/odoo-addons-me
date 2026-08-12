# -*- coding: utf-8 -*-
import logging
import werkzeug
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import is_html_empty

_logger = logging.getLogger(__name__)

_KINGDOM_LIVE_SNIPPETS = {
    's_featured_products': 'theme_kingdom.s_featured_products',
    's_bestsale_products': 'theme_kingdom.s_bestsale_products',
    's_deal_of_the_day': 'theme_kingdom.s_deal_of_the_day',
    's_product_carousel': 'theme_kingdom.s_product_carousel',
    's_category_dual_carousels': 'theme_kingdom.s_category_dual_carousels',
    's_category_slider': 'theme_kingdom.s_category_slider',
    's_brands': 'theme_kingdom.s_brands',
    's_manufacturers': 'theme_kingdom.s_brands',
    's_coming_soon': 'theme_kingdom.s_coming_soon',
}


def sitemap_brands(env, rule, qs):
    """List active brands in the website sitemap."""
    Brand = env['kingdom.brand'].sudo()
    slug = env['ir.http']._slug
    for brand in Brand.search([('active', '=', True)]):
        yield {'loc': f'/brand/{slug(brand)}'}


class KingdomComingSoon(http.Controller):

    @http.route(
        '/coming-soon',
        type='http',
        auth='public',
        website=True,
        sitemap=True,
    )
    def coming_soon_page(self, **kwargs):
        website = request.website
        # Always allow designers; public only when enabled (or explicit preview).
        if (
            not website.kingdom_coming_soon_enabled
            and not request.env.user.has_group('website.group_website_designer')
        ):
            return request.redirect('/')
        return request.render(
            'theme_kingdom.coming_soon_page',
            {
                'website': website,
            },
        )


class WebsiteSaleBrand(WebsiteSale):
    """Shop filter + pretty URLs for Kingdom brands."""

    def _kingdom_parse_brand_id(self, post):
        """Accept ``brand`` (preferred) or legacy ``manufacturer`` query values."""
        for key in ('brand', 'manufacturer'):
            value = post.get(key)
            if value is None or value is False or value == '':
                continue
            if hasattr(value, 'id'):
                return int(value.id)
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return None

    def _get_search_options(self, category=None, attribute_value_dict=None, tags=None,
                            min_price=0.0, max_price=0.0, conversion_rate=1, **post):
        options = super()._get_search_options(
            category=category,
            attribute_value_dict=attribute_value_dict,
            tags=tags,
            min_price=min_price,
            max_price=max_price,
            conversion_rate=conversion_rate,
            **post,
        )
        brand_id = self._kingdom_parse_brand_id(post)
        if brand_id:
            options['kingdom_brand_id'] = brand_id
        return options

    def _shop_get_query_url_kwargs(self, search, min_price, max_price, order=None, tags=None, **kwargs):
        res = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, order=order, tags=tags, **kwargs
        )
        brand_id = self._kingdom_parse_brand_id(kwargs)
        if brand_id:
            res['brand'] = brand_id
        return res

    def _get_additional_shop_values(self, values, **kwargs):
        res = super()._get_additional_shop_values(values, **kwargs)
        Brand = request.env['kingdom.brand'].sudo()
        brand_id = self._kingdom_parse_brand_id(kwargs)
        kingdom_brand = Brand.browse(brand_id).exists() if brand_id else Brand.browse()
        res.update({
            'kingdom_brands': Brand.get_shop_filter_brands(request.website),
            'kingdom_brand': kingdom_brand[:1] if kingdom_brand else False,
        })
        return res

    @route()
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        # Redirect legacy /shop?manufacturer=ID (and /shop?brand=ID) to /brand/<slug>.
        path = request.httprequest.path.rstrip('/') or '/'
        brand_id = self._kingdom_parse_brand_id(post)
        if brand_id and (path == '/shop' or path.startswith('/shop/page/')):
            brand = request.env['kingdom.brand'].sudo().browse(brand_id).exists()
            if brand and brand.active:
                query = request.httprequest.query_string.decode()
                filtered = self._get_filtered_query_string(
                    query, keys_to_remove=['brand', 'manufacturer']
                )
                try:
                    page_num = int(page or 0)
                except (TypeError, ValueError):
                    page_num = 0
                target = brand.get_shop_url()
                if page_num > 1:
                    target = f'{target}/page/{page_num}'
                if filtered:
                    target = f'{target}?{filtered}'
                return request.redirect(target, code=301)
        return super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post,
        )

    @route(
        [
            '/brand',
            '/brand/page/<int:page>',
            '/brand/<model("kingdom.brand"):brand>',
            '/brand/<model("kingdom.brand"):brand>/page/<int:page>',
            '/shop/brand',
            '/shop/brand/page/<int:page>',
            '/shop/brand/<model("kingdom.brand"):brand>',
            '/shop/brand/<model("kingdom.brand"):brand>/page/<int:page>',
        ],
        type='http',
        auth='public',
        website=True,
        sitemap=sitemap_brands,
        handle_params_access_error=lambda e, **kwargs: NotFound.code,
    )
    def brand_shop(self, page=0, brand=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        """Shop listing filtered by brand — public Brand URL entry point."""
        if brand is not None and not brand.active:
            raise NotFound()
        if brand is not None:
            post = dict(post, brand=brand.id)
        return self.shop(
            page=page,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post,
        )


class ThemeKingdomSnippetController(http.Controller):

    def _render_flyout_cart_payload(self, order):
        currency = request.website.currency_id
        amount = order.amount_total if order else 0.0
        return {
            'html': request.env['ir.qweb']._render(
                'theme_kingdom.kingdom_flyout_cart_content',
                {'website_sale_order': order},
            ),
            'cart_quantity': order.cart_quantity if order else 0,
            'amount_total_formatted': currency.format(amount),
        }

    @http.route(
        '/theme_kingdom/cart/flyout',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        sitemap=False,
    )
    def render_flyout_cart(self):
        if not request.website.has_ecommerce_access():
            return self._render_flyout_cart_payload(request.env['sale.order'])

        try:
            order = request.cart
        except AccessError:
            return self._render_flyout_cart_payload(request.env['sale.order'])

        return self._render_flyout_cart_payload(order)

    @http.route(
        '/theme_kingdom/snippet/render',
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        sitemap=False,
        readonly=True,
    )
    def render_live_snippet(self, snippet_key):
        # Accept short keys (s_brands) and full keys (theme_kingdom.s_brands).
        key = (snippet_key or '').strip()
        if key.startswith('theme_kingdom.'):
            key = key[len('theme_kingdom.'):]
        template_key = _KINGDOM_LIVE_SNIPPETS.get(key)
        if not template_key and key in _KINGDOM_LIVE_SNIPPETS.values():
            template_key = key if key.startswith('theme_kingdom.') else f'theme_kingdom.{key}'
        if not template_key:
            # Unknown snippet — keep the baked markup instead of hard-failing the page.
            return False
        try:
            # Never inject editor branding into live HTML — if that markup is later
            # saved into a page, #wrap loses its own branding and Blocks are disabled.
            return request.env['ir.qweb'].with_context(
                inherit_branding=False,
                inherit_branding_auto=False,
            )._render(template_key)
        except Exception:
            # Missing/broken template (e.g. stale arch_fs under --dev=xml).
            _logger.warning(
                'theme_kingdom live snippet render failed for %s → %s',
                snippet_key,
                template_key,
                exc_info=True,
            )
            return False

    @http.route(
        [
            '/shop/quickview/<model("product.template"):product>',
            '/theme_kingdom/quickview/<model("product.template"):product>',
        ],
        type='jsonrpc',
        auth='public',
        methods=['POST'],
        website=True,
        sitemap=False,
        readonly=True,
    )
    def product_quickview(self, product, **kwargs):
        """Return Quick View modal HTML + product metadata for the shop grid."""
        website = request.website
        if not website.has_ecommerce_access():
            raise werkzeug.exceptions.Forbidden()

        product = product.with_context(display_default_code=False)
        if not product.exists() or not product.sale_ok:
            raise werkzeug.exceptions.NotFound()
        if not product.can_access_from_current_website():
            raise werkzeug.exceptions.NotFound()
        if not product.is_published and not request.env.user.has_group('website.group_website_designer'):
            raise werkzeug.exceptions.NotFound()

        combination = product._get_first_possible_combination()
        combination_info = product._get_combination_info(combination=combination, add_qty=1.0)
        product_variant = request.env['product.product'].browse(combination_info['product_id'])

        has_custom_attribute = any(
            ptav.is_custom
            for ptal in product.valid_product_template_attribute_line_ids
            for ptav in ptal.product_template_value_ids._only_active()
        )
        needs_full_page = product.type == 'combo' or has_custom_attribute

        description = product.description_sale or ''
        if product.description_ecommerce and not is_html_empty(product.description_ecommerce):
            description_html = product.description_ecommerce
        else:
            description_html = False

        html = request.env['ir.ui.view']._render_template(
            'theme_kingdom.product_quickview_content',
            {
                'website': website,
                'product': product,
                'product_variant': product_variant,
                'combination': combination,
                'combination_info': combination_info,
                'description': description,
                'description_html': description_html,
                'needs_full_page': needs_full_page,
                'can_add_to_cart': (
                    not needs_full_page
                    and combination_info.get('is_combination_possible', True)
                    and not combination_info.get('prevent_zero_price_sale')
                    and product._website_show_quick_add()
                ),
            },
        )
        return {
            'html': html,
            'product_id': combination_info['product_id'],
            'product_template_id': product.id,
            'product_type': product.type,
            'needs_full_page': needs_full_page,
            'website_url': product.website_url,
            'display_name': combination_info.get('display_name') or product.name,
        }
