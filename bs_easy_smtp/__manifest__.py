{
    'name': "Easy SMTP Setup",
    'summary': "A guided wizard that picks the right SMTP settings and test-sends before saving.",
    'description': """
Easy SMTP Setup
===============
Guides admins through configuring outgoing email: pick a provider (Gmail,
Google Workspace, Office 365, Zoho, SES, SendGrid, Mailgun, or Custom) to
auto-fill the correct host/port/encryption, enter credentials, and send a
real test email before anything is saved. Failures are translated into
plain-language explanations instead of raw SMTP tracebacks.

Setup/validation layer only: zero changes to how Odoo actually sends mail.
""",
    'version': '19.0.1.0.0',
    'category': 'Technical/Email',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'application': False,
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/bs_easy_smtp_preset_data.xml',
        'views/bs_easy_smtp_wizard_views.xml',
    ],
    'icon': '/bs_easy_smtp/static/description/icon.png',
    'installable': True,
    'auto_install': False,
}
