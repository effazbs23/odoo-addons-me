# -*- coding: utf-8 -*-
#############################################################################
#
#    erp23
#
#    Copyright (C) 2026-TODAY erp23(<https://www.erp-23.com/>)
#    Author: erp23(<https://www.erp-23.com/>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import fields, http
from odoo.http import request
from datetime import datetime
from odoo.tools.mail import html2plaintext
from odoo.tools.misc import format_amount

class NaturalFoodController(http.Controller):

    # New Arrivals Route only
    @http.route(['/shop/new-arrivals'], type='http', auth='public', website=True)
    def new_arrivals(self, **kwargs):
        try:
            new_arrival_products = request.env['product.template'].sudo().search(
                [
                    ('is_new_arrival', '=', True),
                    ('is_published', '=', True),
                    ('sale_ok', '=', True),
                ],
                order='create_date desc',
                limit=12
            )
        except Exception:
            new_arrival_products = request.env['product.template'].sudo().search(
                [
                    ('is_published', '=', True),
                    ('sale_ok', '=', True),
                ],
                order='create_date desc',
                limit=12
            )

        try:
            wishlist_enabled = request.env['ir.module.module'].sudo().search_count(
                [
                    ('name', '=', 'website_sale_wishlist'),
                    ('state', '=', 'installed'),
                ]
            ) > 0
        except Exception:
            wishlist_enabled = False

        return request.render('natural_foods.naturalfood_new_arrival', {
            'new_arrival_products': new_arrival_products,
            'section_title': 'New Arrivals',
            'section_subtitle': 'Fresh products this week',
            'wishlist_enabled': wishlist_enabled,
        })

    # Shop by Category Route only
    @http.route(['/shop/categories'], type='http', auth='public', website=True)
    def shop_by_category(self, **kwargs):
        categories = request.env['product.public.category'].sudo().search(
            [('website_published', '=', True)]
        )

        return request.render('natural_foods.naturalfood_shop_by_category', {
            'categories': categories,
            'section_title': 'Shop by Category',
        })



class CustomWebsiteSale(WebsiteSale):
    @http.route(
        [
            '/shop',
            '/shop/page/<int:page>',
            '/shop/category/<model("product.public.category"):category>',
            '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        ],
        type='http',
        auth='public',
        website=True,
    )
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, tags='', **post):
        # Recover gracefully from previously stored string timestamps.
        raw_time = request.session.get('website_sale_pricelist_time')
        if isinstance(raw_time, str):
            try:
                request.session['website_sale_pricelist_time'] = float(raw_time)
            except (TypeError, ValueError):
                request.session.pop('website_sale_pricelist_time', None)
        return super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            tags=tags,
            **post
        )

    def _prepare_product_values(self, product, category, **kwargs):
        values = super()._prepare_product_values(product, category, **kwargs)

        related_products = product.alternative_product_ids.filtered(
            lambda related_product: related_product.is_published and related_product.sale_ok
        )

        if not related_products and product.public_categ_ids:
            related_products = request.env['product.template'].search(
                [
                    ('id', '!=', product.id),
                    ('is_published', '=', True),
                    ('sale_ok', '=', True),
                    ('public_categ_ids', 'in', product.public_categ_ids.ids),
                ],
                limit=4,
            )
        else:
            related_products = related_products[:4]

        values.update({
            'related_products': related_products[:4],
            'product_sku': values['product_variant'].default_code or product.default_code,
        })
        return values


    @http.route('/shop/set_pricelist', type='json', auth='public', website=True)
    def set_pricelist(self, pricelist_id, **kwargs):
        request.session['website_sale_current_pl'] = int(pricelist_id)
        pl = request.env['product.pricelist'].sudo().browse(int(pricelist_id))
        return {
            'success': True,
            'currency_symbol': pl.currency_id.symbol,
            'currency_name': pl.currency_id.name,
        }

    @http.route('/shop/set_currency', type='json', auth='public', website=True)
    def set_currency(self, currency_id, **kwargs):
        currency = request.env['res.currency'].sudo().browse(int(currency_id))
        if not currency.exists() or not currency.active:
            return {'success': False, 'error': 'Invalid currency'}
        pricelist = self._get_or_create_currency_pricelist(currency)
        self._apply_pricelist(pricelist=pricelist)
        request.session['website_sale_pricelist_time'] = datetime.timestamp(datetime.now())
        return {'success': True}

    @http.route('/shop/set_currency/<int:currency_id>', type='http', auth='public', website=True, sitemap=False)
    def set_currency_http(self, currency_id, **kwargs):
        currency = request.env['res.currency'].sudo().browse(int(currency_id))
        if currency.exists() and currency.active:
            pricelist = self._get_or_create_currency_pricelist(currency)
            self._apply_pricelist(pricelist=pricelist)
            request.session['website_sale_pricelist_time'] = datetime.timestamp(datetime.now())
        redirect_url = request.httprequest.referrer or '/shop'
        return request.redirect(redirect_url)

    def _get_or_create_currency_pricelist(self, currency):
        website = request.website
        ProductPricelist = request.env['product.pricelist'].sudo()
        generated_name = '%s Website Pricelist' % currency.name
        domain = [('currency_id', '=', currency.id)] + ProductPricelist._get_website_pricelists_domain(website)
        pricelist = ProductPricelist.search(
            domain,
            order='website_id desc, selectable desc, id asc',
            limit=1,
        )
        if not pricelist:
            # Create a selectable website pricelist for this currency.
            # Use a global "sales price" formula rule so Odoo converts amounts
            # using currency rates instead of keeping the same numeric value.
            base_pricelist = request.pricelist
            pricelist = ProductPricelist.create({
                'name': generated_name,
                'currency_id': currency.id,
                'selectable': True,
                'website_id': website.id,
                'company_id': website.company_id.id,
                'item_ids': [(0, 0, {
                    'applied_on': '3_global',
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'price_discount': 0.0,
                })],
            })
        elif (
            pricelist.website_id == website
            and pricelist.name == generated_name
            and pricelist.item_ids
        ):
            # Repair previously auto-generated pricelists created with the old
            # rule so currency changes actually convert amounts.
            global_items = pricelist.item_ids.filtered(lambda item: item.applied_on == '3_global')
            if global_items:
                global_items.write({
                    'compute_price': 'formula',
                    'base': 'list_price',
                    'base_pricelist_id': False,
                    'price_discount': 0.0,
                })
        return pricelist

    @http.route('/shop/wishlist/get_count', type='json', auth='public', website=True)
    def get_wishlist_count(self):
        if request.website.has_ecommerce_access():
            return len(request.env['product.wishlist'].current())
        return 0

    @http.route('/shop/cart/get_count', type='json', auth='public', website=True)
    def get_cart_count(self):
        order = request.cart
        return order.cart_quantity if order else 0

    @http.route('/shop/cart/dropdown_data', type='json', auth='public', website=True, csrf=False)
    def get_cart_dropdown_data(self):
        order = request.cart
        if not order:
            return {
                'items': [],
                'item_count': 0,
                'total': 0.0,
                'total_display': '$0.00',
            }

        currency = order.currency_id
        items = []
        for line in order.website_order_line:
            image_url = '/web/image/product.product/%s/image_128' % line.product_id.id
            items.append({
                'line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.product_id.display_name,
                'quantity': line.product_uom_qty,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_subtotal_display': '%s%.2f' % (currency.symbol or '$', line.price_subtotal),
                'image_url': image_url,
            })

        return {
            'items': items,
            'item_count': order.cart_quantity,
            'total': order.amount_total,
            'total_display': '%s%.2f' % (currency.symbol or '$', order.amount_total),
        }

    @http.route('/shop/cart/remove_line', type='json', auth='public', website=True, csrf=False)
    def remove_cart_line(self, line_id):
        order = request.cart
        if order:
            try:
                target_line_id = int(line_id)
            except (TypeError, ValueError):
                return self.get_cart_dropdown_data()
            line = order.website_order_line.filtered(lambda l: l.id == target_line_id)
            if line:
                line.unlink()
        return self.get_cart_dropdown_data()


