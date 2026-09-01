# -*- coding: utf-8 -*-
{
    'name': "WhatsApp/SMS Order & Invoice Notifier",
    'summary': "Automatic WhatsApp/SMS notifications on order confirm, shipment, invoice post, payment and overdue.",
    'description': """
WhatsApp/SMS Order & Invoice Notifier
======================================
Sends automatic, templated WhatsApp and/or SMS notifications to customers
when key order and invoice events happen: order confirmed, delivery
shipped, invoice posted, payment received, and invoice overdue (once).

Includes a full delivery log with manual resend, phone number validation,
and a hard non-blocking guarantee: a notification failure never blocks or
rolls back the underlying business transaction.
""",
    'version': '19.0.1.0.0',
    'category': 'Sales/Communication',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'application': False,
    'depends': ['sale', 'account', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/bs_notify_event_template_data.xml',
        'data/ir_cron_overdue_check.xml',
        'views/bs_notify_gateway_config_views.xml',
        'views/bs_notify_event_template_views.xml',
        'views/bs_notify_log_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/bs_notify_menus.xml',
    ],
    'icon': '/bs_whatsapp_sms_order_invoice_notifier/static/description/icon.png',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
}
