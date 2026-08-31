{
    'name': "Simple Invoice",
    'summary': "A toggleable simplified invoicing view for non-accountant users.",
    'description': """
Simple Invoice
==============
Gives admins a single toggle that switches a company (or specific users)
into a simplified invoicing experience: a reduced menu, a stripped-down
invoice form, and one clear status funnel (Draft -> Sent -> Paid ->
Overdue) -- with zero changes to the underlying accounting data model.
Accountants can flip it off any time and see the full Accounting app
exactly as before.

Pure visibility/UX layer: no new workflow, no new state machine, no
changes to tax calculation, chart of accounts, or journal structure.
""",
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'application': False,
    'depends': ['account'],
    'post_init_hook': '_post_init_enable_simple_invoicing',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/bs_simple_invoice_dashboard_views.xml',
    ],
    'icon': '/bs_simple_invoice/static/description/icon.png',
    'images': [
        'static/description/banner.gif',
    ],
    'installable': True,
    'auto_install': False,
}
