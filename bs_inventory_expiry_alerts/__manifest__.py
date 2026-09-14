{
    'name': 'Perishable Inventory Expiry Alerts',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Cross-warehouse dashboard and proactive alerts for lots nearing expiry',
    'description': """
        Perishable Inventory Expiry Alerts
        ====================================
        * Cross-warehouse expiry dashboard grouped by product, warehouse and days-to-expiry bucket
        * Configurable alert thresholds per product category, with a global fallback default
        * Automatic activities for the responsible user when a lot crosses its alert threshold
        * Suggested action helper (markdown/promotion flag or internal transfer) for near-expiry stock
        * Expiry write-off assistant wrapping the standard scrap flow, with a scrapped-value report
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'price': 0.00,
    'currency': 'USD',
    'depends': [
        'product_expiry',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'wizards/stock_expiry_writeoff_wizard_views.xml',
        'views/stock_expiry_dashboard_line_views.xml',
        'views/product_category_views.xml',
        'views/stock_scrap_views.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            ('include', 'web.chartjs_lib'),
            'bs_inventory_expiry_alerts/static/src/js/expiry_dashboard.js',
            'bs_inventory_expiry_alerts/static/src/xml/expiry_dashboard.xml',
            'bs_inventory_expiry_alerts/static/src/scss/expiry_dashboard.scss',
        ],
    },
    'images': ['static/description/banner.gif'],
    'icon': '/bs_inventory_expiry_alerts/static/description/icon.png',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
