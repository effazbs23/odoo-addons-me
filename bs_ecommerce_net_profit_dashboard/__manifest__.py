{
    'name': 'Omnichannel Net Profitability Dashboard',
    'version': '19.0.1.0.0',
    'summary': 'Consolidates multi-channel sales against true COGS, dynamic ad spends, and channel commissions.',
    'category': 'Sales',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['sale_management', 'stock', 'account'],
    'data': [
        'views/bs_sale_order_views.xml',
        'views/bs_ecom_profit_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_ecommerce_net_profit_dashboard/static/src/components/**/*',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'currency': 'USD',
    'price': 99.99,
    'images': [
        'static/description/banner.gif'
    ],
    'icon': 'bs_ecommerce_net_profit_dashboard/static/description/icon.png',
}
