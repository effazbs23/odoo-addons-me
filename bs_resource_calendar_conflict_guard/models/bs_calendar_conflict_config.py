from odoo import api, fields, models


class BsCalendarConflictConfig(models.Model):
    """Singleton configuration for the conflict guard (spec section 6).

    There is normally exactly one active record; ``_get_config()`` is the
    single entry point every other part of the module uses to read it, so
    there is one place that owns the "find or create the singleton" logic.
    """
    _name = 'bs.calendar.conflict.config'
    _description = 'Calendar Conflict Guard Configuration'

    check_employees = fields.Boolean(
        string='Check Employees', default=True,
        help='Check for overlapping bookings on attendees who are internal users.')
    check_resources = fields.Boolean(
        string='Check Resources', default=True,
        help='Check for overlapping bookings on resource.resource records (meeting rooms, equipment).')
    buffer_minutes = fields.Integer(
        string='Buffer (minutes)', default=0,
        help='Minutes of turnaround time required before/after each booking on the same resource. '
             'Defaults to 0 (exact overlap only) so existing schedules are not affected on install.')
    active = fields.Boolean(
        string='Active', default=True,
        help='Global on/off switch for conflict checking.')

    @api.model
    def _get_config(self):
        """Return the singleton config record, creating it with defaults if missing.

        active_test=False is required here: this model has a field literally named
        'active' (the global on/off switch), and Odoo auto-injects an active=True
        filter into every search() on any model with such a field. Without disabling
        that, turning the switch off would make this method blind to its own record
        and silently recreate a fresh (active=True) one on the very next read —
        defeating the toggle entirely.
        """
        config = self.sudo().with_context(active_test=False).search([], limit=1, order='id asc')
        if not config:
            config = self.sudo().create({})
        return config
