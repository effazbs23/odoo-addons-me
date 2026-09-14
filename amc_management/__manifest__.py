{
    'name': 'AMC Management',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Purchase',
    'summary': 'Annual Maintenance Contracts on Purchase: sign the order, accrue the cost monthly, prove each service visit and bill the vendor by milestone',
    'description': """
Annual Maintenance Contract (AMC) Management
============================================

Turns an AMC purchase order into a tracked maintenance contract with its own
service calendar and accrual accounting.

* Flag a purchase order as an AMC order. Its lines then accept service products only.
* **Mark as Signed** on the confirmed order raises one contract per line and splits
  each contract into service periods according to the chosen frequency.
* Monthly provision journal entries are generated per order in draft
  (Dr AMC Expense / Cr AMC Provision), with catch-up folding for late signatures.
* Close each service period as Done, Partially Serviced or Expired. The last two book
  a draft reversal entry for the days that were not serviced.
* Raise milestone vendor bills against the accrued provision, driven by the payment
  term of the order, with sequential-billing control and service report attachments.
* AMC Schedule report (XLSX): a twelve month provision grid per contract and year.
    """,
    'author': 'Brain Station 23',
    'website': 'https://www.brainstation-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 5.0,
    'currency': 'USD',
    'depends': ['account', 'purchase'],
    'data': [
        'security/amc_security.xml',
        'security/ir.model.access.csv',
        'data/amc_mail_template_data.xml',
        'data/ir_cron_data.xml',
        'report/amc_schedule_report.xml',
        'views/amc_site_views.xml',
        'views/amc_contract_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'views/product_category_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/amc_service_period_wizard_views.xml',
        'wizard/amc_vendor_bill_wizard_views.xml',
        'wizard/amc_schedule_report_wizard_views.xml',
        'views/amc_menus.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/images/02_amc_purchase_order.png',
        'static/description/images/04_amc_contract_form.png',
        'static/description/images/09_provision_entry_lines.png',
    ],
    'assets': {
        'web.assets_backend': [
            'amc_management/static/src/js/xlsx_report_action.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
