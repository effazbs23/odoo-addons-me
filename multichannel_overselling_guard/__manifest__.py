{
    'name': 'Overselling Guard for Multi-Channel Retail',
    'version': '17.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Real-time stock reservation checks between POS, eCommerce, and B2B sales.',
    'description': """
Overselling Guard for Multi-Channel Retail
============================================
Real-time stock reservation checks between POS, eCommerce, and B2B sales to
stop the same unit being sold twice:

* Configurable 'reserved buffer' per product/warehouse, held back from sale
  to absorb timing gaps between channels.
* Lightweight soft-reservation model that puts a short-lived hold on stock
  the moment a website/B2B order line is added or a POS order syncs to the
  backend, so one channel's in-progress cart is respected by the others.
* Oversell alert: when two channels still manage to sell past what was
  available, the second confirmation is flagged for manual review instead
  of being silently accepted or blocked.
* Reserved Buffer, Reserved Open Orders, Sellable Now and Oversell Detected
  dashboard views for store/warehouse managers.
* Opt in per product category so guarding only applies to the fast-moving,
  limited-stock SKUs that actually need it.

Important behavior note: the oversell safety net *flags* a suspicious
confirmation for manual review, it never blocks or reverses the sale.

See CHANGELOG.md for scoping notes: this release implements the mechanism
as a backend model plus native dashboard views. True sub-second POS-register
and website-cart JavaScript hooks are out of scope for this release (no live
browser/POS session available to build and test them against) and are
flagged there as a v2 item.
""",
    'author': 'ERP23',
    'website': 'https://www.erp-23.com/',
    'license': 'LGPL-3',
    'depends': ['sale', 'website_sale', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/stock_soft_reservation_views.xml',
        'views/multichannel_stock_buffer_views.xml',
        'views/multichannel_oversell_alert_views.xml',
        'views/multichannel_sellable_report_views.xml',
        'views/product_category_views.xml',
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
