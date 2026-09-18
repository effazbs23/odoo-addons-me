{
    'name': 'Lot Recall Report',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'One-click recall report tracing a lot/serial number to every '
               'customer, order, and shipment it touched.',
    'description': """
Lot Recall Report
==================
Generate an audit-ready recall report for any lot or serial number in one
click:

* Forward trace - every customer, sales order and delivery that received
  stock containing the lot.
* Backward trace - the vendor(s), purchase order(s) and/or manufacturing
  order that fed into the lot.
* Multi-lot batch mode for an entire production run.
* Print-ready PDF and XLSX export, with a searchable recall log for
  compliance and audit purposes.
""",
    'author': 'ERP23',
    'website': 'https://erp23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'depends': ['stock', 'sale_stock', 'mrp', 'purchase', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'report/lot_recall_report_paperformat.xml',
        'report/lot_recall_report_templates.xml',
        'report/lot_recall_report_actions.xml',
        'views/lot_recall_report_views.xml',
        'views/lot_recall_report_line_views.xml',
        'views/stock_lot_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_lot_recall_report/static/src/scss/lot_recall_report.scss',
        ],
    },
    'icon': '/bs_lot_recall_report/static/description/icon.png',
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'currency': 'USD',
    'price': 5.99,
}
