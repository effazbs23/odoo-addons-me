# -*- coding: utf-8 -*-
{
    'name': 'Lessor Lease Scheduling',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Manage lessor finance lease contracts with automated schedule generation',
    'description': """
Lessor Lease Contract & Schedule Management
============================================
This module provides comprehensive lease contract management for lessors:
* Finance lease contract creation and management
* Automated amortization schedule generation
* Gross Method (Hire-Purchase) accounting support
* Precise financial calculations matching Excel models
* Multi-currency support
* Asset integration

Note: Net Method (IFRS 16) support is currently under development.
    """,
    'author': 'Brain Station 23',
    'website': 'https://brainstation-23.com',
    'license': 'LGPL-3',
    'price': 199.00,
    'currency': 'USD',
    'depends': [
        'base',
        'account',
        'mail',
        'web',
    ],
    'data': [
        'security/lessor_lease_security.xml',
        'security/ir.model.access.csv',
        'data/lessor_lease_sequence.xml',
        'views/lessor_lease_contract_views.xml',
        'views/lessor_lease_schedule_line_views.xml',
        'views/lessor_lease_menu.xml',
    ],
    'demo': [
        'demo/lessor_lease_demo.xml',
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'external_dependencies': {
        'python': [],
    },
    "support": "erp23@brainstation-23.com",
}
