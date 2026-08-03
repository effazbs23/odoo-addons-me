{
    'name': 'Return Management System',
    'version': '19.0.1.3.0',
    'category': 'Inventory/Inventory',
    'summary': 'Advanced Return and Replacement Management',
    'description': """
        Complete Return Management System
        ================================
        * Return Request Management
        * Product Replacement Handling
        * Integration with Invoice and Delivery
        * Automated Credit Notes and Receipts
        * Dashboard and Analytics
        * Comprehensive Reporting
    """,
    'author': 'Ayesha Siddika Suchi',
    'website': 'https://www.yourcompany.com',
    'depends': [
        'base',
        'stock',
        'account',
        'sale',
        'purchase',
        'mail',
        'portal',
        'cup_is_customer_is_vendor',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/email_template_data.xml',
        'views/return_request_views.xml',
        'views/gross_return_views.xml',
        'views/vendor_return_views.xml',
        'views/return_dashboard_views.xml',
        'views/menu_views.xml',
        'report/return_report_template.xml',
        'wizard/return_wizard_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'images': ['static/description/images/banner.png'],
}
