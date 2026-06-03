# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _  # pylint: disable=import-error
from odoo.exceptions import UserError  # pylint: disable=import-error
from markupsafe import Markup  # pylint: disable=import-error

_logger = logging.getLogger(__name__)


class LessorLeaseContract(models.Model):
    _inherit = 'lessor.lease.contract'

    def _get_default_vat_rate(self):
        vat_rate_id = self.env['ir.config_parameter'].sudo().get_param(
            f'lessor_lease_accounting.lease_vat_rate_id'
        )
        if vat_rate_id:
            return int(vat_rate_id)
        return False


    vat_rate_id = fields.Many2one(
        default=_get_default_vat_rate
    )

    # ===== Down Payment Invoice Fields =====
    down_payment_invoice_id = fields.Many2one(
        'account.move',
        string='Down Payment Invoice',
        readonly=True,
        copy=False,
        tracking=True,
        help="Customer invoice for the down payment"
    )
    
    down_payment_invoice_state = fields.Selection(
        related='down_payment_invoice_id.state',
        string='Invoice Status',
        store=True,
        readonly=True
    )
    
    # ===== Initial Recognition Fields =====
    initial_recognition_move_id = fields.Many2one(
        'account.move',
        string='Initial Recognition Entry',
        readonly=True,
        copy=False,
        tracking=True,
        help="Journal entry for initial recognition of lease"
    )
    
    initial_recognition_state = fields.Selection(
        related='initial_recognition_move_id.state',
        string='Recognition Status',
        store=True,
        readonly=True
    )
    
    # ===== Accounting Migration Fields =====
    accounting_start_date = fields.Date(
        string='Accounting Start Date',
        tracking=True,
        help="For migrating old leases: Set this date to skip past accounting entries.\n\n"
             "When set:\n"
             "• Down Payment Invoice button will be hidden (assumes already created)\n"
             "• Initial Recognition button will be hidden (assumes already posted)\n"
             "• Cron will only generate entries from this date onwards\n\n"
             "Leave blank for new leases to process all entries normally."
    )
    
    # ===== Count Fields for Smart Buttons =====
    draft_invoice_count = fields.Integer(
        string='Draft Invoices',
        compute='_compute_monthly_counts',
        help="Count of draft monthly invoices"
    )
    
    unpaid_invoice_count = fields.Integer(
        string='Unpaid Invoices',
        compute='_compute_monthly_counts',
        help="Count of posted but unpaid/partially paid invoices"
    )
    
    paid_invoice_count = fields.Integer(
        string='Paid Invoices',
        compute='_compute_monthly_counts',
        help="Count of fully paid invoices"
    )
    
    draft_entry_count = fields.Integer(
        string='Draft Entries',
        compute='_compute_monthly_counts',
        help="Count of draft journal entries"
    )
    
    posted_entry_count = fields.Integer(
        string='Posted Entries',
        compute='_compute_monthly_counts',
        help="Count of posted journal entries"
    )
    
    draft_vat_entry_count = fields.Integer(
        string='Draft VAT Entries',
        compute='_compute_monthly_counts',
        help="Count of draft VAT recognition entries"
    )
    
    posted_vat_entry_count = fields.Integer(
        string='Posted VAT Entries',
        compute='_compute_monthly_counts',
        help="Count of posted VAT recognition entries"
    )
    
    draft_interest_entry_count = fields.Integer(
        string='Draft Interest Entries',
        compute='_compute_monthly_counts',
        help="Count of draft interest recognition entries"
    )
    
    posted_interest_entry_count = fields.Integer(
        string='Posted Interest Entries',
        compute='_compute_monthly_counts',
        help="Count of posted interest recognition entries"
    )
    
    @api.depends('schedule_line_ids', 'schedule_line_ids.invoice_id', 'schedule_line_ids.move_id')
    def _compute_monthly_counts(self):
        """Compute counts for smart buttons"""
        for record in self:
            # Get all monthly invoices (from schedule lines)
            monthly_invoices = record.schedule_line_ids.mapped('invoice_id').filtered(lambda inv: inv)
            
            record.draft_invoice_count = len(monthly_invoices.filtered(lambda inv: inv.state == 'draft'))
            record.unpaid_invoice_count = len(monthly_invoices.filtered(
                lambda inv: inv.state == 'posted' and inv.payment_state in ['not_paid', 'partial']
            ))
            record.paid_invoice_count = len(monthly_invoices.filtered(
                lambda inv: inv.state == 'posted' and inv.payment_state in ['paid', 'in_payment']
            ))
            
            # Get all monthly journal entries (from schedule lines)
            monthly_entries = record.schedule_line_ids.mapped('move_id').filtered(lambda move: move)
            
            record.draft_entry_count = len(monthly_entries.filtered(lambda move: move.state == 'draft'))
            record.posted_entry_count = len(monthly_entries.filtered(lambda move: move.state == 'posted'))
            
            # Get VAT recognition entries (search by reference pattern)
            vat_entries = record.env['account.move'].search([
                ('move_type', '=', 'entry'),
                ('ref', 'ilike', 'VAT Recognition - %s -' % record.name),
            ])
            record.draft_vat_entry_count = len(vat_entries.filtered(lambda m: m.state == 'draft'))
            record.posted_vat_entry_count = len(vat_entries.filtered(lambda m: m.state == 'posted'))
            
            # Get Interest recognition entries (search by reference pattern)
            interest_entries = record.env['account.move'].search([
                ('move_type', '=', 'entry'),
                ('ref', 'ilike', 'Interest Recognition - %s -' % record.name),
            ])
            record.draft_interest_entry_count = len(interest_entries.filtered(lambda m: m.state == 'draft'))
            record.posted_interest_entry_count = len(interest_entries.filtered(lambda m: m.state == 'posted'))
    
    # ===== Constraints =====
    @api.constrains('state')
    def _check_draft_with_accounting_entries(self):
        """
        Prevent setting contract to draft or cancelled if accounting entries exist
        
        User must explicitly cancel/delete all accounting entries before
        reverting to draft or cancelling to prevent data integrity issues.
        """
        for record in self:
            if record.state in ['draft', 'cancelled']:
                error_prefix = 'Cannot set contract to %s:' % ('draft' if record.state == 'draft' else 'cancelled')
                
                # Check for down payment invoice (must be cancelled or deleted)
                if record.down_payment_invoice_id and record.down_payment_invoice_id.state != 'cancel':
                    raise UserError(_(
                        '%s Down payment invoice exists and is not cancelled.\n\n'
                        'Please cancel the down payment invoice first:\n%s (State: %s)'
                    ) % (error_prefix, record.down_payment_invoice_id.name, record.down_payment_invoice_id.state))
                
                # Check for initial recognition entry (must be cancelled or deleted)
                if record.initial_recognition_move_id and record.initial_recognition_move_id.state != 'cancel':
                    raise UserError(_(
                        '%s Initial recognition entry exists and is not cancelled.\n\n'
                        'Please cancel the initial recognition entry first:\n%s (State: %s)'
                    ) % (error_prefix, record.initial_recognition_move_id.name, record.initial_recognition_move_id.state))
                
                # Check for monthly invoices from schedule lines (must all be cancelled)
                monthly_invoices = record.schedule_line_ids.mapped('invoice_id').filtered(
                    lambda inv: inv and inv.state != 'cancel'
                )
                if monthly_invoices:
                    raise UserError(_(
                        '%s %d monthly invoice(s) exist and are not cancelled.\n\n'
                        'Please cancel all monthly invoices first.'
                    ) % (error_prefix, len(monthly_invoices)))
                
                # Check for VAT recognition entries (must all be cancelled)
                vat_entries = self.env['account.move'].search([
                    ('move_type', '=', 'entry'),
                    ('ref', 'ilike', 'VAT Recognition - %s -' % record.name),
                    ('state', '!=', 'cancel'),
                ])
                if vat_entries:
                    raise UserError(_(
                        '%s %d VAT recognition entry(ies) exist and are not cancelled.\n\n'
                        'Please cancel all VAT recognition entries first.'
                    ) % (error_prefix, len(vat_entries)))
                
                # Check for Interest recognition entries (must all be cancelled)
                interest_entries = self.env['account.move'].search([
                    ('move_type', '=', 'entry'),
                    ('ref', 'ilike', 'Interest Recognition - %s -' % record.name),
                    ('state', '!=', 'cancel'),
                ])
                if interest_entries:
                    raise UserError(_(
                        '%s %d interest recognition entry(ies) exist and are not cancelled.\n\n'
                        'Please cancel all interest recognition entries first.'
                    ) % (error_prefix, len(interest_entries)))
    
    # ===== Actions =====
    def action_create_down_payment_invoice(self):
        """
        Create down payment invoice for the lessee
        
        Creates a draft customer invoice with:
        - Down payment amount (gross, including VAT)
        - Proper revenue account
        - VAT tax applied
        - Pre-filled with lessee information
        """
        self.ensure_one()
        
        # Validation
        if self.state != 'confirmed':
            raise UserError(_('Contract must be confirmed to create down payment invoice.'))
        
        if self.down_payment_invoice_id:
            raise UserError(_('Down payment invoice already exists for this contract.'))
        
        # Prepare invoice values
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.lessee_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'ref': _('Down Payment - %s') % self.name,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': _('Down Payment - Lease Contract %s') % self.name,
                'quantity': 1.0,
                # Use NET amount (excluding VAT) as price_unit
                # down_payment_amount is GROSS (including VAT), so we need to calculate net
                'price_unit': self.down_payment_amount / (1 + (self.vat_rate_id.amount / 100)) if self.vat_rate_id else self.down_payment_amount,
                'tax_ids': [(6, 0, [self.vat_rate_id.id])] if self.vat_rate_id else False,
                # Use a default income account - this should be configurable
                'account_id': self._get_down_payment_account().id,
            })],
        }
        
        # Create invoice
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Link invoice to contract
        self.down_payment_invoice_id = invoice.id
        
        message = Markup("<p>%s</p>") % _("Down payment invoice %s created", invoice._get_html_link())
        self.message_post(body=message)

        # Return action to view the created invoice
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _get_down_payment_account(self):
        """
        Get the account for down payment revenue

        PER PDF SPECIFICATION (A1.1):
        Down payment invoice must post to Lease Sales (410101),
        NOT a revenue account. The invoice creates:
        - Dr. AR (113101) - handled by Odoo
        - Cr. Lease Sales (410101) - the product income account
        - Cr. Undue VAT (215102) - tax line

        Returns:
            account.account: HP Receivable account
        """
        return self._get_account('lease_sales_revenue_account_id')
    
    def action_view_down_payment_invoice(self):
        """Open the down payment invoice"""
        self.ensure_one()
        
        if not self.down_payment_invoice_id:
            raise UserError(_('No down payment invoice exists for this contract.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.down_payment_invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ===== Initial Recognition Methods =====
    
    def action_post_initial_recognition(self):
        """
        Post initial recognition entries based on accounting method
        
        - Gross Method: Two separate journal entries (receivable + asset)
        - Net Method: Single IFRS 16 standard entry
        
        IFRS 16 Compliance: Initial recognition at commencement date (Active state)
        when the underlying asset is made available to the lessee.
        """
        self.ensure_one()
        
        # Validation
        if self.state != 'active':
            raise UserError(_(
                'Contract must be active (asset delivered) to post initial recognition.\n'
                'Initial recognition occurs at the commencement date when the asset is '
                'made available to the lessee (IFRS 16).'
            ))
        
        if self.initial_recognition_move_id:
            raise UserError(_('Initial recognition entry already exists for this contract.'))
        
        if not self.accounting_method:
            raise UserError(_('Please select an accounting method before posting initial recognition.'))
        
        # Optional: Check if down payment invoice is posted (recommended for risk management)
        if self.down_payment_invoice_id and self.down_payment_invoice_state != 'posted':
            raise UserError(_(
                'Down payment invoice must be posted before initial recognition.\n'
                'This ensures payment is secured before recognizing the lease.'
            ))
        
        # Post based on accounting method
        if self.accounting_method == 'gross':
            moves = self._create_gross_method_initial_recognition()
            # Link the first move (receivable entry) to contract
            self.initial_recognition_move_id = moves[0].id
            # Post both journal entries
            for move in moves:
                move.action_post()
            # Log message for both entries
            message = Markup("<p>%s<br/>%s<br/>%s</p>") % (
                _("Initial recognition entries posted:"),
                moves[0]._get_html_link(),
                _("%s (Asset)", moves[1]._get_html_link())
            )
            self.message_post(body=message)
            main_move = moves[0]
        elif self.accounting_method == 'net':
            move = self._create_net_method_initial_recognition()
            self.initial_recognition_move_id = move.id
            move.action_post()
            message = Markup("<p>%s</p>") % _('Initial recognition entry %s posted.', move._get_html_link())
            self.message_post(body=message)
            main_move = move
        else:
            raise UserError(_('Invalid accounting method: %s') % self.accounting_method)
        
        # Return action to view the first entry
        return self.action_view_initial_recognition()
    
    def _create_gross_method_initial_recognition(self):
        """
        Create Gross Method (Hire-Purchase) initial recognition entries
        
        TWO separate journal entries as per standard practice:
        
        Entry 1 - Receivable Recognition (4 lines):
        Dr. Hire Purchase Receivable      [Total gross future payments including VAT]
            Cr. Lease Sales Revenue        [Sum of principal payments]
            Cr. Deferred Interest          [Total unearned interest]
            Cr. Undue Output VAT           [Total future VAT]
        
        Entry 2 - Asset Derecognition (2 lines):
        Dr. Cost of Goods Sold             [cost_price]
            Cr. Asset for Sale             [cost_price]
        
        Returns:
            list: Two account.move records [receivable_entry, asset_entry]
        """
        self.ensure_one()
        
        # Validation: Schedule must be generated
        if not self.schedule_line_ids:
            raise UserError(_(
                'Amortization schedule must be generated before posting initial recognition.\n'
                'Please generate the schedule first.'
            ))
        
        # Get configured accounts
        hire_purchase_receivable = self._get_account('hire_purchase_receivable_account_id')
        lease_sales_revenue = self._get_account('lease_sales_revenue_account_id')
        deferred_interest = self._get_account('deferred_interest_account_id')
        undue_output_vat = self._get_account('undue_output_vat_account_id')
        cost_of_goods_sold = self._get_account('cost_of_goods_sold_account_id')
        asset_for_sale = self._get_account('asset_for_sale_account_id')
        journal = self._get_default_journal('lease_journal_id')
        
        # Calculate amounts from schedule
        total_gross_payments = sum(self.schedule_line_ids.mapped('gross_payment'))  # Including VAT
        total_interest = sum(self.schedule_line_ids.mapped('interest'))
        total_vat = sum(self.schedule_line_ids.mapped('vat'))
        total_principal = sum(self.schedule_line_ids.mapped('principal'))
        
        # Balance adjustment for rounding errors
        # Due to rounding in individual schedule lines, the sum of credits may not exactly equal debit
        total_credits = total_principal + total_interest + total_vat
        rounding_diff = total_gross_payments - total_credits
        
        # Apply adjustment to Lease Sales Revenue (principal)
        # This ensures the entry balances perfectly
        adjusted_principal = total_principal + rounding_diff
        
        # Entry 1: Receivable Recognition
        receivable_move_vals = {
            'move_type': 'entry',
            'date': fields.Date.today(),
            'ref': _('Initial Recognition - Receivable - %s') % self.name,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                # Dr. Hire Purchase Receivable (GROSS - including VAT)
                (0, 0, {
                    'name': _('Hire Purchase Receivable - %s') % self.name,
                    'account_id': hire_purchase_receivable.id,
                    'debit': total_gross_payments,
                    'credit': 0.0,
                    'partner_id': self.lessee_id.id,
                }),
                # Cr. Lease Sales Revenue (Principal only, with rounding adjustment)
                (0, 0, {
                    'name': _('Lease Sales Revenue - %s') % self.name,
                    'account_id': lease_sales_revenue.id,
                    'debit': 0.0,
                    'credit': adjusted_principal,  # Adjusted for rounding
                    'partner_id': self.lessee_id.id,
                }),
                # Cr. Deferred Interest
                (0, 0, {
                    'name': _('Deferred Interest - %s') % self.name,
                    'account_id': deferred_interest.id,
                    'debit': 0.0,
                    'credit': total_interest,
                }),
                # Cr. Undue Output VAT
                (0, 0, {
                    'name': _('Undue Output VAT - %s') % self.name,
                    'account_id': undue_output_vat.id,
                    'debit': 0.0,
                    'credit': total_vat,
                }),
            ],
        }
        
        # Entry 2: Asset Derecognition
        asset_move_vals = {
            'move_type': 'entry',
            'date': fields.Date.today(),
            'ref': _('Initial Recognition - Asset - %s') % self.name,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                # Dr. Cost of Goods Sold
                (0, 0, {
                    'name': _('Cost of Goods Sold - %s') % self.asset_name,
                    'account_id': cost_of_goods_sold.id,
                    'debit': self.cost_price,
                    'credit': 0.0,
                }),
                # Cr. Asset for Sale
                (0, 0, {
                    'name': _('Asset Derecognition - %s') % self.asset_name,
                    'account_id': asset_for_sale.id,
                    'debit': 0.0,
                    'credit': self.cost_price,
                }),
            ],
        }
        
        # Create both journal entries
        receivable_move = self.env['account.move'].create(receivable_move_vals)
        asset_move = self.env['account.move'].create(asset_move_vals)
        
        return [receivable_move, asset_move]
    
    def _create_net_method_initial_recognition(self):
        """
        Create Net Method (IFRS 16) initial recognition entry
        
        Entry structure (2-3 lines):
        Dr. Lease Receivable               [PV of net lease payments]
            Cr. Asset Account              [Asset book value]
        Dr/Cr. Gain/Loss on Disposal       [Any difference]
        """
        self.ensure_one()
        
        # Validation: Schedule must be generated
        if not self.schedule_line_ids:
            raise UserError(_(
                'Amortization schedule must be generated before posting initial recognition.\n'
                'Please generate the schedule first.'
            ))
        
        # Get configured accounts
        lease_receivable = self._get_account('lease_receivable_account_id')
        asset_for_sale = self._get_account('asset_for_sale_account_id')
        gain_loss_disposal = self._get_account('gain_loss_disposal_account_id')
        journal = self._get_default_journal('lease_journal_id')
        
        # Calculate PV of lease payments
        # Opening NPV of first schedule line represents PV
        
        pv_lease_payments = self.schedule_line_ids[0].opening_npv if self.schedule_line_ids else 0.0
        
        # Calculate gain/loss
        gain_loss = pv_lease_payments - self.cost_price
        
        # Prepare journal entry lines
        line_vals = [
            # Dr. Lease Receivable
            (0, 0, {
                'name': _('Lease Receivable - %s') % self.name,
                'account_id': lease_receivable.id,
                'debit': pv_lease_payments,
                'credit': 0.0,
                'partner_id': self.lessee_id.id,
            }),
            # Cr. Asset Account
            (0, 0, {
                'name': _('Asset Derecognition - %s') % self.asset_name,
                'account_id': asset_for_sale.id,
                'debit': 0.0,
                'credit': self.cost_price,
            }),
        ]
        
        # Add gain/loss line if difference exists
        if abs(gain_loss) > 0.01:  # Threshold for rounding differences
            if gain_loss > 0:
                # Gain
                line_vals.append((0, 0, {
                    'name': _('Gain on Disposal - %s') % self.asset_name,
                    'account_id': gain_loss_disposal.id,
                    'debit': 0.0,
                    'credit': abs(gain_loss),
                }))
            else:
                # Loss
                line_vals.append((0, 0, {
                    'name': _('Loss on Disposal - %s') % self.asset_name,
                    'account_id': gain_loss_disposal.id,
                    'debit': abs(gain_loss),
                    'credit': 0.0,
                }))
        
        # Prepare journal entry
        move_vals = {
            'move_type': 'entry',
            'date': fields.Date.today(),
            'ref': _('Initial Recognition (Net Method) - %s') % self.name,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': line_vals,
        }
        
        # Create the journal entry
        move = self.env['account.move'].create(move_vals)
        
        return move

    def _get_default_journal(self, param_name):
        """
        Get configured account journal from settings

        Args:
            param_name: Parameter name (e.g., 'lessor_lease_journal_id')

        Returns:
            account.journal record

        Raises:
            UserError if journal not configured
        """
        journal_id = self.env['ir.config_parameter'].sudo().get_param(
            f'lessor_lease_accounting.{param_name}'
        )

        if not journal_id:
            raise UserError(_(
                "Journal %s is not configured. "
                "Please configure it in Lessor Lease > Configuration > Settings > Lessor Lease Accounting."
            ) % param_name.replace('_', ' ').title())

        journal = self.env['account.journal'].browse(int(journal_id))

        if not journal.exists():
            raise UserError(_('Configured journal (ID: %s) does not exist.') % journal_id)

        return journal

    def _get_account(self, param_name):
        """
        Get configured account from settings
        
        Args:
            param_name: Parameter name (e.g., 'hire_purchase_receivable_account_id')
        
        Returns:
            account.account record
        
        Raises:
            UserError if account not configured
        """
        account_id = self.env['ir.config_parameter'].sudo().get_param(
            f'lessor_lease_accounting.{param_name}'
        )
        
        if not account_id:
            raise UserError(_(
                'Account %s is not configured. '
                'Please configure it in Lessor Lease > Configuration > Settings > Lessor Lease Accounting.'
            ) % param_name.replace('_', ' ').title())
        
        account = self.env['account.account'].browse(int(account_id))
        
        if not account.exists():
            raise UserError(_('Configured account (ID: %s) does not exist.') % account_id)
        
        return account
    
    def action_view_initial_recognition(self):
        """
        View all initial recognition entries
        
        For Gross Method: Shows both receivable and asset entries
        For Net Method: Shows single IFRS 16 entry
        """
        self.ensure_one()
        
        # Search for all initial recognition entries by reference pattern
        initial_entries = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', 'Initial Recognition%' + self.name),
        ])
        
        # If not found by pattern, use the stored move_id
        if not initial_entries and self.initial_recognition_move_id:
            initial_entries = self.initial_recognition_move_id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Initial Recognition Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', initial_entries.ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    # ===== Periodic Accounting Methods (LLA-203) =====
    
    @api.model
    def cron_process_periodic_accounting(self):
        """
        Cron job to process periodic accounting for all active leases
        
        Runs daily to:
        1. Generate installment invoices for due payments
        2. Post VAT recognition entries
        3. Post interest recognition entries
        
        Processes schedule lines where payment_date = today
        Respects accounting_start_date for historical lease migrations
        """
        today = fields.Date.today()
        
        # Find all active contracts
        contracts = self.search([
            ('state', '=', 'active'),
            ('accounting_method', '=', 'gross'),  # Only Gross Method for now
        ])
        
        processed_count = 0
        error_count = 0
        
        for contract in contracts:
            try:
                # Process due schedule lines for this contract
                # Use <= to catch overdue payments (not just today)
                # This ensures missed payments are processed on next cron run
                due_lines = contract.schedule_line_ids.filtered(
                    lambda l: l.payment_date <= today and not l.is_invoiced
                )
                
                # Filter by accounting_start_date if configured (for old lease migrations)
                if contract.accounting_start_date:
                    due_lines = due_lines.filtered(
                        lambda l: l.payment_date >= contract.accounting_start_date
                    )
                
                for line in due_lines:
                    contract._process_periodic_accounting_for_line(line)
                    processed_count += 1
                    
            except Exception as e:
                error_count += 1
                _logger.error(
                    'Error processing periodic accounting for contract %s: %s',
                    contract.name, str(e)
                )
        
        _logger.info(
            'Periodic accounting cron completed. Processed: %d, Errors: %d',
            processed_count, error_count
        )
        
        return True
    
    def _process_periodic_accounting_for_line(self, schedule_line):
        """
        Create and post accounting entries for a single schedule line
        
        Creates all entries and automatically posts them:
        1. Installment invoice (Posted)
        2. VAT recognition entry (Posted)
        3. Interest recognition entry (Posted)
        
        This provides complete automation of the monthly accounting cycle.
        Errors are logged and notified via contract chatter.
        
        Args:
            schedule_line: lessor.lease.schedule.line record
        """
        self.ensure_one()
        
        invoice = None
        vat_move = None
        interest_move = None
        
        try:
            # Step 1: Create and post installment invoice
            invoice = self._create_installment_invoice(schedule_line)
            
            # Step 2: Create and post VAT recognition entry
            vat_move = self._create_vat_recognition_entry(schedule_line)
            
            # Step 3: Create and post interest recognition entry
            interest_move = self._create_interest_recognition_entry(schedule_line)
            
            # Mark line as processed
            schedule_line.write({
                'is_invoiced': True,
                'invoice_id': invoice.id,
            })
            
            # Log success in chatter
            message = Markup("<p>%s<br/>✅ %s<br/>✅ %s<br/>✅ %s</p>") % (
                _('Month %s entries created and posted:', schedule_line.month),
                _('Invoice: %s (Posted)', invoice._get_html_link()),
                _('VAT Entry: %s (Posted)', vat_move._get_html_link()),
                _('Interest Entry: %s (Posted)', interest_move._get_html_link())
            )
            self.message_post(body=message)
            
            return True
            
        except Exception as e:
            error_msg = _('Failed to process Month %s accounting entries: %s') % (schedule_line.month, str(e))
            _logger.error('%s - Contract: %s', error_msg, self.name)
            
            # Notify via chatter
            message = Markup("<p style='color: red;'>⚠️ %s</p>") % error_msg
            self.message_post(
                body=message,
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )
            
            # Re-raise to let cron continue with next contract
            raise
    
    def _create_installment_invoice(self, schedule_line):
        """
        Create and post customer invoice for monthly installment
        
        Args:
            schedule_line: lessor.lease.schedule.line record
            
        Returns:
            account.move: Created invoice (posted state)
        """
        self.ensure_one()
        
        # Prepare invoice values
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.lessee_id.id,
            'invoice_date': schedule_line.payment_date,
            'invoice_date_due': schedule_line.payment_date,
            'invoice_origin': _('%s - Month %s') % (self.name, schedule_line.month),
            'ref': _('Installment %s/%s - %s') % (schedule_line.month, self.term_months, self.name),
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': _('Monthly Installment - %s (Month %s/%s)') % (
                    self.name, schedule_line.month, self.term_months
                ),
                'quantity': 1.0,
                'price_unit': schedule_line.gross_payment,
                'account_id': self._get_installment_revenue_account().id,
            })],
        }
        
        # Create invoice
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Auto-post invoice
        if invoice.line_ids:
            try:
                invoice.action_post()
                _logger.info('Posted invoice %s for contract %s', invoice.name, self.name)
            except Exception as e:
                _logger.error('Failed to post invoice %s: %s', invoice.name, str(e))
                raise
        else:
            error_msg = 'Failed to create invoice lines for contract %s' % self.name
            _logger.error(error_msg)
            raise UserError(_(error_msg))
        
        return invoice
    
    def _create_vat_recognition_entry(self, schedule_line):
        """
        Create and post VAT recognition journal entry
        
        Entry:
        Dr. Undue Output VAT        [VAT amount from schedule]
            Cr. Output VAT          [VAT amount from schedule]
        
        Args:
            schedule_line: lessor.lease.schedule.line record
            
        Returns:
            account.move: Created journal entry (posted state)
        """
        self.ensure_one()
        
        # Get configured accounts
        undue_output_vat = self._get_account('undue_output_vat_account_id')
        output_vat = self._get_account('output_vat_account_id')
        journal = self._get_default_journal('lease_journal_id')
        
        # Prepare journal entry
        move_vals = {
            'move_type': 'entry',
            'date': schedule_line.payment_date,
            'ref': _('VAT Recognition - %s - Month %s') % (self.name, schedule_line.month),
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                # Dr. Undue Output VAT
                (0, 0, {
                    'name': _('Undue Output VAT - %s - Month %s') % (self.name, schedule_line.month),
                    'account_id': undue_output_vat.id,
                    'debit': schedule_line.vat,
                    'credit': 0.0,
                }),
                # Cr. Output VAT
                (0, 0, {
                    'name': _('Output VAT Payable - %s - Month %s') % (self.name, schedule_line.month),
                    'account_id': output_vat.id,
                    'debit': 0.0,
                    'credit': schedule_line.vat,
                }),
            ],
        }
        
        # Create journal entry
        move = self.env['account.move'].create(move_vals)
        
        # Auto-post entry
        if move.line_ids:
            try:
                move.action_post()
                _logger.info('Posted VAT entry %s for contract %s', move.name, self.name)
            except Exception as e:
                _logger.error('Failed to post VAT entry %s: %s', move.name, str(e))
                raise
        else:
            error_msg = 'Failed to create VAT entry lines for contract %s' % self.name
            _logger.error(error_msg)
            raise UserError(_(error_msg))
        
        return move
    
    def _create_interest_recognition_entry(self, schedule_line):
        """
        Create and post interest recognition journal entry
        
        Entry:
        Dr. Deferred Interest      [Interest amount from schedule]
            Cr. Interest Income     [Interest amount from schedule]
        
        Args:
            schedule_line: lessor.lease.schedule.line record
            
        Returns:
            account.move: Created journal entry (posted state)
        """
        self.ensure_one()
        
        # Get configured accounts
        deferred_interest = self._get_account('deferred_interest_account_id')
        interest_income = self._get_account('interest_income_account_id')
        journal = self._get_default_journal('lease_journal_id')
        
        # Prepare journal entry
        move_vals = {
            'move_type': 'entry',
            'date': schedule_line.payment_date,
            'ref': _('Interest Recognition - %s - Month %s') % (self.name, schedule_line.month),
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'currency_id': self.currency_id.id,
            'line_ids': [
                # Dr. Deferred Interest
                (0, 0, {
                    'name': _('Deferred Interest - %s - Month %s') % (self.name, schedule_line.month),
                    'account_id': deferred_interest.id,
                    'debit': schedule_line.interest,
                    'credit': 0.0,
                }),
                # Cr. Interest Income
                (0, 0, {
                    'name': _('Interest Income - %s - Month %s') % (self.name, schedule_line.month),
                    'account_id': interest_income.id,
                    'debit': 0.0,
                    'credit': schedule_line.interest,
                }),
            ],
        }
        
        # Create journal entry
        move = self.env['account.move'].create(move_vals)
        
        # Auto-post entry
        if move.line_ids:
            try:
                move.action_post()
                _logger.info('Posted interest entry %s for contract %s', move.name, self.name)
            except Exception as e:
                _logger.error('Failed to post interest entry %s: %s', move.name, str(e))
                raise
        else:
            error_msg = 'Failed to create interest entry lines for contract %s' % self.name
            _logger.error(error_msg)
            raise UserError(_(error_msg))
        
        return move
    
    def _get_installment_revenue_account(self):
        """
        Get the account for installment revenue

        PER PDF SPECIFICATION (E1.1):
        Monthly installment invoice must post to HP Receivable (113104),
        NOT Lease Sales. Lease Sales is only credited at initial recognition.

        This prevents Lease Sales from being credited every month.

        Returns:
            account.account: HP Receivable account
        """
        return self._get_account('hire_purchase_receivable_account_id')
    
    # ===== Navigation Actions for Monthly Invoices and Entries =====
    
    def action_view_draft_invoices(self):
        """View draft monthly invoices only"""
        self.ensure_one()
        invoice_ids = self.schedule_line_ids.mapped('invoice_id').filtered(
            lambda inv: inv and inv.state == 'draft'
        ).ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Draft Invoices - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'create': False,
            },
        }
    
    def action_view_unpaid_invoices(self):
        """View posted but unpaid/partially paid invoices"""
        self.ensure_one()
        invoice_ids = self.schedule_line_ids.mapped('invoice_id').filtered(
            lambda inv: inv and inv.state == 'posted' and inv.payment_state in ['not_paid', 'partial']
        ).ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unpaid Invoices - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'create': False,
            },
        }
    
    def action_view_paid_invoices(self):
        """View fully paid invoices"""
        self.ensure_one()
        invoice_ids = self.schedule_line_ids.mapped('invoice_id').filtered(
            lambda inv: inv and inv.state == 'posted' and inv.payment_state in ['paid', 'in_payment']
        ).ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Paid Invoices - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', invoice_ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'create': False,
            },
        }
    
    def action_view_draft_entries(self):
        """View draft monthly journal entries only"""
        self.ensure_one()
        entry_ids = self.schedule_line_ids.mapped('move_id').filtered(
            lambda move: move and move.state == 'draft'
        ).ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Draft Journal Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', entry_ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    def action_view_posted_entries(self):
        """View posted monthly journal entries only"""
        self.ensure_one()
        entry_ids = self.schedule_line_ids.mapped('move_id').filtered(
            lambda move: move and move.state == 'posted'
        ).ids
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Posted Journal Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', entry_ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    def action_view_draft_vat_entries(self):
        """View draft VAT recognition entries"""
        self.ensure_one()
        vat_entries = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', 'VAT Recognition - %s -' % self.name),
            ('state', '=', 'draft'),
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Draft VAT Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', vat_entries.ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    def action_view_posted_vat_entries(self):
        """View posted VAT recognition entries"""
        self.ensure_one()
        vat_entries = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', 'VAT Recognition - %s -' % self.name),
            ('state', '=', 'posted'),
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Posted VAT Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', vat_entries.ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    def action_view_draft_interest_entries(self):
        """View draft Interest recognition entries"""
        self.ensure_one()
        interest_entries = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', 'Interest Recognition - %s -' % self.name),
            ('state', '=', 'draft'),
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Draft Interest Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', interest_entries.ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
    
    def action_view_posted_interest_entries(self):
        """View posted Interest recognition entries"""
        self.ensure_one()
        interest_entries = self.env['account.move'].search([
            ('move_type', '=', 'entry'),
            ('ref', 'ilike', 'Interest Recognition - %s -' % self.name),
            ('state', '=', 'posted'),
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Posted Interest Entries - %s') % self.name,
            'res_model': 'account.move',
            'domain': [('id', 'in', interest_entries.ids)],
            'view_mode': 'list,form',
            'target': 'current',
            'context': {
                'default_move_type': 'entry',
                'create': False,
            },
        }
