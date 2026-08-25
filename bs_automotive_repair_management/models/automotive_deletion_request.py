import psycopg2

from odoo import _, api, fields, models
from odoo.exceptions import UserError

DELETABLE_MODELS = [
    ('automotive.vehicle', 'Vehicle'),
    ('automotive.vehicle.inspection', 'Vehicle Inspection'),
    ('automotive.repair.order', 'Repair Order'),
]


class AutomotiveDeletionRequest(models.Model):
    _name = 'automotive.deletion.request'
    _description = 'Deletion Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    res_model = fields.Selection(DELETABLE_MODELS, required=True)
    res_id = fields.Integer(required=True)
    record_name = fields.Char(required=True)
    requested_by = fields.Many2one(
        'res.users', default=lambda self: self.env.user, required=True, readonly=True,
    )
    reason = fields.Text(required=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='pending', required=True, tracking=True)
    reviewed_by = fields.Many2one('res.users', readonly=True)
    review_date = fields.Datetime(readonly=True)
    review_notes = fields.Text()

    def _get_manager_partners(self):
        group = self.env.ref('bs_automotive_repair_management.group_shop_manager')
        return self.env['res.users'].search([('all_group_ids', 'in', group.id)]).partner_id

    @api.model_create_multi
    def create(self, vals_list):
        requests = super().create(vals_list)
        for request in requests:
            manager_partners = request._get_manager_partners()
            request.message_subscribe(partner_ids=manager_partners.ids)
            request.message_post(
                body=_(
                    '%(user)s requested deletion of %(record)s (%(model)s): %(reason)s'
                ) % {
                    'user': request.requested_by.name,
                    'record': request.record_name,
                    'model': dict(DELETABLE_MODELS).get(request.res_model, request.res_model),
                    'reason': request.reason,
                },
                partner_ids=manager_partners.ids,
                subtype_xmlid='mail.mt_comment',
            )
        return requests

    def _check_is_manager(self):
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager'):
            raise UserError(_('Only a Shop Manager can review deletion requests.'))

    def action_approve(self):
        self._check_is_manager()
        for request in self:
            if request.state != 'pending':
                raise UserError(_('Only pending requests can be approved.'))
            record = self.env[request.res_model].browse(request.res_id).exists()
            if record:
                try:
                    with self.env.cr.savepoint():
                        record.unlink()
                except psycopg2.errors.ForeignKeyViolation:
                    raise UserError(_(
                        'Cannot delete %(record)s: other records still reference it '
                        '(e.g. repair orders, warranty claims). Resolve or delete those '
                        'first, then approve this request again.'
                    ) % {'record': request.record_name})
            request.write({
                'state': 'approved',
                'reviewed_by': self.env.user.id,
                'review_date': fields.Datetime.now(),
            })

    def action_reject(self):
        self._check_is_manager()
        for request in self:
            if request.state != 'pending':
                raise UserError(_('Only pending requests can be rejected.'))
        self.write({
            'state': 'rejected',
            'reviewed_by': self.env.user.id,
            'review_date': fields.Datetime.now(),
        })
