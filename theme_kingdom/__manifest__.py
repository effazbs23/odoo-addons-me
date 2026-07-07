{
    'name': 'Theme Kingdom',
    'summary': (
        'A premium, responsive Odoo theme, Odoo eCommerce theme, Odoo website theme, Odoo 19 theme, '
        'Odoo store theme, responsive Odoo theme, premium Odoo theme, Odoo shop theme, multipurpose '
        'eCommerce theme, Odoo storefront theme, Odoo website builder theme and Odoo 19 compatible '
        'theme, purpose-built as a megastore theme, electronics store theme, appliance store theme, '
        'multi-category retail theme, department store theme, supermarket theme, gadget store theme, '
        'furniture store theme, fashion store theme, grocery store theme, hypermarket theme and home '
        'appliances theme. Comes with mega menu, hero slider, category carousel, category dual '
        'carousel, sticky header, mobile bottom navigation, manufacturer logos, brand slider, promo '
        'banners, blog news section and service highlights, plus deal of the day, countdown timer, '
        'flash sale theme, best seller products, featured products, product carousel, product badges, '
        'product filters, related products and product tabs. Shop smarter with flyout cart, mini cart, '
        'wishlist, pricelist integration, loyalty promotions, bulk pricelist products and cart discount '
        'theme tools, built on drag and drop snippets, website builder blocks, no-code theme, '
        'customizable Odoo theme, easy setup theme, plug and play theme and ready to use theme '
        'foundations. Delivers responsive design, mobile friendly theme, modern UI theme, clean layout '
        'theme, fast loading theme, SEO friendly theme, conversion optimized theme, elegant design '
        'theme and professional theme quality, the theme to buy Odoo theme, best Odoo eCommerce theme, '
        'Odoo theme for electronics, Odoo theme for megastore, online store theme and retail theme '
        'shoppers choose. Runs on swiper carousel theme, category grid layout, CMS theme, Odoo '
        'snippets, OWL interactions, Bootstrap based theme, lightweight theme, fast performance theme, '
        'SEO optimized theme, mobile-first theme and cross-browser theme tech, powering product '
        'discovery, category navigation, discount theme, promotional theme, eCommerce homepage '
        'builder, shop by category, countdown sale banner, scheduled promotions, auto scroll carousel, '
        'upsell and cross-sell, trending products, responsive product grid, flash deals theme, '
        'multi-brand store theme and brand showcase theme features.'
    ),
    'description': '''
Kingdom Mega Store Theme
========================

Premium responsive Odoo eCommerce theme for megastores, electronics, appliances,
and multi-category retail businesses.

Features
--------
* Deal of the Day with countdown, scheduled start/end, pricelist & promotion integration
* Mega menu, hero slider, category carousels, featured & best-sale products
* Flyout cart, wishlist, mobile bottom navigation
* Manufacturer logos, promo banners, blog news, service highlights
* Website Builder snippets — drag and drop homepage blocks
* Odoo native pricelist and loyalty promotion engine for offers

Configuration
-------------
Website → Configuration → Deals of the Day, Featured Products, Best Sale Products.
Sales → Pricelists for offer pricing. eCommerce → Promotions for cart discounts.
    ''',
    'category': 'Theme/eCommerce',
    'version': '19.0.1.0',
    'author': 'ERP 23',
    'company': 'nopCommerce, Brainstation 23 PLC',
    'maintainer': 'ERP 23',
    'website': 'https://www.erp-23.com',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'website_sale',
        'website_sale_wishlist',
        'website_sale_loyalty',
        'website_blog',
        'auth_signup',
        'product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/product_public_category_access.xml',
        'data/deals_of_day_cron.xml',
        'views/assets.xml',
        'views/header_template.xml',
        'views/footer_template.xml',
        'views/product_category_views.xml',
        'views/flyout_cart_template.xml',
        'views/product_related_template.xml',
        'views/featured_products_views.xml',
        'views/bestsale_products_views.xml',
        'views/manufacturer_views.xml',
        'views/deals_of_day_views.xml',
        'views/pricelist_bulk_products_views.xml',
        'views/product_tab_views.xml',
        'views/snippets/s_hero_slider.xml',
        'views/snippets/s_category_slider.xml',
        'views/snippets/s_deal_of_the_day.xml',
        'views/snippets/s_promo_banners.xml',
        'views/snippets/s_promo_banner.xml',
        'views/snippets/s_blog_news.xml',
        'views/snippets/s_bestsale_products.xml',
        'views/snippets/s_featured_products.xml',
        'views/snippets/s_category_dual_carousels.xml',
        'views/snippets/s_product_carousel.xml',
        'views/snippets/s_manufacturers.xml',
        'views/snippets/s_service_highlights.xml',
        'views/snippets/snippet_list.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'theme_kingdom/static/src/css/bootstrap.min.css',
            'theme_kingdom/static/src/css/bootstrap-icons.min.css',
            'theme_kingdom/static/src/css/kingdom.css',
            'theme_kingdom/static/src/css/color.css',
            'theme_kingdom/static/src/css/swiper-bundle.min.css',
            'theme_kingdom/static/src/css/magnific-popup.css',
            'theme_kingdom/static/src/css/styles.css',
            'theme_kingdom/static/src/css/customCss.css',
            'theme_kingdom/static/src/css/category-grid.css',
            ('after', 'website_sale/static/src/js/cart_service.js', 'theme_kingdom/static/src/js/kingdom_cart_service_patch.js'),
            ('after', 'website_sale_wishlist/static/src/js/website_sale_wishlist_utils.js', 'theme_kingdom/static/src/js/kingdom_wishlist_utils_patch.js'),
            'theme_kingdom/static/src/interactions/kingdom_flyout_cart.js',
            'theme_kingdom/static/src/interactions/featured_product_card.js',
            'theme_kingdom/static/src/interactions/kingdom_live_snippet.js',
        ],
        'website.website_builder_assets': [
            'theme_kingdom/static/src/website_builder/**/*',
        ],
    },

    'images': [
        'static/description/kingdom_description.png',
        'static/description/kingdom_screenshot.gif',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'post_init_hook': 'post_init_hook',
    'pre_init_hook': 'pre_init_hook',
    'price': 0.0,
    'currency': 'USD',
}
