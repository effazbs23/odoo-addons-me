from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, AccessError


class PettyCashRequest(models.Model):
    _name = 'petty.cash.request'
    _description = 'Petty Cash Request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default='New')
    date = fields.Date('Request Date', required=True, default=fields.Date.context_today, tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                   default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
                                   tracking=True)
    department_id = fields.Many2one('hr.department', 'Department', related='employee_id.department_id', store=True)
    line_ids = fields.One2many('petty.cash.request.line', 'request_id', 'Purpose Lines', copy=True)
    amount = fields.Monetary('Requested Amount', compute='_compute_amount', store=True, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                   default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                  default=lambda self: self.env.company)
    purpose = fields.Text('Purpose', required=False)
    request_type = fields.Selection([
        ('purchase', 'Purchase'),
        ('salary', 'Salary'),
        ('tour_travel', 'Tour & Travel'),
        ('operational_expenses', 'Operational Expenses'),
        ('expense', 'Expense'),
        ('other', 'Other'),
    ], string='Request Type', default='purchase', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('issued', 'Issued')
    ], default='draft', tracking=True)
    approved_by = fields.Many2one('res.users', 'Approved By', readonly=True, tracking=True)
    approved_date = fields.Datetime('Approved Date', readonly=True)
    advance_id = fields.Many2one('petty.cash.advance', 'Cash Advance', readonly=True)
    notes = fields.Text('Notes')
    vessel_id = fields.Many2one(
        "account.analytic.account",
        string="Cost Center", required=True,
        domain="[('plan_id.name', 'in', ['Vessels', 'Cost Centers']), ('company_id', 'in', [False, company_id])]"
    )
    raised_by = fields.Many2one("res.users", string="Raised By", default=lambda self: self.env.user)
    attachment_ids = fields.Many2many('ir.attachment', 'petty_cash_request_attachment_rel',
                                       'petty_cash_request_id', 'attachment_id', 'Attachments')

    @api.depends('line_ids.amount')
    def _compute_amount(self):
        for record in self:
            record.amount = sum(record.line_ids.mapped('amount'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("petty.cash.request") or "New"
        return super().create(vals_list)

    def _check_manager(self):
        """Approval-level actions require the Petty Cash Manager group."""
        if not self.env.user.has_group('petty_cash.group_petty_cash_manager'):
            raise AccessError(_(
                'Only a Petty Cash Manager can approve or reject cash requests.'
            ))

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft requests can be submitted.'))
            if not rec.line_ids:
                raise UserError(_('Add at least one purpose line before submitting.'))
        self.write({'state': 'submitted'})

    def action_approve(self):
        self._check_manager()
        for rec in self:
            if rec.state != 'submitted':
                raise UserError(_('Only submitted requests can be approved.'))
        self.write({
            'state': 'approved',
            'approved_by': self.env.uid,
            'approved_date': fields.Datetime.now()
        })

    def action_reject(self):
        self._check_manager()
        for rec in self:
            if rec.state not in ('submitted', 'approved'):
                raise UserError(_('Only submitted or approved requests can be rejected.'))
        self.write({'state': 'rejected'})

    def action_draft(self):
        for rec in self:
            if rec.state not in ('submitted', 'rejected'):
                raise UserError(_('Only submitted or rejected requests can be reset to draft.'))
        self.write({'state': 'draft'})
