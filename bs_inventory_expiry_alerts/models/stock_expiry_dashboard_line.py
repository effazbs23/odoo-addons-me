from odoo import fields, models, tools


class StockExpiryDashboardLine(models.Model):
    _name = 'stock.expiry.dashboard.line'
    _description = 'Expiry Dashboard Line'
    _auto = False
    _order = 'days_to_expiry'

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    categ_id = fields.Many2one('product.category', string='Product Category', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lot/Serial', readonly=True)
    location_id = fields.Many2one('stock.location', string='Location', readonly=True)
    expiration_date = fields.Datetime(string='Expiration Date', readonly=True)
    quantity = fields.Float(string='Quantity', readonly=True)
    days_to_expiry = fields.Integer(string='Days to Expiry', readonly=True)
    expiry_bucket = fields.Selection([
        ('expired', 'Expired'),
        ('0_7', '0-7 Days'),
        ('8_30', '8-30 Days'),
        ('31_90', '31-90 Days'),
        ('90_plus', '90+ Days'),
    ], string='Expiry Bucket', readonly=True)
    suggested_action = fields.Selection([
        ('markdown', 'Suggest Markdown/Promotion'),
        ('transfer', 'Suggest Internal Transfer'),
    ], string='Suggested Action', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    q.id AS id,
                    q.product_id AS product_id,
                    pt.categ_id AS categ_id,
                    loc.warehouse_id AS warehouse_id,
                    q.lot_id AS lot_id,
                    q.location_id AS location_id,
                    sl.expiration_date AS expiration_date,
                    q.quantity AS quantity,
                    (sl.expiration_date::date - CURRENT_DATE) AS days_to_expiry,
                    CASE
                        WHEN (sl.expiration_date::date - CURRENT_DATE) < 0 THEN 'expired'
                        WHEN (sl.expiration_date::date - CURRENT_DATE) <= 7 THEN '0_7'
                        WHEN (sl.expiration_date::date - CURRENT_DATE) <= 30 THEN '8_30'
                        WHEN (sl.expiration_date::date - CURRENT_DATE) <= 90 THEN '31_90'
                        ELSE '90_plus'
                    END AS expiry_bucket,
                    CASE
                        WHEN (sl.expiration_date::date - CURRENT_DATE) > COALESCE(
                            NULLIF(pc.expiry_alert_days, 0),
                            (SELECT COALESCE(NULLIF(value, '')::int, 30) FROM ir_config_parameter
                             WHERE key = 'bs_inventory_expiry_alerts.expiry_alert_days_default')
                        ) THEN NULL
                        WHEN (sl.expiration_date::date - CURRENT_DATE) <= COALESCE(
                            NULLIF(pc.expiry_alert_days, 0),
                            (SELECT COALESCE(NULLIF(value, '')::int, 30) FROM ir_config_parameter
                             WHERE key = 'bs_inventory_expiry_alerts.expiry_alert_days_default')
                        ) / 2.0 THEN 'markdown'
                        ELSE 'transfer'
                    END AS suggested_action
                FROM stock_quant q
                JOIN stock_lot sl ON sl.id = q.lot_id
                JOIN product_product pp ON pp.id = q.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                LEFT JOIN product_category pc ON pc.id = pt.categ_id
                JOIN stock_location loc ON loc.id = q.location_id
                WHERE q.quantity > 0
                  AND loc.usage = 'internal'
                  AND sl.expiration_date IS NOT NULL
            )
        """)
