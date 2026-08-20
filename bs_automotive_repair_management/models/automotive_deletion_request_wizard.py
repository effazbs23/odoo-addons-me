from odoo import _, fields, models
from odoo.exceptions import UserError


class AutomotiveDeletionRequestWizard(models.TransientModel):
    _name = 'automotive.deletion.request.wizard'
    _description = 'Request Deletion Approval'

    res_model = fields.Char(required=True)
    res_id = fields.Integer(required=True)
    record_name = fields.Char(required=True)
    reason = fields.Text(required=True)

    def action_submit(self):
        self.ensure_one()
        existing = self.env['automotive.deletion.request'].search([
            ('res_model', '=', self.res_model),
            ('res_id', '=', self.res_id),
            ('state', '=', 'pending'),
        ], limit=1)
        if existing:
            raise UserError(_(
                'A deletion request for this record is already pending review.'
            ))
        self.env['automotive.deletion.request'].create({
            'res_model': self.res_model,
            'res_id': self.res_id,
            'record_name': self.record_name,
            'reason': self.reason,
        })
        return {'type': 'ir.actions.act_window_close'}
