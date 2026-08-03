from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnRequest(models.Model):
    _name = 'return.request'
    _description = 'Purchase Return Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Return Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        required=True,
        tracking=True,
        domain=[('supplier_rank', '>', 0)]
    )

    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True
    )

    expected_return_date = fields.Date(
        string='Expected Return Date',
        default=lambda self: fields.Date.today() + timedelta(days=7)
    )

    return_line_ids = fields.One2many(
        'return.request.line',
        'return_request_id',
        string='Return Lines'
    )

    reason = fields.Text(string='Return Reason')

    # Computed totals
    total_return_qty = fields.Float(
        string='Total Return Quantity',
        compute='_compute_totals',
        store=True
    )

    total_return_amount = fields.Monetary(
        string='Total Return Amount',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        required=True,
        default=lambda self: self.env.company.currency_id
    )

    # Generated documents (populated by the vendor return processing)
    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Return to Vendor',
        readonly=True
    )

    credit_note_id = fields.Many2one(
        'account.move',
        string='Vendor Credit Note',
        readonly=True
    )

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')

    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    ##################################################################

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('return.request') or _('New')
        return super().create(vals_list)

    @api.depends('return_line_ids.return_qty', 'return_line_ids.price_unit')
    def _compute_totals(self):
        for record in self:
            record.total_return_qty = sum(record.return_line_ids.mapped('return_qty'))
            record.total_return_amount = sum(
                line.return_qty * line.price_unit for line in record.return_line_ids
            )

    def action_submit(self):
        """Submit return request for approval."""
        if not self.return_line_ids:
            raise UserError(_('Please add at least one return line.'))
        if not any(line.return_qty > 0 for line in self.return_line_ids):
            raise UserError(_('Please specify return quantities.'))

        self.state = 'submitted'
        self.message_post(body=_('Return request submitted for approval.'))

    def action_approve(self):
        """Approve return request."""
        self.state = 'approved'
        self.message_post(body=_('Return request approved.'))

    def action_process(self):
        """Process the return request. Vendor returns override this to create the
        return-to-vendor picking and the vendor credit note."""
        self.state = 'processing'

    def action_done(self):
        """Mark return request as done."""
        self.state = 'done'
        self.message_post(body=_('Return request completed.'))

    def action_cancel(self):
        """Cancel return request."""
        self.state = 'cancelled'
        self.message_post(body=_('Return request cancelled.'))

    def action_reset_to_draft(self):
        """Reset to draft state."""
        self.state = 'draft'

    def action_view_return_picking(self):
        """Open the return-to-vendor picking."""
        if self.return_picking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Return to Vendor'),
                'res_model': 'stock.picking',
                'res_id': self.return_picking_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_credit_note(self):
        """Open the vendor credit note."""
        if self.credit_note_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Vendor Credit Note'),
                'res_model': 'account.move',
                'res_id': self.credit_note_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
