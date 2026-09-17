{
    'name': 'BS Supply Chain Lead Time & Bottleneck Dashboard',
    'version': '19.0.1.0.0',
    'summary': 'Tracks vendor delivery precision slip indexes, picking delays, and backorder impacts.',
    'category': 'Inventory',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['purchase', 'stock'],
    'data': [
        'views/bs_supply_chain_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_supply_chain_bottleneck_dashboard/static/src/components/**/*',
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
    'icon': 'bs_supply_chain_bottleneck_dashboard/static/description/icon.png',
}
