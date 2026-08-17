# -*- coding: utf-8 -*-
{
    'name': 'Lessor Lease Accounting',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Automated accounting for lessor lease contracts',
    'description': """
Lessor Lease Accounting Automation
===================================
This module extends lessor_lease_scheduling with accounting features:
* Down payment invoicing
* Initial recognition journal entries (Gross Method/Hire-Purchase)
* Periodic accounting automation
* GL account configuration
* Complete lease lifecycle accounting

Note: Net Method (IFRS 16) support is currently under development.
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'license': 'LGPL-3',
    'price': 249.00,
    'currency': 'USD',
    'support': 'erp23@brainstation-23.com',
    'depends': [
        'lessor_lease_scheduling',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/menus.xml',
        'views/res_config_settings_views.xml',
        'views/lessor_lease_contract_views.xml',
        'views/lessor_lease_dashboard_views.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'company': 'ERP23',
}
