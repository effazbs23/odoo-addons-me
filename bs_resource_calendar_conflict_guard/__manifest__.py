{
    'name': 'Resource/Calendar Conflict Guard',
    'version': '19.0.1.0.0',
    'category': 'Productivity/Calendar',
    'summary': 'Block double-booked calendar events for employees and resources, with next-slot suggestions',
    'description': """
        Resource/Calendar Conflict Guard
        =================================
        * Real-time double-booking detection for calendar events (employees and/or resource.resource)
        * Suggested next-available slot when a conflict is found
        * Configurable buffer time around bookings
        * Override group with an explicit "Book Anyway" confirmation step
        * Conflict log for admin visibility
    """,
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'price': 0.00,
    'currency': 'USD',
    'depends': [
        'calendar',
        'resource',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/bs_calendar_conflict_log_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',
}
