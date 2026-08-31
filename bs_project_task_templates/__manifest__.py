{
    'name': "Project Stage Task Templates",
    'summary': "Auto-create a checklist of tasks whenever a project or task enters a configured stage.",
    'description': """
Project Stage Task Templates
=============================
Define, once, a set of template tasks tied to a project stage or a task
stage. Whenever a project (or a task) moves into that stage, the module
automatically creates the associated checklist tasks -- with resolved
assignee, computed deadline, priority and tags -- with zero manual re-entry.

Includes idempotency control per template (always / first-time-only /
confirm-before-creating) and an audit trail linking every generated task
back to its template and triggering record.
""",
    'version': '19.0.1.0.0',
    'category': 'Project',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 0.00,
    'currency': 'USD',
    'application': False,
    'icon': '/bs_project_task_templates/static/description/icon.png',
    'images': [
        'static/description/banner.gif',
    ],
    'depends': ['project'],
    'data': [
        'security/ir.model.access.csv',
        'views/project_stage_task_template_views.xml',
        'views/project_task_type_views.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'wizards/project_stage_template_confirm_wizard_views.xml',
        'views/project_menus.xml',
    ],
}
