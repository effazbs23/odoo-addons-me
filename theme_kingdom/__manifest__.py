{
    'name': 'Theme Kingdom',
    'summary': 'Premium Megastore E-Commerce Theme for Odoo',
    'description': '''
        Kingdom is a modern, fully responsive Odoo website theme designed for 
        megastores and e-commerce businesses. Features include mega menu, 
        announcement bar, product carousels, quick view, wishlist, and more.
    ''',
    'category': 'Theme/eCommerce',
    'version': '19.0.1.0',
    'author': 'ERP 23',
    'company': 'nopCommerce, Brainstation 23 PLC',
    'maintainer': 'ERP 23',
    'website': 'https://www.erp-23.com',
    'depends': [
        'website',
        'website_sale',
        'website_sale_wishlist',
        'website_blog',
        'auth_signup',
        'product'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/header_template.xml',
        'views/footer_template.xml',
        'views/product_category_views.xml',
        'views/product_tab_views.xml',
        'views/featured_products_views.xml',
        'views/bestsale_products_views.xml',
        'views/manufacturer_views.xml',
        'views/deals_of_day_views.xml',
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
           
        ],
    },

    'images': [
        # 'static/description/banner.gif',
    ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0.0,
    'currency': 'USD',
}
