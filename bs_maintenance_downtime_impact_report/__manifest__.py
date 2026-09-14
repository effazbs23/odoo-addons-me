{
    'name': 'Maintenance-to-Manufacturing Downtime Impact Report',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Maintenance',
    'summary': 'Correlates logged equipment downtime against missed manufacturing order due '
               'dates, connecting Maintenance and Manufacturing reporting.',
    'description': """
        Maintenance-to-Manufacturing Downtime Impact Report
        * Downtime impact report: which manufacturing orders were scheduled on
          affected equipment/workcenters during a maintenance window
        * Missed-due-date correlation for late manufacturing orders
        * Cost-of-downtime estimate (workcenter cost/hour x downtime hours)
        * Equipment reliability ranking (pivot/graph) to prioritize
          preventive maintenance budget
        * Exportable summary (XLSX) for monthly operations review
        * Purely analytical/read-only: no change to how maintenance requests
          or work orders are created or scheduled
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['maintenance', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'security/maintenance_downtime_security.xml',
        'views/mrp_workcenter_views.xml',
        'views/maintenance_downtime_report_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            ('include', 'web.chartjs_lib'),
            'bs_maintenance_downtime_impact_report/static/src/scss/downtime_dashboard.scss',
            'bs_maintenance_downtime_impact_report/static/src/js/downtime_dashboard/downtime_dashboard.js',
            'bs_maintenance_downtime_impact_report/static/src/js/downtime_dashboard/downtime_dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 0.00,
    'images': ['static/description/banner.gif'],
    'icon': '/bs_maintenance_downtime_impact_report/static/description/icon.png',
}
