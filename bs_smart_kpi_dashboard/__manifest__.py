{
    'name': 'Smart KPI Dashboard',
    'category': 'Productivity',
    'summary': 'Type a KPI request in plain English, get a live chart — no external AI API, no data leaves your server.',
    'version': '19.0.1.0.0',
    'license': 'OPL-1',
    'price': 29,
    'currency': 'USD',
    'icon': '/bs_smart_kpi_dashboard/static/description/icon.png',
    'images': [
        'static/description/banner.gif',
    ],
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    # All four business apps are intentionally hard dependencies for this
    # SKU: data/allowlist_data.xml seeds one ready-to-use allow-list entry
    # per app (Sales, Invoicing, CRM, Inventory) so the dashboard has
    # something chartable out of the box on every one of them. This is a
    # deliberate "batteries included" trade-off for a $29 productivity
    # add-on, not an oversight — see README.md's "Requirements" section
    # for the customer-facing version of this note.
    'depends': ['base', 'web', 'sale', 'account', 'crm', 'stock'],
    'data': [
        'security/ai_dashboard_security.xml',
        'security/ir.model.access.csv',
        'data/allowlist_data.xml',
        'data/synonym_data.xml',
        'data/ir_cron_data.xml',
        'views/ai_dashboard_allowlist_views.xml',
        'views/ai_dashboard_synonym_views.xml',
        'views/ai_dashboard_unmatched_phrase_views.xml',
        'views/ai_dashboard_tile_views.xml',
        'views/res_config_settings_views.xml',
        'views/ai_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'web.chartjs_lib'),
            'bs_smart_kpi_dashboard/static/src/js/**/*',
            'bs_smart_kpi_dashboard/static/src/xml/**/*',
            'bs_smart_kpi_dashboard/static/src/css/**/*',
        ],
    },
    'installable': True,
    'application': True,
    'uninstall_hook': 'uninstall_hook',
}
