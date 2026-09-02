{
    'name': 'No Code Custom Field Builder (CE)',
    'version': '19.0.1.0.0',
    'category': 'Technical/Customization',
    'summary': 'Add a real custom field to any model through a guided wizard, no code required',
    'author': 'ERP23',
    'website': 'https://erp23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'depends': ['base', 'web', 'base_automation', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/bs_addfield_actions.xml',
        'views/bs_addfield_registry_views.xml',
        'views/bs_addfield_wizard_views.xml',
    ],
    'application': False,
    'installable': True,
    'currency': 'USD',
    'price': 0.00,
    'assets': {
        'web.assets_backend': [
            'bs_custom_field_builder/static/src/css/bs_addfield.css',
        ],
    },
}
