from odoo import fields, models


class BsCalendarConflictLog(models.Model):
    """Audit trail of every blocked or overridden double-booking attempt (spec section 6)."""
    _name = 'bs.calendar.conflict.log'
    _description = 'Calendar Conflict Guard Log'
    _order = 'create_date desc'

    event_id = fields.Many2one(
        'calendar.event', string='Event', ondelete='cascade',
        help='The event that triggered the conflict check. Empty for a blocked create() attempt: '
             'the event that would have been created never persists, so there is nothing to link to.')
    conflicting_event_id = fields.Many2one(
        'calendar.event', string='Conflicting Event', ondelete='set null',
        help='The existing event it conflicted with.')
    resource_type = fields.Selection(
        [('employee', 'Employee'), ('resource', 'Resource')],
        string='Resource Type', required=True)
    # NOTE: targets res.partner rather than hr.employee for the 'employee' type — this module
    # depends only on calendar/resource (not hr, per spec depends list), and "employee" conflicts
    # here are checked against calendar attendees (res.partner), not hr.employee records.
    resource_ref = fields.Reference(
        [('res.partner', 'Contact'), ('resource.resource', 'Resource')],
        string='Resource')
    action_taken = fields.Selection(
        [('blocked', 'Blocked'), ('overridden', 'Overridden')],
        string='Action Taken', required=True)
    overridden_by = fields.Many2one(
        'res.users', string='Overridden By',
        help='Set only when action_taken is "overridden".')
