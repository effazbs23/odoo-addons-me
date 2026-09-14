from odoo import api, fields, models, tools

_CHART_BUCKETS = [
    ('0-7', lambda d: d <= 7),
    ('8-14', lambda d: 8 <= d <= 14),
    ('15-30', lambda d: 15 <= d <= 30),
    ('31-60', lambda d: 31 <= d <= 60),
    ('61+', lambda d: d > 60),
]
_STATUS_COLORS = {'critical': '#DC3545', 'warning': '#F0AD4E', 'watch': '#6C757D'}


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

    @api.model
    def get_dashboard_data(self):
        lines = self.search_read(
            [], ['product_id', 'warehouse_id', 'lot_id', 'location_id',
                 'expiration_date', 'quantity', 'days_to_expiry', 'suggested_action'])
        product_ids = {line['product_id'][0] for line in lines if line['product_id']}
        prices = {p.id: p.standard_price for p in self.env['product.product'].browse(product_ids)}

        expiring_soon = at_risk = safe = 0
        value_at_risk = 0.0
        bucket_counts = {label: 0 for label, _ in _CHART_BUCKETS}
        warehouse_counts = {}
        table_rows = []

        for line in lines:
            days = line['days_to_expiry']
            qty = line['quantity']
            price = prices.get(line['product_id'][0], 0.0) if line['product_id'] else 0.0

            if days <= 7:
                expiring_soon += 1
                status = 'critical'
            elif days <= 30:
                at_risk += 1
                status = 'warning' if days <= 14 else 'watch'
            else:
                safe += 1
                status = 'watch'

            if days <= 30:
                value_at_risk += qty * price

            for label, test in _CHART_BUCKETS:
                if test(days):
                    bucket_counts[label] += 1
                    break

            wh_name = line['warehouse_id'][1] if line['warehouse_id'] else 'N/A'
            warehouse_counts[wh_name] = warehouse_counts.get(wh_name, 0) + 1

            table_rows.append({
                'product_name': line['product_id'][1] if line['product_id'] else '',
                'lot_name': line['lot_id'][1] if line['lot_id'] else '',
                'warehouse_name': wh_name,
                'expiration_date': line['expiration_date'],
                'days_to_expiry': days,
                'status': status,
                'quant_id': line['id'],
            })

        table_rows.sort(key=lambda r: r['days_to_expiry'])
        total_lots = len(lines) or 1
        palette = ['#4472C4', '#ED7D31', '#FFC000', '#70AD47', '#255E91']
        by_warehouse = [
            {
                'name': name,
                'count': count,
                'percentage': round(count * 100.0 / total_lots),
                'color': palette[i % len(palette)],
            }
            for i, (name, count) in enumerate(sorted(warehouse_counts.items(), key=lambda kv: -kv[1]))
        ]

        markdown_count = sum(1 for line in lines if line['suggested_action'] == 'markdown')
        transfer_count = sum(1 for line in lines if line['suggested_action'] == 'transfer')

        currency = self.env.company.currency_id
        return {
            'kpis': {
                'expiring_soon': expiring_soon,
                'at_risk': at_risk,
                'safe': safe,
                'value_at_risk': value_at_risk,
            },
            'currency_symbol': currency.symbol,
            'bucket_labels': [label for label, _ in _CHART_BUCKETS],
            'bucket_counts': [bucket_counts[label] for label, _ in _CHART_BUCKETS],
            'by_warehouse': by_warehouse,
            'total_lots': len(lines),
            'table_rows': table_rows[:20],
            'markdown_count': markdown_count,
            'transfer_count': transfer_count,
            'status_colors': _STATUS_COLORS,
        }
