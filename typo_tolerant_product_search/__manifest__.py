{
    'name': 'Typo-Tolerant Product Search',
    'version': '19.0.1.0.0',
    'category': 'Website/eCommerce',
    'summary': 'Multi-word fuzzy fallback, configurable sensitivity and a search-miss log for eCommerce product search',
    'author': 'ERP23',
    'website': 'https://erp23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'depends': ['website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/website_sale_search_results_templates.xml',
        'views/search_fuzzy_log_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'typo_tolerant_product_search/static/src/js/fuzzy_click_tracker.js',
        ],
    },
    'application': False,
    'installable': True,
    'currency': 'USD',
    'price': 0.00,
}
