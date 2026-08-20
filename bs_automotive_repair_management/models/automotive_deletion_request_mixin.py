from odoo import fields, models


class AutomotiveDeletionRequestMixin(models.AbstractModel):
    _name = 'automotive.deletion.request.mixin'
    _description = 'Adds a manager-approval deletion request flow to a model'

    user_can_delete_directly = fields.Boolean(compute='_compute_user_can_delete_directly')

    def _compute_user_can_delete_directly(self):
        can_delete = self.env.user.has_group('bs_automotive_repair_management.group_shop_manager')
        for record in self:
            record.user_can_delete_directly = can_delete

    def action_request_deletion(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'automotive.deletion.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
                'default_record_name': self.display_name,
            },
        }
