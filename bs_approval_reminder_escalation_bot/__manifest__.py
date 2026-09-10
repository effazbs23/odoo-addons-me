{
    'name': 'Approval Reminder & Escalation Bot',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Automation',
    'summary': 'Automated reminders and escalation for pending approvals on Purchase Orders, Expenses, and Time Off',
    'description': """
Automatically remind approvers when approvals have been pending past configurable,
business-day-aware thresholds. Escalates to a backup approver at a second threshold.
Covers Purchase Orders, Expenses, and Time Off requests.
    """,
    'author': 'ERP23',
    'website': 'https://erp23.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'resource', 'purchase', 'hr_expense', 'hr_holidays'],
    'data': [
        'data/bs_approval_reminder_activity_type.xml',
        'data/ir_cron_approval_reminder.xml',
        'security/ir.model.access.csv',
        'views/bs_approval_reminder_config_views.xml',
        'views/bs_approval_reminder_log_views.xml',
        'views/bs_approval_reminder_snooze_wizard_views.xml',
        'views/mail_activity_views.xml',
        'views/bs_approval_reminder_dashboard_views.xml',
        'views/purchase_order_views.xml',
        'views/hr_expense_views.xml',
        'views/hr_leave_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_approval_reminder_escalation_bot/static/src/js/dashboard_action.js',
            'bs_approval_reminder_escalation_bot/static/src/xml/dashboard_templates.xml',
            'bs_approval_reminder_escalation_bot/static/src/css/dashboard.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
