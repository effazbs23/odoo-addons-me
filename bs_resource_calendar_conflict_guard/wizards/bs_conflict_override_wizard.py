import json

from odoo import _, fields, models
from odoo.exceptions import AccessError


class BsConflictOverrideWizard(models.TransientModel):
    """Explicit "Book Anyway" confirmation for override-eligible users (spec section
    7.5 / 9). Never a silent bypass: the calendar.event create()/write() hook always
    redirects here instead of applying the change directly, and the change is only
    ever (re-)applied — and logged as 'overridden' — once this wizard's button is
    clicked.
    """
    _name = 'bs.conflict.override.wizard'
    _description = 'Booking Conflict Override Confirmation'

    mode = fields.Selection([('create', 'Create'), ('write', 'Write')], required=True)
    event_ids = fields.Many2many(
        'calendar.event', string='Events to Update',
        help='Set for write() overrides: the record(s) the original write() call targeted.')
    vals_json = fields.Text(
        required=True,
        help='JSON-encoded field values from the original create()/write() call, to be '
             're-applied verbatim once the user confirms.')
    conflict_summary = fields.Text(readonly=True)

    def action_book_anyway(self):
        self.ensure_one()
        if not self.env.user.has_group('bs_resource_calendar_conflict_guard.group_conflict_override'):
            raise AccessError(_('You do not have permission to override booking conflicts.'))
        payload = json.loads(self.vals_json)
        Event = self.env['calendar.event'].with_context(bs_conflict_override=True)
        if self.mode == 'create':
            Event.create(payload)
        else:
            self.event_ids.with_context(bs_conflict_override=True).write(payload)
        return {'type': 'ir.actions.act_window_close'}
