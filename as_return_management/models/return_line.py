from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ReturnRequestLine(models.Model):
    _name = 'return.request.line'
    _description = 'Return Request Line'

    return_request_id = fields.Many2one(
        'return.request',
        string='Return Request',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True
    )

    description = fields.Text(string='Description')
    uom_id = fields.Many2one(related='product_id.uom_id', string='UOM', readonly=True, store=True)

    invoiced_qty = fields.Float(
        string='Invoiced Quantity',
        digits='Product Unit of Measure'
    )

    delivered_qty = fields.Float(
        string='Delivered Quantity',
        digits='Product Unit of Measure'
    )

    available_qty = fields.Float(
        string='Available for Return',
        digits='Product Unit of Measure'
        ,compute='_compute_available_qty', store=True
    )

    return_qty = fields.Float(
        string='Return Quantity',
        digits='Product Unit of Measure'
    )

    replacement_qty = fields.Float(
        string='Replacement Quantity',
        digits='Product Unit of Measure'
    )

    replacement_product_id = fields.Many2one(
        'product.product',
        string='Replacement Product'
    )

    price_unit = fields.Float(
        string='Unit Price',
        digits='Product Price'
    )

    return_reason = fields.Selection([
        ('defective', 'Defective'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged'),
        ('not_needed', 'Not Needed'),
        ('quality_issue', 'Quality Issue'),
        ('other', 'Other')
    ], string='Return Reason')

    return_condition = fields.Selection([
        ('new', 'New'),
        ('used', 'Used'),
        ('damaged', 'Damaged'),
        ('defective', 'Defective')
    ], string='Return Condition')

    action_type = fields.Selection([
        ('return', 'Return'),
        ('replace', 'Replace'),
        #('return_replace', 'Return & Replace')
    ], string='Action', default='return')

    notes = fields.Text(string='Notes')

    # Computed fields
    return_amount = fields.Monetary(
        string='Return Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )

    replacement_amount = fields.Monetary(
        string='Replacement Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='return_request_id.currency_id',
        store=True
    )

    move_id = fields.Many2one( 'stock.move', "Move")

    already_returned_qty = fields.Float(
        string="Already Returned",
        digits="Product Unit of Measure",
        compute="_compute_already_returned_qty",
        store=True  # or True if you want to persist in db
    )

    # Add computed field for cost price in gross returns
    cost_price = fields.Float(
        string='Cost Price',
        compute='_compute_cost_price',
        store=True,
        help='Cost price for gross returns'
    )

    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        currency_field='currency_id',
        help='Total cost for gross return line'
    )


    @api.depends('product_id', 'return_request_id.partner_id')
    def _compute_already_returned_qty(self):
        for line in self:
            qty = 0.0
            if line.product_id and line.return_request_id.partner_id:
                # sum of return_qty for this product & partner in posted return requests
                other_lines = self.env['return.request.line'].search([
                    ('product_id', '=', line.product_id.id),
                    ('return_request_id.partner_id', '=', line.return_request_id.partner_id.id),
                    ('id', '!=', line.id),
                ])
                qty = sum(other_lines.mapped('return_qty'))
            line.already_returned_qty = qty

    @api.depends('delivered_qty', 'already_returned_qty')
    def _compute_available_qty(self):
        for line in self:
            line.available_qty = line.delivered_qty - line.already_returned_qty

    @api.depends('return_qty', 'replacement_qty', 'price_unit', 'replacement_product_id')
    def _compute_amounts(self):
        for line in self:
            line.return_amount = line.return_qty * line.price_unit
            replacement_price = (
                line.replacement_product_id.list_price
                if line.replacement_product_id
                else line.price_unit
            )
            line.replacement_amount = line.replacement_qty * replacement_price

    @api.constrains('return_qty', 'available_qty')
    def _check_return_qty(self):
        for line in self:
            if line.return_qty > line.available_qty:
                raise ValidationError(
                    _('Return quantity cannot exceed available quantity for product %s')
                    % line.product_id.name
                )

    @api.constrains('return_qty', 'replacement_qty')
    def _check_quantities(self):
        for line in self:
            if line.return_qty < 0:
                raise ValidationError(_('Return quantity cannot be negative.'))
            if line.replacement_qty < 0:
                raise ValidationError(_('Replacement quantity cannot be negative.'))

    @api.onchange('action_type')
    def _onchange_action_type(self):
        if self.action_type == 'return':
            self.replacement_qty = 0
            self.replacement_product_id = False
        elif self.action_type == 'replace':
            self.return_qty = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.price_unit = self.product_id.list_price

    # Compute cost price for gross returns
    @api.depends('product_id')
    def _compute_cost_price(self):
        for line in self:
            if line.return_request_id.is_gross_return and line.product_id:
                line.cost_price = line.product_id.standard_price
            else:
                line.cost_price = 0

    @api.depends('return_qty', 'cost_price')
    def _compute_total_cost(self):
        for line in self:
            if line.return_request_id.is_gross_return:
                line.total_cost = line.return_qty * line.cost_price
            else:
                line.total_cost = 0

    @api.constrains('return_qty', 'available_qty')
    def _check_return_qty(self):
        for line in self:
            if not line.return_request_id.is_gross_return:
                # Apply existing validation only for regular returns
                if line.return_qty > line.available_qty:
                    raise ValidationError(
                        _('Return quantity cannot exceed available quantity for product %s.')
                        % line.product_id.name
                    )

