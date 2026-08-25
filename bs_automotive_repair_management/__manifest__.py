{
    'name': 'Automotive Service & Repair Order Management',
    'version': '19.0.1.0.0',
    'category': 'Services/Field Service',
    'summary': 'Job-card workflow for auto repair shops: vehicles, labor, '
               'parts with warranty tracking, negotiated pricing, capacity-'
               'based pickup estimates, handover documentation and warranty '
               'claims',
    'description': """
        Automotive Service & Repair Order Management

        * Vehicle intake tied to customer records (res.partner)
        * Repair order job-card workflow (draft -> estimate -> approved ->
          in_progress -> quality_check -> ready -> invoiced -> closed)
        * Labor lines per technician, optional service catalog lookup
        * Parts consumption as real stock moves, with lot/serial-based
          warranty tracking reusing stock.lot
        * Dual-input negotiated pricing (percentage or fixed price) with
          per-salesperson discount caps enforced server-side
        * Capacity-based expected pickup time using resource.calendar
        * Vehicle check-in / check-out inspections with photo/video and
          itemized belongings, treated as immutable once recorded
        * Warranty claims that reuse the same repair order workflow
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': [
        'base',
        'mail',
        'sale',
        'stock',
        'account',
        'resource',
        'hr',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/product_data.xml',
        'data/stock_data.xml',
        'data/mail_template_data.xml',
        'views/automotive_service_catalog_views.xml',
        'views/automotive_workshop_resource_views.xml',
        'views/automotive_repair_order_views.xml',
        'views/automotive_vehicle_views.xml',
        'views/automotive_vehicle_inspection_views.xml',
        'views/automotive_warranty_claim_views.xml',
        'views/automotive_deletion_request_views.xml',
        'views/hr_employee_stats_views.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_automotive_repair_management/static/src/scss/automotive_repair_kanban.scss',
            'bs_automotive_repair_management/static/src/js/menu_badges/menu_badges.js',
            'bs_automotive_repair_management/static/src/js/menu_badges/menu_badges.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
    'currency': 'USD',
    'price': 99.99,
    'images': [
        'static/description/banner.gif'
    ],
    'icon' : 'static/description/icon.png',
}
