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
        string='Billed Quantity',
        digits='Product Unit of Measure'
    )

    delivered_qty = fields.Float(
        string='Received Quantity',
        digits='Product Unit of Measure'
    )

    available_qty = fields.Float(
        string='Available for Return',
        digits='Product Unit of Measure',
        compute='_compute_available_qty', store=True
    )

    return_qty = fields.Float(
        string='Return Quantity',
        digits='Product Unit of Measure'
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

    notes = fields.Text(string='Notes')

    return_amount = fields.Monetary(
        string='Return Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='return_request_id.currency_id',
        store=True
    )

    move_id = fields.Many2one('stock.move', "Move")

    already_returned_qty = fields.Float(
        string="Already Returned",
        digits="Product Unit of Measure",
        compute="_compute_already_returned_qty",
        store=True
    )

    @api.depends('product_id', 'return_request_id.partner_id')
    def _compute_already_returned_qty(self):
        for line in self:
            qty = 0.0
            if line.product_id and line.return_request_id.partner_id:
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

    @api.depends('return_qty', 'price_unit')
    def _compute_amounts(self):
        for line in self:
            line.return_amount = line.return_qty * line.price_unit

    @api.constrains('return_qty', 'available_qty')
    def _check_return_qty(self):
        for line in self:
            if line.return_qty > line.available_qty:
                raise ValidationError(
                    _('Return quantity cannot exceed available quantity for product %s.')
                    % line.product_id.name
                )

    @api.constrains('return_qty')
    def _check_quantities(self):
        for line in self:
            if line.return_qty < 0:
                raise ValidationError(_('Return quantity cannot be negative.'))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.name
            self.price_unit = self.product_id.standard_price
