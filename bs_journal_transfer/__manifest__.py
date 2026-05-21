{
    'name': 'Journal Transfer',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Transfer amounts between journals with bank statement line creation',
    'description': """
        Journal Transfer
        ================
        * Transfer amounts between source and destination journals
        * Automatic bank statement line creation
        * Auto-reconciliation with Internal Transfer model
        * Full Accounting Integration
    """,
    'author': 'Ispahani',
    'depends': ['accountant'],
    'data': [
        'security/bs_journal_transfer_security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/bs_journal_transfer_views.xml',
        'views/bs_journal_transfer_menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
