from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BsAddfieldRegistry(models.Model):
    _name = 'bs.addfield.registry'
    _description = 'Custom Fields Added (Add-a-Field Wizard Registry)'
    _inherit = ['mail.thread']
    _order = 'create_date desc'
    _rec_name = 'field_label'

    # Live links -- become empty once the underlying metadata is actually deleted
    # (state='deleted'), which is why the display fields below are stored snapshots
    # rather than related fields: this row is an audit log, and a log entry must stay
    # readable after what it refers to is gone.
    target_model_id = fields.Many2one('ir.model', string='Model Reference', ondelete='set null', readonly=True)
    field_id = fields.Many2one('ir.model.fields', string='Field Reference', ondelete='set null', readonly=True)
    view_id = fields.Many2one('ir.ui.view', string='View Inheritance', ondelete='set null', readonly=True)
    automation_id = fields.Many2one(
        'base.automation', string='Notification Automation', ondelete='set null', readonly=True)

    # Snapshots, set once at creation, independent of the live links above.
    model_name = fields.Char(string='Model (Technical)', readonly=True)
    model_label = fields.Char(string='Model', readonly=True)
    model_module = fields.Char(string='App', readonly=True)
    field_name = fields.Char(string='Field (Technical)', readonly=True)
    field_label = fields.Char(string='Field Name', readonly=True)
    field_type = fields.Char(string='Field Type', readonly=True)
    notebook_page = fields.Char(string='Tab', readonly=True)

    state = fields.Selection([
        ('active', 'Active'),
        ('disabled', 'Disabled'),
        ('deleted', 'Deleted'),
    ], default='active', required=True, tracking=True)
    created_by_wizard = fields.Boolean(default=True, readonly=True)
    has_data = fields.Boolean(
        string='Has Data', compute='_compute_has_data',
        help="Whether any record on the target model currently has a non-empty value for this field.")
    field_required = fields.Boolean(
        string='Required', compute='_compute_field_required', inverse='_inverse_field_required',
        tracking=True, help="Toggling this updates the underlying field directly; safe post-creation.")

    @api.depends('target_model_id', 'field_id', 'state')
    def _compute_has_data(self):
        for record in self:
            if record.state == 'deleted' or not record.field_id or not record.target_model_id.model:
                record.has_data = False
                continue
            Target = record.env[record.target_model_id.model].sudo()
            record.has_data = bool(
                Target.search_count([(record.field_id.name, '!=', False)], limit=1))

    @api.depends('field_id.required')
    def _compute_field_required(self):
        for record in self:
            record.field_required = bool(record.field_id.required)

    def _inverse_field_required(self):
        for record in self:
            if record.field_id:
                record.field_id.required = record.field_required

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # A blank record with no field_label is the throwaway placeholder that
            # Odoo auto-saves when "Launch Wizard" is clicked on a brand-new record
            # (any server-calling button forces a save first) -- action_launch_wizard
            # unlinks it immediately after, so it never needs a chatter entry.
            if record.field_label:
                record.message_post(body=_(
                    'Field "%(label)s" (%(name)s) added on %(model)s.',
                    label=record.field_label, name=record.field_name, model=record.model_label))
        return records

    def action_launch_wizard(self):
        """Bound to the "New" record's placeholder form (see the view): clicking it
        auto-saves this blank record first (standard Odoo behavior for any
        server-calling button on an unsaved record), so the first thing this does is
        discard that placeholder before handing off to the real wizard."""
        self.ensure_one()
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add a Field'),
            'res_model': 'bs.addfield.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_remove_wizard(self):
        self.ensure_one()
        if self.state == 'deleted':
            raise UserError(_('This field has already been deleted.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Remove Field'),
            'res_model': 'bs.addfield.remove.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_registry_id': self.id,
                'default_field_label': self.field_label,
                'default_model_label': self.model_label,
                'default_has_data': self.has_data,
                'default_has_automation': bool(self.automation_id),
            },
        }

    def action_disable_field(self):
        """No-warning path: only reachable from a button invisible when has_data is True."""
        self._set_enabled(False)

    def action_disable_field_confirmed(self):
        """Warning-accepted path: the button carries a `confirm` dialog in the view."""
        self._set_enabled(False)

    def action_enable_field(self):
        self._set_enabled(True)

    def _set_enabled(self, enabled):
        for record in self:
            if record.state == 'deleted':
                raise UserError(_('This field has been deleted and cannot be re-enabled.'))
            record.state = 'active' if enabled else 'disabled'
            if record.view_id:
                record.view_id.active = enabled
