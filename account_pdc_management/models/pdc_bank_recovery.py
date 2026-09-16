from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PdcBankRecovery(models.Model):
    """The fee a bank charges for a returned cheque, and its recovery.

    Two postings, deliberately kept apart:

    * the **bank charge entry** books what the bank actually took from the
      company -- Dr Bank Charges / Cr Bank. Without it the fee only ever shows up
      during bank reconciliation and there is nothing to check a recovery
      against.
    * the **bank recovery invoice** bills that same fee back to the party whose
      cheque bounced.

    The recovery can never exceed the charge. Recovering more would turn a
    pass-through cost into income the company never incurred, so the amount
    billed is the charge less whatever was waived, and a constraint enforces it
    regardless of how the record was written.
    """
    _name = 'pdc.bank.recovery'
    _description = 'Bounced Cheque Bank Charge Recovery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(
        string='Reference', required=True, copy=False, readonly=True, index='trigram',
        default=lambda self: _('New'),
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('charged', 'Charge Posted'),
            ('invoiced', 'Invoiced'),
            ('cancel', 'Cancelled'),
        ],
        string='Status', default='draft', required=True, copy=False, tracking=True,
    )

    payment_id = fields.Many2one(
        'account.payment', string='Bounced Cheque', required=True, ondelete='cascade',
        copy=False, tracking=True, check_company=True,
        domain="[('is_pdc', '=', True), ('pdc_state', '=', 'bounced')]",
    )
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True, tracking=True,
        help="Party the bank charge is recovered from.",
    )
    cheque_number = fields.Char(related='payment_id.cheque_number', string='Cheque Number', store=True)
    bounce_date = fields.Date(related='payment_id.pdc_bounce_date', string='Bounce Date', store=True)

    company_id = fields.Many2one(
        'res.company', string='Company', required=True, default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency', readonly=True)

    # -- what the bank took ---------------------------------------------------
    charge_amount = fields.Monetary(
        string='Bank Charge', required=True, tracking=True,
        help="Fee the bank actually deducted for the returned cheque. This is the ceiling "
             "of what can be recovered from the partner.",
    )
    charge_date = fields.Date(
        string='Charge Date', required=True, default=fields.Date.context_today, tracking=True,
    )
    bank_journal_id = fields.Many2one(
        'account.journal', string='Charged By Bank', check_company=True,
        domain="[('type', '=', 'bank'), ('is_pdc', '=', False)]",
        help="Bank journal the fee was deducted from.",
    )
    charge_reason = fields.Text(string='Reason / Bank Advice Reference')
    charge_move_id = fields.Many2one(
        'account.move', string='Bank Charge Entry', readonly=True, copy=False,
    )

    # -- what is billed back --------------------------------------------------
    waiver_amount = fields.Monetary(
        string='Waived', tracking=True,
        help="Part of the bank charge the company decides to absorb. It lowers the amount "
             "billed to the partner; it never raises it.",
    )
    waiver_reason = fields.Text(string='Waiver Reason')
    recovery_amount = fields.Monetary(
        string='Recoverable', compute='_compute_amounts', store=True, tracking=True,
        help="Bank charge less the waived part. This is what the recovery invoice is raised for.",
    )
    tax_ids = fields.Many2many(
        'account.tax', string='Taxes', check_company=True,
        domain="[('type_tax_use', '=', 'sale')]",
        help="Taxes added on top of the recovered amount on the invoice.",
    )
    tax_amount = fields.Monetary(string='Tax', compute='_compute_amounts', store=True)
    total_amount = fields.Monetary(
        string='Total Invoiced', compute='_compute_amounts', store=True,
    )
    invoice_id = fields.Many2one(
        'account.move', string='Bank Recovery Invoice', readonly=True, copy=False, tracking=True,
    )
    invoice_state = fields.Selection(
        related='invoice_id.state', string='Invoice Status', readonly=True,
    )
    invoice_payment_state = fields.Selection(
        related='invoice_id.payment_state', string='Invoice Payment', readonly=True,
    )

    # ------------------------------------------------------------------
    # Computes / constraints
    # ------------------------------------------------------------------
    @api.depends('charge_amount', 'waiver_amount', 'tax_ids', 'partner_id')
    def _compute_amounts(self):
        for recovery in self:
            net = max(0.0, recovery.charge_amount - recovery.waiver_amount)
            recovery.recovery_amount = net
            taxes = recovery.tax_ids.compute_all(
                net, currency=recovery.currency_id, quantity=1.0, partner=recovery.partner_id,
            ) if (recovery.tax_ids and net) else None
            recovery.tax_amount = (taxes['total_included'] - taxes['total_excluded']) if taxes else 0.0
            recovery.total_amount = net + recovery.tax_amount

    @api.constrains('charge_amount')
    def _check_charge_amount(self):
        for recovery in self:
            if recovery.charge_amount <= 0:
                raise ValidationError(_("The bank charge has to be greater than zero."))

    @api.constrains('waiver_amount', 'charge_amount')
    def _check_waiver_amount(self):
        for recovery in self:
            if recovery.waiver_amount < 0:
                raise ValidationError(_("The waived amount cannot be negative."))
            if recovery.waiver_amount > recovery.charge_amount:
                raise ValidationError(_(
                    "The waived amount (%(waiver)s) cannot exceed the bank charge (%(charge)s).",
                    waiver=recovery.waiver_amount, charge=recovery.charge_amount))

    @api.constrains('recovery_amount', 'charge_amount')
    def _check_recovery_within_charge(self):
        """The whole point of the model: never bill more than the bank took."""
        for recovery in self:
            if recovery.currency_id.compare_amounts(
                    recovery.recovery_amount, recovery.charge_amount) > 0:
                raise ValidationError(_(
                    "The recoverable amount (%(recovery)s) cannot exceed the bank charge "
                    "(%(charge)s). A bounced cheque fee is passed on at cost.",
                    recovery=recovery.recovery_amount, charge=recovery.charge_amount))

    @api.onchange('payment_id')
    def _onchange_payment_id(self):
        if self.payment_id:
            self.partner_id = self.payment_id.partner_id
            self.bank_journal_id = (
                self.payment_id.pdc_bank_journal_id
                or self.payment_id.journal_id.pdc_bank_journal_id
            )
            if not self.tax_ids:
                self.tax_ids = self.company_id.pdc_recovery_tax_ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pdc.bank.recovery') or _('New')
        return super().create(vals_list)

    def unlink(self):
        if any(recovery.charge_move_id or recovery.invoice_id for recovery in self):
            raise UserError(_(
                "A recovery that already carries accounting entries cannot be deleted. "
                "Cancel it instead."))
        return super().unlink()

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    def _get_charge_config(self):
        self.ensure_one()
        company = self.company_id
        missing = []
        if not company.pdc_bank_charge_account_id:
            missing.append(_("Bank Charge account"))
        if not company.pdc_operations_journal_id:
            missing.append(_("PDC Operations journal"))
        if not self.bank_journal_id:
            missing.append(_("Charged By Bank journal, on this record"))
        elif not self.bank_journal_id.default_account_id:
            missing.append(_("default account on bank journal %s") % self.bank_journal_id.display_name)
        if missing:
            raise UserError(_(
                "Set the following under Accounting > Configuration > Settings > Post Dated "
                "Cheques before posting the bank charge:\n- %s") % "\n- ".join(missing))
        # The charge is a miscellaneous entry, so its journal has to accept one. Said here
        # rather than letting account.move fail on its own opaque constraint.
        if company.pdc_operations_journal_id.type != 'general':
            raise UserError(_(
                "The PDC Operations journal (%(journal)s) is a '%(type)s' journal. The bank "
                "charge entry is a miscellaneous entry, so pick a Miscellaneous journal under "
                "Accounting > Configuration > Settings > Post Dated Cheques.",
                journal=company.pdc_operations_journal_id.display_name,
                type=company.pdc_operations_journal_id.type))
        return company

    def _get_recovery_config(self):
        self.ensure_one()
        company = self.company_id
        missing = []
        if not company.pdc_recovery_income_account_id:
            missing.append(_("Bank Charge Recovery income account"))
        if not company.pdc_recovery_journal_id:
            missing.append(_("Bank Charge Recovery sales journal"))
        if missing:
            raise UserError(_(
                "Set the following under Accounting > Configuration > Settings > Post Dated "
                "Cheques before raising the recovery invoice:\n- %s") % "\n- ".join(missing))
        # The recovery is a customer invoice, and account.move refuses one outside a sales
        # journal. Catch a mis-picked journal here, where the setting can be named.
        if company.pdc_recovery_journal_id.type != 'sale':
            raise UserError(_(
                "The Bank Charge Recovery journal (%(journal)s) is a '%(type)s' journal. The "
                "recovery is a customer invoice, so it needs a Sales journal. Change it under "
                "Accounting > Configuration > Settings > Post Dated Cheques.",
                journal=company.pdc_recovery_journal_id.display_name,
                type=company.pdc_recovery_journal_id.type))
        return company

    # ------------------------------------------------------------------
    # Bank charge
    # ------------------------------------------------------------------
    def _prepare_charge_move_vals(self, company):
        self.ensure_one()
        label = _("Bank charge - returned cheque %s") % (
            self.cheque_number or self.payment_id.display_name)
        return {
            'move_type': 'entry',
            'journal_id': company.pdc_operations_journal_id.id,
            'date': self.charge_date,
            'ref': label,
            'company_id': company.id,
            'pdc_payment_id': self.payment_id.id,
            'pdc_entry_type': 'bank_charge',
            'line_ids': [
                Command.create({
                    'name': label,
                    'account_id': company.pdc_bank_charge_account_id.id,
                    'partner_id': self.partner_id.id,
                    'debit': self.charge_amount,
                    'credit': 0.0,
                }),
                Command.create({
                    'name': label,
                    'account_id': self.bank_journal_id.default_account_id.id,
                    'partner_id': self.partner_id.id,
                    'debit': 0.0,
                    'credit': self.charge_amount,
                }),
            ],
        }

    def action_post_charge(self):
        """Book what the bank took: Dr Bank Charges / Cr Bank."""
        for recovery in self:
            if recovery.state != 'draft':
                raise UserError(_("Only a draft recovery can have its bank charge posted."))
            company = recovery._get_charge_config()
            move = self.env['account.move'].create(recovery._prepare_charge_move_vals(company))
            move.action_post()
            recovery.write({'state': 'charged', 'charge_move_id': move.id})
            recovery.message_post(body=_("Bank charge of %(amount)s posted as %(move)s.",
                                         amount=recovery.charge_amount, move=move.name))
        return True

    # ------------------------------------------------------------------
    # Recovery invoice
    # ------------------------------------------------------------------
    def _prepare_invoice_vals(self, company):
        self.ensure_one()
        label = _("Bank charge recovery - returned cheque %s") % (
            self.cheque_number or self.payment_id.display_name)
        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'journal_id': company.pdc_recovery_journal_id.id,
            'invoice_date': fields.Date.context_today(self),
            'company_id': company.id,
            'ref': label,
            'pdc_payment_id': self.payment_id.id,
            'pdc_entry_type': 'recovery',
            'invoice_line_ids': [Command.create({
                'name': label,
                'quantity': 1.0,
                'price_unit': self.recovery_amount,
                'account_id': company.pdc_recovery_income_account_id.id,
                'tax_ids': [Command.set(self.tax_ids.ids)],
            })],
        }

    def action_create_invoice(self):
        """Raise the draft bank recovery invoice for the recoverable amount."""
        for recovery in self:
            if recovery.state != 'charged':
                raise UserError(_(
                    "Post the bank charge first: the recovery invoice is capped by what the "
                    "bank actually charged."))
            if recovery.invoice_id:
                raise UserError(_("Recovery %s already has an invoice.") % recovery.name)
            if not recovery.recovery_amount:
                recovery.write({'state': 'invoiced'})
                recovery.message_post(body=_("Charge fully waived, no recovery invoice raised."))
                continue
            company = recovery._get_recovery_config()
            invoice = self.env['account.move'].create(recovery._prepare_invoice_vals(company))
            recovery.write({'state': 'invoiced', 'invoice_id': invoice.id})
            # A draft invoice has no number yet, so display_name is what reads.
            recovery.message_post(body=_("Draft recovery invoice %(invoice)s raised for %(total)s.",
                                         invoice=invoice.display_name,
                                         total=recovery.total_amount))
            invoice.message_post(body=_("Raised from bank charge recovery %(name)s on cheque "
                                        "%(cheque)s.", name=recovery.name,
                                        cheque=recovery.cheque_number or ''))
        if len(self) == 1 and self.invoice_id:
            return self.action_view_invoice()
        return True

    def action_cancel(self):
        """Undo the recovery, reversing whatever was already posted."""
        for recovery in self:
            if recovery.state == 'cancel':
                continue
            if recovery.invoice_id and recovery.invoice_id.state == 'posted':
                raise UserError(_(
                    "Recovery invoice %s is posted. Credit note it from the invoice itself "
                    "before cancelling this recovery.") % recovery.invoice_id.name)
            if recovery.invoice_id:
                recovery.invoice_id.button_cancel()
            if recovery.charge_move_id and recovery.charge_move_id.state == 'posted':
                reversal = recovery.charge_move_id._reverse_moves([{
                    'date': fields.Date.context_today(recovery),
                    'ref': _("Reversal of %s") % recovery.charge_move_id.name,
                    'journal_id': recovery.charge_move_id.journal_id.id,
                }], cancel=True)
                recovery.message_post(body=_("Bank charge reversed by %s.") % reversal.name)
            recovery.write({'state': 'cancel'})
        return True

    def action_reset_to_draft(self):
        for recovery in self:
            if recovery.state != 'cancel':
                raise UserError(_("Only a cancelled recovery can be reset to draft."))
            recovery.write({
                'state': 'draft', 'charge_move_id': False, 'invoice_id': False,
            })
        return True

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError(_("No recovery invoice has been raised yet."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bank Recovery Invoice'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_charge_move(self):
        self.ensure_one()
        if not self.charge_move_id:
            raise UserError(_("The bank charge has not been posted yet."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bank Charge Entry'),
            'res_model': 'account.move',
            'res_id': self.charge_move_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_payment(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Post Dated Cheque'),
            'res_model': 'account.payment',
            'res_id': self.payment_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
