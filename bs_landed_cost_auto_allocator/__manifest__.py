{
    'name': 'Landed Cost Auto-Allocator',
    'version': '19.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': "Automatically splits freight/duty/customs charges across a "
               "purchase order's lines by weight, volume, or value.",
    'description': """
Landed Cost Auto-Allocator
===========================
One-click allocation of freight, duty and customs charges across a receipt's
lines, built directly on top of core `stock_landed_costs`:

* One-click "Auto-Allocate" button on a Landed Cost: suggests an allocation
  method per cost line from reusable rule templates, runs a pre-flight
  data-quality check, then lets core compute the actual split.
* Reuses core's own `split_method` field on landed cost lines (Equal, By
  Quantity, By Current Cost, By Weight, By Volume) - no parallel allocation
  field or reimplemented split math.
* Rule templates ("always allocate DHL freight by weight") matched by
  vendor and/or cost-type product, with a documented priority order.
* Mixed allocation on the same record: freight by weight, duty by value,
  customs by quantity - each cost line keeps its own method.
* Allocation Preview: Weight/Volume/Value columns alongside the existing
  valuation adjustment lines, so the split can be sanity-checked before
  posting.
* Allocation audit trail: a human-readable formula breakdown stored per
  adjustment line, for finance review.

Extends `stock.landed.cost` / `stock.valuation.adjustment.lines` - it
automates the split calculation Odoo already lets you enter manually, it
does not replace the landed cost accounting flow itself.
""",
    'author': 'ERP23',
    'website': 'https://erp23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'depends': ['stock_landed_costs', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'views/landed_cost_allocation_rule_views.xml',
        'views/stock_landed_cost_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_landed_cost_auto_allocator/static/src/scss/landed_cost_auto_allocator.scss',
        ],
    },
    'icon': '/bs_landed_cost_auto_allocator/static/description/icon.png',
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'currency': 'USD',
    'price': 5.99,
}
