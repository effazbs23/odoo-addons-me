# -*- coding: utf-8 -*-
{
    'name': 'Inventory Valuation Details',
    'version': '19.0.2.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Per-product valuation, cost method & expected journal entries on every stock operation',
    'description': """
        Inventory Valuation Details
        =======================
        Odoo 19 removed per-move valuation layers (SVL). This module brings full
        valuation transparency back — directly on receipts, deliveries, scraps and manufacturing orders.

        What you get:
        -------------
        * 💰 Valuation smart button on every Transfer (receipt, delivery, return, dropship) showing the total stock value for that operation
        * 📄 Journal Entry smart button — links directly to the accounting entry
        * 🏭 Smart buttons on Manufacturing Orders:
            - Valuation
        * 🗑️ Scrap Valuation smart button on Scrap Orders
        * Per-product breakdown: quantity, unit cost, total value, cost method
        * Expected journal entry (DR / CR) per move — using Odoo 19's actual
          accounts (Stock Valuation, Stock Variation, Expense / COGS, WIP)
          even when no per-move journal entry is created
        * Distinguishes: Perpetual vs Periodic valuation, FIFO / AVCO / Standard
        * Correctly skips Services and untracked Consumables (no valuation)
        * Covers: Purchase receipts, Sales deliveries, Customer/Vendor returns,
          Dropship, Scraps, Unbuild orders, Landed costs,
          MRP components & finished goods
        * Global report: Inventory → Reporting → Stock Valuations
          (filter/group by product, category, cost method, valuation method, date)

    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'price': 25.00,
    'currency': 'USD',
    'depends': ['stock_account', 'mrp_account'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_move_valuation_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_scrap_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

