{
    'name': 'Lot Traceability Lookup',
    'category': 'Manufacturing/Inventory',
    'summary': 'Search a lot/serial number, get a plain-language backward + forward traceability chain, exportable as a PDF for audits and recalls.',
    'description': """
        Lot Traceability Lookup
        ========================
        * Single search box (with barcode-scan support) for any lot/serial number
        * Backward trace: source lots, components, and originating vendor receipts
        * Forward trace: consuming manufacturing orders, resulting lots, and customer deliveries
        * Plain-language summary generated above the detailed chain, no AI/LLM involved
        * Nested chain view with wide-fanout ("...and 47 more") and depth-cap handling
        * One-click PDF export for audits and recalls, with every export logged
        * Purely read/report layer over Odoo's native lot/serial data - no new tracking mechanism
    """,
    'version': '19.0.1.0.0',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'report/bs_trace_export_report.xml',
        'views/bs_trace_lookup_views.xml',
        'views/bs_trace_export_log_views.xml',
        'views/bs_trace_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_lot_traceability_lookup/static/src/css/bs_trace_lookup.css',
        ],
    },
    'images': ['static/description/assets/main_screenshot.png'],
    'icon': '/bs_lot_traceability_lookup/static/description/icon.png',
    'installable': True,
    'application': True,
}
