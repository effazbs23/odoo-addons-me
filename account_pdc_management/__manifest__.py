{
    'name': 'Post Dated Cheque Management',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Track post dated cheques, clear or bounce them, and recover bank charges from the customer',
    'description': """
Post Dated Cheque (PDC) Management
==================================

Handle post dated cheques end to end, starting from a normal customer or vendor
payment. No contract, no subscription, no third party module required.

* Flag any journal as a PDC journal and give it a holding account.
* Payments made in that journal are held in the PDC account instead of the bank
  until the cheque actually clears.
* Clear a cheque to move the money into the real bank account.
* Bounce a cheque to put the balance back on the customer, with the return
  reason and the bank return advice kept on the record.
* Redeposit a bounced cheque, and bounce it again if it fails a second time.
* Record the fee the bank charged you for the returned cheque, then recover it
  from the customer with a bank recovery invoice that can never exceed the fee
  you actually paid.

Everything is posted as ordinary journal entries, so the general ledger, the
partner ledger and the aged reports all stay correct.
""",
    'author': 'Brain Station 23',
    'website': 'https://www.brainstation-23.com',
    'support': 'erp23@brainstation-23.com',
    # Paid app on the Odoo App Store. The store only sells modules published under
    # the Odoo Proprietary License, so OPL-1 rather than LGPL-3. Full text in LICENSE.
    'license': 'OPL-1',
    'price': 5.00,
    'currency': 'USD',
    'depends': ['account'],
    'data': [
        'security/pdc_security.xml',
        'security/ir.model.access.csv',
        'data/pdc_sequence_data.xml',
        'wizard/pdc_clear_wizard_views.xml',
        'wizard/pdc_bounce_wizard_views.xml',
        'wizard/pdc_recovery_wizard_views.xml',
        'views/account_journal_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'views/pdc_bank_recovery_views.xml',
        'views/res_config_settings_views.xml',
        'report/pdc_report_actions.xml',
        'report/pdc_cheque_register_templates.xml',
        'views/pdc_menus.xml',
    ],
    'demo': ['demo/pdc_demo.xml'],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
