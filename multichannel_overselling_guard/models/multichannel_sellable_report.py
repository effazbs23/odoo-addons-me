from odoo import fields, models, tools


class MultichannelSellableReport(models.Model):
    """Read-only 'Sellable Now' reporting model, one row per (product,
    warehouse) that has on-hand stock, a reservation or a configured buffer.
    Built the same way core reporting models such as `sale.report` are: a
    plain Python model with `_auto = False` backed by a SQL view created in
    `init()`, so it needs no data migration and stays cheap to query.

    Deliberately excludes rows with nothing to show (no stock, no
    reservation, no buffer) to avoid a full product x warehouse cross join
    on installations with a large catalog.
    """
    _name = 'multichannel.sellable.report'
    _description = 'Multichannel Sellable Now Report'
    _auto = False
    _order = 'product_id, warehouse_id'

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', readonly=True)
    on_hand = fields.Float(string='On Hand', readonly=True)
    reserved = fields.Float(string='Reserved', readonly=True)
    buffer_qty = fields.Float(string='Reserved Buffer', readonly=True)
    sellable_now = fields.Float(string='Sellable Now', readonly=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ], string='Status', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        # Status thresholds (documented here since they're not configurable):
        # sellable_now <= 0 -> out_of_stock, 0 < sellable_now <= 10 -> low_stock,
        # otherwise available.
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %(table)s AS (
                WITH wh_root AS (
                    SELECT wh.id AS warehouse_id, sl.parent_path AS root_path
                    FROM stock_warehouse wh
                    JOIN stock_location sl ON sl.id = wh.view_location_id
                ),
                on_hand_by_wh AS (
                    SELECT wr.warehouse_id, sq.product_id, SUM(sq.quantity) AS on_hand
                    FROM stock_quant sq
                    JOIN stock_location loc ON loc.id = sq.location_id
                    JOIN wh_root wr ON loc.parent_path LIKE wr.root_path || '%%'
                    WHERE loc.usage = 'internal'
                    GROUP BY wr.warehouse_id, sq.product_id
                ),
                reserved_by_wh AS (
                    SELECT ssr.warehouse_id, ssr.product_id, SUM(ssr.quantity) AS reserved
                    FROM stock_soft_reservation ssr
                    WHERE ssr.state IN ('active', 'confirmed')
                    GROUP BY ssr.warehouse_id, ssr.product_id
                )
                SELECT
                    ROW_NUMBER() OVER (ORDER BY pp.id, wh.id) AS id,
                    pp.id AS product_id,
                    wh.id AS warehouse_id,
                    COALESCE(oh.on_hand, 0.0) AS on_hand,
                    COALESCE(rw.reserved, 0.0) AS reserved,
                    COALESCE(buf.buffer_qty, cat.default_reserved_buffer_qty, 0.0) AS buffer_qty,
                    (COALESCE(oh.on_hand, 0.0)
                        - COALESCE(buf.buffer_qty, cat.default_reserved_buffer_qty, 0.0)
                        - COALESCE(rw.reserved, 0.0)) AS sellable_now,
                    CASE
                        WHEN (COALESCE(oh.on_hand, 0.0)
                            - COALESCE(buf.buffer_qty, cat.default_reserved_buffer_qty, 0.0)
                            - COALESCE(rw.reserved, 0.0)) <= 0 THEN 'out_of_stock'
                        WHEN (COALESCE(oh.on_hand, 0.0)
                            - COALESCE(buf.buffer_qty, cat.default_reserved_buffer_qty, 0.0)
                            - COALESCE(rw.reserved, 0.0)) <= 10 THEN 'low_stock'
                        ELSE 'available'
                    END AS status
                FROM product_product pp
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN product_category cat ON cat.id = pt.categ_id
                CROSS JOIN stock_warehouse wh
                LEFT JOIN on_hand_by_wh oh ON oh.product_id = pp.id AND oh.warehouse_id = wh.id
                LEFT JOIN reserved_by_wh rw ON rw.product_id = pp.id AND rw.warehouse_id = wh.id
                LEFT JOIN multichannel_stock_buffer buf
                    ON buf.product_id = pp.id AND buf.warehouse_id = wh.id
                WHERE pt.active = true
                  AND (oh.on_hand IS NOT NULL OR rw.reserved IS NOT NULL OR buf.buffer_qty IS NOT NULL)
            )
        """ % {'table': self._table})
