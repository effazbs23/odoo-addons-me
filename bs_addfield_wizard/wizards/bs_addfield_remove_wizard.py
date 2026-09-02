from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BsAddfieldRemoveWizard(models.TransientModel):
    _name = 'bs.addfield.remove.wizard'
    _description = 'Remove Custom Field'

    registry_id = fields.Many2one('bs.addfield.registry', required=True, readonly=True)
    field_label = fields.Char(related='registry_id.field_id.field_description', readonly=True)
    model_name = fields.Char(related='registry_id.target_model_id.name', readonly=True)
    has_data = fields.Boolean(related='registry_id.has_data', readonly=True)
    has_automation = fields.Boolean(compute='_compute_has_automation')
    # Edge case (spec 9): removing a field with populated data requires an explicit
    # second confirmation -- never silently drop data.
    confirm_data_loss = fields.Boolean(
        string='I understand this will permanently delete existing data in this field')
    # Edge case (spec 4.7): a field with a dependent automation offers to remove the
    # automation first rather than blocking outright.
    remove_automation = fields.Boolean(
        string='Also remove the linked notification automation', default=True)

    @api.depends('registry_id.automation_id')
    def _compute_has_automation(self):
        for wizard in self:
            wizard.has_automation = bool(wizard.registry_id.automation_id)

    def action_confirm(self):
        self.ensure_one()
        registry = self.registry_id
        if registry.automation_id and not self.remove_automation:
            raise UserError(_(
                'This field has a notification automation attached. Check "Also remove the '
                'linked notification automation" to proceed, or remove the automation '
                'manually first.'))
        if registry.has_data and not self.confirm_data_loss:
            raise UserError(_(
                'This field currently has data on existing records. Confirm data loss to '
                'proceed with removal.'))
        # Capture the linked records before deleting anything: field_id/view_id cascade
        # to the registry row itself (see models/bs_addfield_registry.py), so `registry`
        # may no longer exist in DB partway through -- never dereference it again below.
        automation = registry.automation_id
        view = registry.view_id
        field = registry.field_id
        # Dependency-ordered removal (spec 7.6): automation -> view -> field, all wrapped
        # in one transaction so a partial failure never leaves orphaned metadata.
        with self.env.cr.savepoint():
            if automation:
                templates = automation.action_server_ids.mapped('template_id')
                automation.unlink()
                templates.unlink()
            view.unlink()
            field.unlink()
            if registry.exists():
                registry.unlink()
        return {'type': 'ir.actions.act_window_close'}
