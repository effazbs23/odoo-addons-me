{
    'name': 'Subcontractor-Owned Stock Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Manufacturing',
    'summary': 'Clear reporting split between company-owned and subcontractor-owned '
               'inventory sitting in the same subcontracting location.',
    'description': """
        Subcontractor-Owned Stock Dashboard
        * Main dashboard: company vs. subcontractor-owned stock at subcontracting
          locations, with a by-workcenter/vendor breakdown chart
        * Per-subcontractor breakdown: quantity and value held by each vendor
        * Aging report with configurable buckets
        * Value-at-risk report for finance/insurance
        * Drill-down into the underlying stock.quant / stock.move.line records
        * Optional overdue alert (activity or chatter message) per vendor
        * Purely read-only: no new stock-move logic, reads mrp_subcontracting's
          existing locations and stock.quant.owner_id as-is
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['mrp_subcontracting'],
    'data': [
        'security/ir.model.access.csv',
        'security/subcontracting_stock_security.xml',
        'data/ir_cron_data.xml',
        'views/subcontracting_stock_report_views.xml',
        'views/stock_drilldown_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'web.chartjs_lib'),
            'bs_subcontracting_stock_dashboard/static/src/scss/subcontracting_dashboard.scss',
            'bs_subcontracting_stock_dashboard/static/src/js/subcontracting_dashboard/subcontracting_dashboard.js',
            'bs_subcontracting_stock_dashboard/static/src/js/subcontracting_dashboard/subcontracting_dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 9.99,
    'images': ['static/description/banner.gif'],
    'icon': '/bs_subcontracting_stock_dashboard/static/description/icon.png',
}
