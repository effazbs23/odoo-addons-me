{
    'name': 'CRM Win Rate & Lost Reason Analytics',
    'version': '19.0.1.0.0',
    'category': 'CRM',
    'summary': 'Mandatory, categorized lost-reason capture plus a native win-rate '
               'and stage drop-off dashboard for the CRM pipeline',
    'description': """
        CRM Lost Reason + Win Rate Dashboard

        * Structured lost-reason categories (Pricing, Timing, Competitor,
          No Budget, No Response, Not a Fit, Other) on crm.lost.reason
        * Mandatory reason capture when marking a lead lost
        * Optional free-text lost note for drill-down context
        * Win Rate Dashboard: overall, by reason category, by salesperson,
          by lead source
        * Stage drop-off analysis (bar chart, closest 19.0 equivalent to a
          funnel)
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
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 0.00,
}