class DealsOfDayController(http.Controller):

    @http.route('/deals/of/day', type='json', auth='public', website=True)
    def deals_of_day(self):
        deal = request.env['natural.deals.of.day'].sudo().search(
            [('is_active', '=', True)],
            limit=1,
            order='sequence asc'
        )

        products = deal.product_tmpl_ids if deal else []

        return {
            'deal': deal,
            'products': products,
            'end_time': deal.deal_end_time if deal else False
        }


class QuickViewController(http.Controller):

    @http.route('/quick_view/data/<int:product_id>', type='json', auth='public', website=True)
    def quick_view_data(self, product_id):
        product = request.env['product.template'].sudo().browse(product_id).exists()
        website = request.website
        if not product or not product.sale_ok or not product.is_published:
            return {'error': 'Product not available'}

        pricelist = (
            request.session.get('website_sale_current_pl')
            and request.env['product.pricelist'].sudo().browse(
                int(request.session.get('website_sale_current_pl'))
            )
        ) or website._get_and_cache_current_pricelist()
        currency = (
            pricelist.currency_id
            if pricelist and pricelist.exists()
            else request.env.company.currency_id
        )

        contextual_product = (
            product.with_context(pricelist=pricelist.id)
            if pricelist and pricelist.exists()
            else product
        )
        price = contextual_product._get_contextual_price()
        list_price = contextual_product.list_price
        variant_id = product._get_first_possible_variant_id()
        short_description = html2plaintext(product.description_sale or product.description or '').strip()
        order = request.cart
        cart_quantity = 0
        if order and variant_id:
            cart_line = order.website_order_line.filtered(lambda line: line.product_id.id == variant_id)[:1]
            cart_quantity = int(cart_line.product_uom_qty) if cart_line else 0

        return {
            'product_id': product.id,
            'product_variant_id': variant_id,
            'product_type': product.type,
            'name': product.name,
            'category': product.categ_id.name or '',
            'description': short_description[:280],
            'image_url': '/web/image/product.template/%s/image_512' % product.id,
            'price': price,
            'price_display': format_amount(request.env, price, currency),
            'list_price': list_price,
            'list_price_display': format_amount(request.env, list_price, currency),
            'has_discount': list_price > price,
            'currency_symbol': currency.symbol or '',
            'product_url': '/shop/%s' % request.env['ir.http']._slug(product),
            'cart_quantity': cart_quantity,
            'can_add_to_cart': bool(variant_id and website.has_ecommerce_access()),
        }
