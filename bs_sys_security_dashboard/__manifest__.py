{
    'name': 'BS Server Health & Security Command Center',
    'version': '19.0.1.0.0',
    'summary': 'Live session manager, security telemetry, and database slow-query monitoring dashboard.',
    'category': 'Technical',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['base', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/bs_sys_security_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_sys_security_dashboard/static/src/components/**/*',
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
    'icon': 'bs_sys_security_dashboard/static/description/icon.png',
}
