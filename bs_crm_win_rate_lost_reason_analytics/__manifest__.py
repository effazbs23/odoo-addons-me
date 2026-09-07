{
    'name': 'CRM Win Rate & Lost Reason Analytics',
    'version': '19.0.1.0.0',
    'category': 'CRM',
    'summary': 'Mandatory, categorized lost-reason capture plus a visual win-rate '
               'and stage drop-off dashboard for the CRM pipeline',
    'description': """
        CRM Lost Reason + Win Rate Dashboard

        * Structured lost-reason categories (Pricing, Timing, Competitor,
          No Budget, No Response, Not a Fit, Other) on crm.lost.reason
        * Mandatory reason capture when marking a lead lost
        * Optional free-text lost note for drill-down context
        * Win Rate Dashboard: a single-page visual overview (KPI cards,
          lost-reasons donut, salesperson win rate, stage drop-off funnel,
          leads by source), filterable by date range/team/salesperson
        * Native pivot/graph views kept alongside it for raw data
          drill-down and export
        * Backfills categories and reporting fields for leads/reasons that
          existed before this module was installed
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['crm'],
    'data': [
        'data/crm_lost_reason_category_data.xml',
        'views/crm_lost_reason_views.xml',
        'wizard/crm_lead_lost_views.xml',
        'views/crm_lead_dashboard_views.xml',
        'views/crm_win_rate_dashboard_action.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_crm_win_rate_lost_reason_analytics/static/src/scss/win_rate_dashboard.scss',
            'bs_crm_win_rate_lost_reason_analytics/static/src/js/win_rate_dashboard/win_rate_dashboard.js',
            'bs_crm_win_rate_lost_reason_analytics/static/src/js/win_rate_dashboard/win_rate_dashboard.xml',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 0.00,
    'images': ['static/description/banner.gif'],
    'icon': 'static/description/icon.png',
}
