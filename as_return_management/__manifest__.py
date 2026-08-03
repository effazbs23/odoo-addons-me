{
    'name': 'Purchase Return Management',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Manage vendor returns against purchase orders with credit notes',
    'description': """
        Purchase Return Management
        ==========================
        * Vendor (purchase) return requests anchored on purchase orders
        * Return goods from the correct source location, lot/serial aware
        * Automatic vendor credit notes and return-to-vendor pickings
        * Approval workflow (draft, submitted, approved, processing, done)
        * Purchase return analysis and reporting
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'price': '28',
    'currency': 'USD',
    'depends': [
        'stock',
        'account',
        'purchase',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/email_template_data.xml',
        'views/vendor_return_views.xml',
        'views/return_dashboard_views.xml',
        'views/menu_views.xml',
        'report/return_report_template.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': [
        'static/description/banner.png',
        'static/description/logo.png',
    ],
}
