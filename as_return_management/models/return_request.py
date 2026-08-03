from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class ReturnRequest(models.Model):
    _name = 'return.request'
    _description = 'Return Request'
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
        string='Customer',
        required=True,
        tracking=True
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

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice'), ('state', '=', 'posted')]
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery Order',
        domain=[('picking_type_code', '=', 'outgoing'), ('state', '=', 'done')]
    )

    return_line_ids = fields.One2many(
        'return.request.line',
        'return_request_id',
        string='Return Lines'
    )

    reason = fields.Text(string='Return Reason')

    # Computed fields
    total_return_qty = fields.Float(
        string='Total Return Quantity',
        compute='_compute_totals',
        store=True
    )

    total_replacement_qty = fields.Float(
        string='Total Replacement Quantity',
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

    # Generated documents
    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Return Receipt',
        readonly=True
    )

    replacement_picking_id = fields.Many2one(
        'stock.picking',
        string='Replacement Delivery',
        readonly=True
    )

    credit_note_id = fields.Many2one(
        'account.move',
        string='Credit Note',
        readonly=True
    )

    replacement_invoice_id = fields.Many2one(
        'account.move',
        string='Replacement Invoice',
        readonly=True
    )

    # Additional fields
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')

    return_type = fields.Selection([
        ('return_only', 'Return Only'),
        ('replacement_only', 'Replacement Only'),
        ('return_replacement', 'Return & Replacement')
    ], string='Return Type', compute='_compute_return_type', store=True)

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

    # fields for gross returns
    is_gross_return = fields.Boolean(
        string='Is Gross Return',
        default=False,
        help='Return without invoice reference'
    )

    gross_return_type = fields.Selection([
        ('damaged_goods', 'Damaged Goods'),
        ('expired_products', 'Expired Products'),
        ('quality_control', 'Quality Control Rejection'),
        ('overstock', 'Overstock Return'),
        ('promotional_return', 'Promotional Return'),
        ('sample_return', 'Sample Return'),
        ('other', 'Other')
    ], string='Gross Return Type')

    gross_return_source = fields.Selection([
        ('warehouse', 'Warehouse'),
        ('retail_store', 'Retail Store'),
        ('field_sales', 'Field Sales'),
        ('customer_direct', 'Customer Direct'),
        ('supplier', 'Supplier'),
        ('production', 'Production'),
        ('other', 'Other')
    ], string='Return Source')

    reference_document = fields.Char(
        string='Reference Document',
        help='Any reference document number for gross return'
    )

    gross_return_date = fields.Date(
        string='Gross Return Date',
        help='Date when goods were actually returned'
    )

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        help='Warehouse where goods are being returned'
    )

    responsible_person = fields.Char(
        string='Responsible Person',
        help='Person responsible for the return'
    )

    gross_total_cost = fields.Monetary(
        string='Total Cost Value',
        compute='_compute_gross_totals',
        store=True,
        currency_field='currency_id',
        help='Total cost value for gross returns'
    )

    ##################################################################

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('return.request') or _('New')

        return super().create(vals_list)

    @api.depends('return_line_ids.return_qty', 'return_line_ids.replacement_qty', 'return_line_ids.price_unit')
    def _compute_totals(self):
        for record in self:
            record.total_return_qty = sum(record.return_line_ids.mapped('return_qty'))
            record.total_replacement_qty = sum(record.return_line_ids.mapped('replacement_qty'))
            record.total_return_amount = sum(
                line.return_qty * line.price_unit for line in record.return_line_ids
            )

    @api.depends('return_line_ids.return_qty', 'return_line_ids.replacement_qty')
    def _compute_return_type(self):
        for record in self:
            has_return = any(line.return_qty > 0 for line in record.return_line_ids)
            has_replacement = any(line.replacement_qty > 0 for line in record.return_line_ids)

            if has_return and has_replacement:
                record.return_type = 'return_replacement'
            elif has_return:
                record.return_type = 'return_only'
            elif has_replacement:
                record.return_type = 'replacement_only'
            else:
                record.return_type = 'return_only'

    @api.onchange('picking_id')
    def _onchange_documents(self):
        if self.invoice_id or self.picking_id:
            self._generate_return_lines()

    def _generate_return_lines(self):

        if self.return_operation_type == 'vendor':
            # Vendor returns build their lines in _generate_po_return_lines,
            # triggered from the purchase_order_id onchange (vendor_return.py)
            return

        if self.is_gross_return:
            # For gross returns, lines are manually created
            return

        """Generate return lines based on selected invoice and picking"""
        self.return_line_ids = [(5, 0, 0)]  # Clear existing lines

        lines_data = {}

        # Get lines from invoice
        if self.invoice_id:
            for line in self.invoice_id.invoice_line_ids:
                if line.product_id and line.product_id.type in ['product', 'consu']:
                    key = line.product_id.id
                    lines_data[key] = {
                        'product_id': line.product_id.id,
                        'description': line.name,
                        'invoiced_qty': line.quantity,
                        'delivered_qty': 0,
                        'price_unit': line.price_unit,
                        'available_qty': line.quantity,
                        'move_id': 0,
                    }

        # Get lines from picking
        if self.picking_id:
            for move in self.picking_id.move_ids:
                key = move.product_id.id
                if key in lines_data:
                    lines_data[key]['delivered_qty'] = move.quantity
                    lines_data[key]['available_qty'] = min(
                        lines_data[key]['invoiced_qty'],
                        move.quantity
                    )
                    lines_data[key]['move_id'] = move.id
                else:
                    lines_data[key] = {
                        'product_id': move.product_id.id,
                        'description': move.product_id.name,
                        'invoiced_qty': 0,
                        'delivered_qty': move.quantity,
                        'price_unit': move.product_id.list_price,
                        'available_qty': move.quantity,
                        'move_id': move.id,
                    }

        # Create return lines
        line_vals = []
        for data in lines_data.values():
            line_vals.append((0, 0, data))

        self.return_line_ids = line_vals

    def action_submit(self):
        """Submit return request for approval"""
        if not self.return_line_ids:
            raise UserError(_('Please add at least one return line.'))
        # check if at least one return or replacement quantity is set
        if not any(line.return_qty > 0 or line.replacement_qty > 0 for line in self.return_line_ids):
            raise UserError(_('Please specify return or replacement quantities.'))

        self.state = 'submitted'
        self.message_post(body=_('Return request submitted for approval.'))

    def action_approve(self):
        """Approve return request"""
        if self.is_gross_return:
            # Auto-process gross returns
            self.action_process_gross_return()
            self.state = 'processing'
        else:
            self.state = 'approved'
        self.message_post(body=_('Return request approved.'))

    def action_process(self):
        """Process the return request"""
        self.state = 'processing'

        # Create return picking if there are returns
        if any(line.return_qty > 0 for line in self.return_line_ids):
            self._create_return_picking()

        # Create replacement picking if there are replacements
        if any(line.replacement_qty > 0 for line in self.return_line_ids):
            self._create_replacement_picking()

        # Create credit note
        if self.invoice_id and any(line.return_qty > 0 for line in self.return_line_ids):
            self._create_credit_note()

        # Create replacement invoice
        if any(line.replacement_qty > 0 for line in self.return_line_ids):
            self._create_replacement_invoice()

    def _create_return_picking(self):
        """Create return picking for returned items"""
        picking_type = self._get_return_picking_type()
        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': self.partner_id.property_stock_customer.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'return_id': self.picking_id.id,
            'origin': _("Return of %(picking_name)s", picking_name=self.picking_id.name),
            'company_id': self.company_id.id,
            'sale_id': self.picking_id.sale_id.id,
        }

        picking = self.env['stock.picking'].create(picking_vals)

        # Create moves for returned items
        for line in self.return_line_ids.filtered(lambda l: l.return_qty > 0):
            move_vals = {
                'product_id': line.product_id.id,
                'product_uom_qty': line.return_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'company_id': self.company_id.id,
                'origin_returned_move_id': line.move_id.id if line.move_id else False,
                'origin': line.move_id.origin if line.move_id else False,
                'description_picking': line.move_id.description_picking if line.move_id else False,
                'sale_line_id': line.move_id.sale_line_id.id if line.move_id else False,
            }

            self.env['stock.move'].create(move_vals)

        picking.action_confirm()
        picking.button_validate()
        self.return_picking_id = picking.id

    def _create_replacement_picking(self):
        """Create replacement picking for replacement items"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_('No outgoing picking type found.'))

        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': self.partner_id.property_stock_customer.id,
            'origin': self.name,
            'company_id': self.company_id.id,
        }

        picking = self.env['stock.picking'].create(picking_vals)

        # Create moves for replacement items
        for line in self.return_line_ids.filtered(lambda l: l.replacement_qty > 0):
            replacement_product = line.replacement_product_id or line.product_id
            move_vals = {
                'name': replacement_product.name,
                'product_id': replacement_product.id,
                'product_uom_qty': line.replacement_qty,
                'product_uom': replacement_product.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'company_id': self.company_id.id,
            }
            self.env['stock.move'].create(move_vals)

        picking.action_confirm()
        self.replacement_picking_id = picking.id

    def _create_credit_note(self):
        """Create credit note for returned items"""
        if not self.invoice_id:
            return

        credit_note_vals = {
            'move_type': 'out_refund',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=self.invoice_id.name, reason=self.reason)
            if self.reason
            else _('Reversal of: %s', self.invoice_id.name),
            'company_id': self.company_id.id,
            'currency_id': self.invoice_id.currency_id.id,
            'reversed_entry_id': self.invoice_id.id,
            'invoice_origin': self.invoice_id.invoice_origin,
        }

        credit_note = self.env['account.move'].create(credit_note_vals)

        # Create credit note lines
        for line in self.return_line_ids.filtered(lambda l: l.return_qty > 0):
            line_vals = {
                'move_id': credit_note.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'quantity': line.return_qty,
                'price_unit': line.price_unit,
                'account_id': line.product_id.property_account_income_id.id or
                              line.product_id.categ_id.property_account_income_categ_id.id,
                'ref': _('Reversal of: %(move_name)s, %(reason)s', move_name=self.invoice_id.name, reason=self.reason)
                if self.reason else _('Reversal of: %s', self.invoice_id.name),
            }
            self.env['account.move.line'].create(line_vals)

        credit_note.action_post()
        self.credit_note_id = credit_note.id

    def _create_replacement_invoice(self):
        """Create invoice for replacement items"""
        replacement_lines = self.return_line_ids.filtered(lambda l: l.replacement_qty > 0)
        if not replacement_lines:
            return

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'ref': f'Replacement: {self.name}',
            'company_id': self.company_id.id,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Create invoice lines for replacements
        for line in replacement_lines:
            replacement_product = line.replacement_product_id or line.product_id
            line_vals = {
                'move_id': invoice.id,
                'product_id': replacement_product.id,
                'name': replacement_product.name,
                'quantity': line.replacement_qty,
                'price_unit': replacement_product.list_price,
                'account_id': replacement_product.property_account_income_id.id or
                              replacement_product.categ_id.property_account_income_categ_id.id,
            }
            self.env['account.move.line'].create(line_vals)

        self.replacement_invoice_id = invoice.id

    def action_done(self):
        """Mark return request as done"""
        self.state = 'done'
        self.message_post(body=_('Return request completed.'))

    def action_cancel(self):
        """Cancel return request"""
        self.state = 'cancelled'
        self.message_post(body=_('Return request cancelled.'))

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.state = 'draft'

    def action_view_return_picking(self):
        """View return picking"""
        if self.return_picking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Return Receipt'),
                'res_model': 'stock.picking',
                'res_id': self.return_picking_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_replacement_picking(self):
        """View replacement picking"""
        if self.replacement_picking_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Replacement Delivery'),
                'res_model': 'stock.picking',
                'res_id': self.replacement_picking_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_credit_note(self):
        """View credit note"""
        if self.credit_note_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Credit Note'),
                'res_model': 'account.move',
                'res_id': self.credit_note_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_replacement_invoice(self):
        """View replacement invoice"""
        if self.replacement_invoice_id:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Replacement Invoice'),
                'res_model': 'account.move',
                'res_id': self.replacement_invoice_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    # gross return computations
    @api.model
    def _get_default_warehouse(self):
        return self.env['stock.warehouse'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)

    # Add computed field to show different totals for gross returns
    @api.depends('return_line_ids.return_qty', 'return_line_ids.product_id', 'is_gross_return')
    def _compute_gross_totals(self):
        for record in self:
            if record.is_gross_return:
                total_cost = 0
                for line in record.return_line_ids:
                    # Use standard cost for gross returns
                    cost_price = line.product_id.standard_price
                    total_cost += line.return_qty * cost_price
                record.gross_total_cost = total_cost
            else:
                record.gross_total_cost = 0

    @api.onchange('is_gross_return')
    def _onchange_is_gross_return(self):
        if self.is_gross_return:
            self.invoice_id = False
            self.picking_id = False
            self.return_type = 'return_only'
            if not self.warehouse_id:
                self.warehouse_id = self._get_default_warehouse()
        else:
            self.gross_return_type = False
            self.gross_return_source = False
            self.warehouse_id = False

    @api.constrains('is_gross_return', 'invoice_id', 'picking_id')
    def _check_gross_return_constraints(self):
        for record in self:
            if record.is_gross_return and (record.invoice_id or record.picking_id):
                raise ValidationError(_('Gross returns cannot have invoice or delivery order references.'))
            if not record.is_gross_return and not record.invoice_id and not record.picking_id:
                raise ValidationError(_('Regular returns must have either invoice or delivery order reference.'))

    def action_process_gross_return(self):
        """Process gross return - create stock moves"""
        if not self.is_gross_return:
            return

        if not self.return_line_ids:
            raise UserError(_('Please add return lines before processing.'))

        # Create stock picking for gross return
        picking_vals = {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'picking_type_id': self._get_return_picking_type().id,
            'location_id': self.warehouse_id.lot_stock_id.id if self.warehouse_id else self._get_customer_location().id,
            'location_dest_id': self._get_return_location().id,
            'origin': self.name,
            'move_type': 'direct',
        }

        picking = self.env['stock.picking'].create(picking_vals)

        for line in self.return_line_ids.filtered(lambda l: l.return_qty > 0):
            move_vals = {
                'name': line.product_id.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.return_qty,
                'product_uom': line.product_id.uom_id.id,
                'picking_id': picking.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
            }
            self.env['stock.move'].create(move_vals)

        self.return_picking_id = picking.id
        picking.action_confirm()
        picking.button_validate()

        # Create credit note for gross return
        credit_note_vals = {
            'move_type': 'out_refund',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'ref': self.name,
            'company_id': self.company_id.id,
            'currency_id': self.env.user.company_id.currency_id.id,
            'stock_move_id': picking.id,
        }

        credit_note = self.env['account.move'].create(credit_note_vals)

        # Create credit note lines
        for line in self.return_line_ids.filtered(lambda l: l.return_qty > 0):
            line_vals = {
                'move_id': credit_note.id,
                'product_id': line.product_id.id,
                'name': line.description,
                'quantity': line.return_qty,
                'price_unit': line.price_unit,
                'account_id': line.product_id.property_account_income_id.id or
                              line.product_id.categ_id.property_account_income_categ_id.id,
            }
            self.env['account.move.line'].create(line_vals)

        credit_note.action_post()
        self.credit_note_id = credit_note.id

        self.message_post(
            body=_('Gross return picking %s created.') % picking.name
        )

    def _get_return_picking_type(self):
        """Create replacement picking for replacement items"""
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id)
        ], limit=1)

        if not picking_type:
            raise UserError(_('No incoming picking type found.'))
        return picking_type

    def _get_return_location(self):
        """Return location where customer will send products back for this warehouse."""
        self.ensure_one()
        if not self.warehouse_id:
            raise UserError(_("Please set a warehouse on the return request."))

        # Otherwise, fallback to main stock location
        return self.warehouse_id.lot_stock_id
