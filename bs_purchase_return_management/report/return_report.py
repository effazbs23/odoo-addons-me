from odoo import fields, models, tools


class ReturnReport(models.Model):
    _name = 'return.report'
    _description = 'Purchase Return Analysis Report'
    _auto = False
    _rec_name = 'return_request_id'

    return_request_id = fields.Many2one('return.request', string='Return Request')
    partner_id = fields.Many2one('res.partner', string='Vendor')
    product_id = fields.Many2one('product.product', string='Product')
    return_qty = fields.Float(string='Return Quantity')
    return_amount = fields.Float(string='Return Amount')
    request_date = fields.Datetime(string='Request Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status')
    return_reason = fields.Selection([
        ('defective', 'Defective'),
        ('wrong_item', 'Wrong Item'),
        ('damaged', 'Damaged'),
        ('not_needed', 'Not Needed'),
        ('quality_issue', 'Quality Issue'),
        ('other', 'Other')
    ], string='Return Reason')
    user_id = fields.Many2one('res.users', string='Responsible')
    company_id = fields.Many2one('res.company', string='Company')

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    row_number() OVER () AS id,
                    rr.id AS return_request_id,
                    rr.partner_id,
                    rl.product_id,
                    rl.return_qty,
                    rl.return_amount,
                    rr.request_date,
                    rr.state,
                    rl.return_reason,
                    rr.user_id,
                    rr.company_id,
                    rr.purchase_order_id,
                    rl.lot_id
                FROM return_request rr
                LEFT JOIN return_request_line rl ON rr.id = rl.return_request_id
                WHERE rl.id IS NOT NULL
            )
        """ % self._table)
