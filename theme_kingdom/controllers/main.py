# -*- coding: utf-8 -*-
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import is_html_empty

_KINGDOM_LIVE_SNIPPETS = {
    's_featured_products': 'theme_kingdom.s_featured_products',
    's_bestsale_products': 'theme_kingdom.s_bestsale_products',
    's_deal_of_the_day': 'theme_kingdom.s_deal_of_the_day',
    's_product_carousel': 'theme_kingdom.s_product_carousel',
    's_category_dual_carousels': 'theme_kingdom.s_category_dual_carousels',
    's_category_slider': 'theme_kingdom.s_category_slider',
    's_manufacturers': 'theme_kingdom.s_manufacturers',
    's_coming_soon': 'theme_kingdom.s_coming_soon',
}


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

class WebsiteSaleManufacturer(WebsiteSale):
    """Filter /shop by manufacturer assigned on product.template."""

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
        manufacturer = post.get('manufacturer')
        if manufacturer:
            try:
                options['kingdom_manufacturer_id'] = int(manufacturer)
            except (TypeError, ValueError):
                pass
        return options

    def _shop_get_query_url_kwargs(self, search, min_price, max_price, order=None, tags=None, **kwargs):
        res = super()._shop_get_query_url_kwargs(
            search, min_price, max_price, order=order, tags=tags, **kwargs
        )
        manufacturer = kwargs.get('manufacturer')
        if manufacturer:
            res['manufacturer'] = manufacturer
        return res


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
        template_key = _KINGDOM_LIVE_SNIPPETS.get(snippet_key)
        if not template_key:
            raise werkzeug.exceptions.NotFound()
        # Never inject editor branding into live HTML — if that markup is later
        # saved into a page, #wrap loses its own branding and Blocks are disabled.
        return request.env['ir.qweb'].with_context(
            inherit_branding=False,
            inherit_branding_auto=False,
        )._render(template_key)

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
