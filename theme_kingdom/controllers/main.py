# -*- coding: utf-8 -*-
import werkzeug

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

_KINGDOM_LIVE_SNIPPETS = {
    's_featured_products': 'theme_kingdom.s_featured_products',
    's_bestsale_products': 'theme_kingdom.s_bestsale_products',
    's_deal_of_the_day': 'theme_kingdom.s_deal_of_the_day',
    's_product_carousel': 'theme_kingdom.s_product_carousel',
    's_category_dual_carousels': 'theme_kingdom.s_category_dual_carousels',
    's_category_slider': 'theme_kingdom.s_category_slider',
    's_manufacturers': 'theme_kingdom.s_manufacturers',
}


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
