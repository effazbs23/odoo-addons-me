{
    'name': 'Manufacturing Intercompany Work Order Sync',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Auto-creates a manufacturing order in another company when a '
               'component is only produced there.',
    'description': """
Manufacturing Intercompany Work Order Sync
============================================
Auto-creates a manufacturing order in Company B when Company A's MO needs a
component only Company B produces -- beyond generic intercompany transfers:

* Mark any product as "Produced By Company" to flag it as manufactured by a
  different company within the same multi-company database.
* When a manufacturing order's raw-material shortage involves such a
  component, this module builds the intercompany purchase order on top of
  core `sale_purchase_inter_company_rules` and creates the follow-up
  manufacturing order in the producing company automatically.
* A status smart panel on the origin MO shows the live state and progress
  of the dependent manufacturing order (e.g. "Waiting on Company B -- 60%
  complete") instead of a generic stock shortage.
* Due-date exception alert when the supplying company's manufacturing order
  is forecast to finish later than the requesting MO needs it.
* A "Check Intercompany Supply" button lets a user manually trigger or retry
  the sync if the automatic check on confirmation did not fire.

IMPORTANT -- Same-database multi-company only: this module works by directly
querying and creating records across companies that live in the SAME Odoo
database (a standard multi-company setup). It does NOT synchronize
manufacturing orders across two separate Odoo instances/databases -- there is
no API/webhook bridge here, only in-database multi-company automation on top
of core intercompany sale/purchase rules. Do not install this expecting
cross-instance sync.
""",
    'author': 'ERP23',
    'website': 'https://www.erp-23.com/',
    'license': 'LGPL-3',
    'depends': ['mrp', 'sale', 'purchase', 'sale_purchase_inter_company_rules'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/mrp_production_views.xml',
        'views/mrp_production_intercompany_link_views.xml',
        'views/product_template_views.xml',
        'views/menus.xml',
    ],
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
