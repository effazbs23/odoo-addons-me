{
    'name': 'Manufacturing Finite Capacity Scheduler',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Drag-and-drop Gantt scheduler that prevents double-booking a '
               'workcenter and reschedules work orders against real capacity.',
    'description': """
Manufacturing Finite Capacity Scheduler
========================================
Plan work orders against the real, finite capacity of each workcenter:

* Drag-and-drop Gantt view of every work order, grouped by workcenter.
* Automatic conflict detection when two work orders overlap on the same
  workcenter beyond its configured capacity.
* One-click 'Auto-schedule' that places unscheduled work orders into the
  next available capacity slot, respecting manufacturing order due dates.
* Manufacturing order due-date risk indicator.

Requires Odoo Enterprise: the Gantt view type used for the scheduler is
provided by the Enterprise `web_gantt` module.
""",
    'author': 'ERP23',
    'website': 'https://www.erp-23.com/',
    'license': 'OPL-1',
    'depends': ['mrp', 'web_gantt'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mrp_auto_schedule_wizard_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_workcenter_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_finite_capacity_scheduler/static/src/scss/mrp_finite_capacity_scheduler.scss',
        ],
    },
    'icon': '/mrp_finite_capacity_scheduler/static/description/icon.png',
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
