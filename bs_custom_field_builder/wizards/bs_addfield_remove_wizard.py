from odoo import _, fields, models
from odoo.exceptions import UserError


class BsAddfieldRemoveWizard(models.TransientModel):
    _name = 'bs.addfield.remove.wizard'
    _description = 'Remove Custom Field'

    # Plain fields snapshotted via context defaults (see action_open_remove_wizard on the
    # registry model) rather than related=/compute=: Odoo's web client excludes readonly
    # fields from the onchange request it sends when opening a new record, so a related
    # or computed field that's also marked readonly never gets a value client-side even
    # though it resolves correctly at the Python/RPC level -- confirmed by testing in a
    # real browser (the widget mounted but stayed empty; direct onchange() calls in a
    # shell returned the correct value every time). default_get-sourced values don't have
    # this problem, which is exactly how registry_id itself already worked reliably.
    registry_id = fields.Many2one('bs.addfield.registry', required=True, readonly=True)
    field_label = fields.Char(readonly=True)
    model_label = fields.Char(readonly=True)
    has_data = fields.Boolean(readonly=True)
    has_automation = fields.Boolean(readonly=True)
    # Non-blocking heads-up (spec: warn, don't block) -- a manually-built view, saved
    # filter, or export template referencing this field's technical name won't be
    # fixed up by removal and will break; the user decides whether that's acceptable.
    has_other_references = fields.Boolean(readonly=True)
    # Edge case (spec 9): removing a field with populated data requires an explicit
    # second confirmation -- never silently drop data.
    confirm_data_loss = fields.Boolean(
        string='I understand this will permanently delete existing data in this field')
    # Edge case (spec 4.7): a field with a dependent automation offers to remove the
    # automation first rather than blocking outright.
    remove_automation = fields.Boolean(
        string='Also remove the linked notification automation', default=True)

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
        automation = registry.automation_id
        view = registry.view_id
        field = registry.field_id
        # Dependency-ordered removal (spec 7.6): automation -> view -> field, all wrapped
        # in one transaction so a partial failure never leaves orphaned metadata. The
        # registry row itself is kept (state='deleted') as a permanent audit-log entry --
        # field_id/view_id/automation_id null out automatically (ondelete='set null') as
        # their targets are unlinked.
        with self.env.cr.savepoint():
            if automation:
                templates = automation.action_server_ids.mapped('template_id')
                automation.unlink()
                templates.unlink()
            view.unlink()
            field.unlink()
            registry.state = 'deleted'
        return {'type': 'ir.actions.act_window_close'}
