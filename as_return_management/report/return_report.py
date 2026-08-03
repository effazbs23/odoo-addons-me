from odoo import fields, models, tools


class ReturnReport(models.Model):
    _name = 'return.report'
    _description = 'Return Analysis Report'
    _auto = False
    _rec_name = 'return_request_id'

    return_request_id = fields.Many2one('return.request', string='Return Request')
    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Product')
    return_qty = fields.Float(string='Return Quantity')
    replacement_qty = fields.Float(string='Replacement Quantity')
    return_amount = fields.Float(string='Return Amount')
    replacement_amount = fields.Float(string='Replacement Amount')
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

    return_operation_type = fields.Selection([
        ('customer', 'Customer Return'),
        ('vendor', 'Vendor Return')
    ], string='Operation Type')

    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial')

    # Add new fields for gross returns
    # Add new fields for gross returns
    is_gross_return = fields.Boolean(string='Is Gross Return')
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

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
                                          related='company_id.currency_id')
    gross_total_cost = fields.Monetary(string='Total Cost Value', currency_field='company_currency_id')



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
                    rl.replacement_qty,
                    rl.return_amount,
                    rl.replacement_amount,
                    rr.request_date,
                    rr.state,
                    rl.return_reason,
                    rr.user_id,
                    rr.company_id,
                    rr.return_operation_type,
                    rr.purchase_order_id,
                    rl.lot_id,
                    rr.is_gross_return,
                    rr.gross_return_type,
                    rr.gross_return_source,
                    rr.warehouse_id,
                    rr.gross_total_cost
                FROM return_request rr
                LEFT JOIN return_request_line rl ON rr.id = rl.return_request_id
                WHERE rl.id IS NOT NULL
            )
        """ % self._table)