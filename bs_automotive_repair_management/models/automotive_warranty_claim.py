from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AutomotiveWarrantyClaim(models.Model):
    _name = 'automotive.warranty.claim'
    _description = 'Warranty Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True)

    origin_repair_order_id = fields.Many2one(
        'automotive.repair.order', string='Original Repair Order', required=True, index=True,
    )
    origin_part_line_id = fields.Many2one(
        'automotive.repair.order.part', string='Original Part Line', required=True,
        domain="[('order_id', '=', origin_repair_order_id)]",
        help='Points at the exact part installed — this is why the lot/serial '
             'tracking on part lines matters (§2): the claim can name the '
             'precise unit, not just "an alternator sometime last year."',
    )
    vehicle_id = fields.Many2one(related='origin_repair_order_id.vehicle_id', store=True)

    claim_date = fields.Date(default=fields.Date.context_today, required=True)
    issue_description = fields.Text(required=True)

    within_warranty = fields.Boolean(compute='_compute_within_warranty', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('resolved', 'Resolved'),
    ], default='draft', required=True, tracking=True, copy=False)

    resolution_repair_order_id = fields.Many2one(
        'automotive.repair.order', string='Resolution Repair Order', readonly=True, copy=False,
    )

    @api.depends('claim_date', 'origin_part_line_id.warranty_end_date')
    def _compute_within_warranty(self):
        for claim in self:
            end_date = claim.origin_part_line_id.warranty_end_date
            claim.within_warranty = bool(end_date and claim.claim_date and claim.claim_date <= end_date)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('automotive.warranty.claim') or _('New')
        claims = super().create(vals_list)
        for claim in claims:
            claim._send_claim_received_email()
        return claims

    def _send_claim_received_email(self):
        self.ensure_one()
        if not self.vehicle_id.partner_id.email:
            return
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_warranty_claim_received',
            subtype_xmlid='mail.mt_comment',
        )

    def action_submit(self):
        for claim in self:
            if claim.state != 'draft':
                raise UserError(_('Only draft claims can be submitted for review.'))
        self.write({'state': 'under_review'})
        for claim in self:
            if not claim.within_warranty:
                claim._notify_managers_out_of_warranty()

    def _get_manager_partners(self):
        group = self.env.ref('bs_automotive_repair_management.group_shop_manager')
        return self.env['res.users'].search([('all_group_ids', 'in', group.id)]).partner_id

    def _notify_managers_out_of_warranty(self):
        """Out-of-warranty claims aren't blocked (a manager may still want to
        approve one as an exception) but managers need to be flagged so they
        can make that call knowingly, rather than approving without
        realizing the part is past its warranty end date."""
        self.ensure_one()
        manager_partners = self._get_manager_partners()
        self.message_subscribe(partner_ids=manager_partners.ids)
        part_line = self.origin_part_line_id
        self.message_post(
            body=_(
                '⚠ This claim is outside the standard warranty period: '
                '%(product)s was sold/installed on %(start)s with a %(months)s-month '
                'warranty (ended %(end)s), but the claim date is %(claim_date)s. '
                'A Shop Manager can still approve it as an exception.'
            ) % {
                'product': part_line.product_id.display_name,
                'start': part_line.warranty_start_date or _('unknown'),
                'months': part_line.warranty_months,
                'end': part_line.warranty_end_date or _('unknown'),
                'claim_date': self.claim_date,
            },
            partner_ids=manager_partners.ids,
            subtype_xmlid='mail.mt_comment',
        )

    def _check_is_manager(self):
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager'):
            raise UserError(_('Only a Shop Manager can approve or reject warranty claims.'))

    def action_reject(self):
        self._check_is_manager()
        for claim in self:
            if claim.state != 'under_review':
                raise UserError(_('Only claims under review can be rejected.'))
        self.write({'state': 'rejected'})

    def action_approve(self):
        self._check_is_manager()
        for claim in self:
            if claim.state != 'under_review':
                raise UserError(_('Only claims under review can be approved.'))
        self.write({'state': 'approved'})

    def action_create_repair_order(self):
        """Lets the user create the resolution repair order themselves,
        referencing this claim's number, instead of the system generating
        one silently on approval."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved claims can have a repair order created against them.'))
        if self.resolution_repair_order_id:
            raise UserError(_('This claim already has a resolution repair order.'))
        origin = self.origin_repair_order_id
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Repair Order — %s') % self.name,
            'res_model': 'automotive.repair.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_order_type': 'warranty_claim',
                'default_warranty_claim_id': self.id,
                'default_vehicle_id': self.vehicle_id.id,
                'default_customer_complaint': self.issue_description,
                'default_salesperson_id': origin.salesperson_id.id,
            },
        }

    def action_resolve(self):
        for claim in self:
            if claim.state != 'approved':
                raise UserError(_('Only approved claims can be marked resolved.'))
            if claim.resolution_repair_order_id.state != 'closed':
                raise UserError(_(
                    'The resolution repair order must be closed before the claim can be marked resolved.'
                ))
        self.write({'state': 'resolved'})
