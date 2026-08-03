{
    'name': 'Petty Cash Management',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Complete Petty Cash Management with Accounting Integration',
    'description': """
        Petty Cash Management System
        =============================
        * Cash Receive - Company provides cash to petty cashier
        * Cash Request - Employee requests petty cash
        * Advance Payment - Advance given for future expenses
        * Settlement - Employee submits bills and settles advance
        * Full Accounting Integration
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'price': 50,
    'currency': 'USD',
    'depends': ['base', 'account', 'hr', 'hr_expense', 'mail', 'portal', 'website'],
    'images': [
        'static/description/banner.gif',
        'static/description/logo.png',
    ],
    'data': [
        'security/petty_cash_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/analytic_cost_center_data.xml',
        'data/dashboard_data.xml',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml',
        'views/petty_cash_dashboard_views.xml',
        'views/petty_cash_request_views.xml',
        'views/petty_cash_advance_views.xml',
        'views/petty_cash_settlement_views.xml',
        'views/portal_menu.xml',
        'templates/portal_cash_request_form.xml',
        'templates/portal_my_cash_requests.xml',
        'templates/portal_cash_request_detail.xml',
        'reports/petty_cash_reports.xml',
        'views/petty_cash_menus.xml',

    ],
    'demo': [
        'demo/demo_comprehensive.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'petty_cash/static/lib/chart.js/chart.umd.min.js',
            'petty_cash/static/src/components/**/*.js',
            'petty_cash/static/src/components/**/*.xml',
            'petty_cash/static/src/scss/**/*.scss',
        ],
        'web.assets_frontend': [
            'petty_cash/static/src/js/cash_request_form.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
