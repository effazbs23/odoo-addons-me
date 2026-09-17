{
    'name': 'HR Burnout & Retention Risk Dashboard',
    'version': '19.0.1.0.0',
    'summary': 'Proactive burnout flags, disengagement tracking, and operational retention hazard indexes.',
    'category': 'Human Resources',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'depends': ['hr', 'hr_timesheet', 'hr_holidays', 'project'],
    'data': [
        'views/bs_hr_burnout_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_hr_burnout_dashboard/static/src/components/**/*',
        ],
    },
    'license': 'OPL-1',
    'installable': True,
    'application': True,
    'auto_install': False,
    'currency': 'USD',
    'price': 99.99,
    'images': [
        'static/description/banner.gif'
    ],
    'icon': 'bs_hr_burnout_dashboard/static/description/icon.png',
}
