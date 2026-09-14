from odoo import _, api, fields, models, tools

DEFAULT_BUCKET_1_MAX = 7
DEFAULT_BUCKET_2_MAX = 14
DEFAULT_BUCKET_3_MAX = 30
DEFAULT_ALERT_DAYS = 30


class SubcontractingStockReport(models.Model):
    _name = 'subcontracting.stock.report'
    _description = 'Subcontractor-Owned Stock Report (read-only view over stock.quant)'
    _auto = False
    _order = 'id desc'

    quant_id = fields.Many2one('stock.quant', 'Quant', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', readonly=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    lot_id = fields.Many2one('stock.lot', 'Lot/Serial', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    owner_id = fields.Many2one('res.partner', 'Owner', readonly=True)
    quantity = fields.Float('Quantity', readonly=True)
    ownership = fields.Selection([('company', 'Company-Owned'), ('subcontractor', 'Subcontractor-Owned')], readonly=True)
    last_in_date = fields.Datetime('Last Received', readonly=True)

    # Non-stored: resolving the vendor and the product cost are both
    # company-dependent (JSONB) fields on res.partner/product.product, so
    # they're read through the ORM instead of hand-rolled JSONB SQL. Age
    # is deliberately live (not stored) so it keeps advancing with the
    # calendar even when nobody touches the record - see the equivalent
    # note on bs_purchase_reorder_optimizer's stale-orderpoint fields.
    partner_id = fields.Many2one('res.partner', 'Subcontractor', compute='_compute_partner_id')
    value = fields.Float('Value', compute='_compute_value')
    age_days = fields.Integer('Days at Subcontractor', compute='_compute_age')
    aging_bucket = fields.Selection(
        [('b1', '0-7'), ('b2', '8-14'), ('b3', '15-30'), ('b4', '30+')],
        string='Aging Bucket', compute='_compute_age')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT
                    sq.id AS id,
                    sq.id AS quant_id,
                    sq.location_id AS location_id,
                    sq.product_id AS product_id,
                    sq.lot_id AS lot_id,
                    sq.company_id AS company_id,
                    sq.owner_id AS owner_id,
                    sq.quantity AS quantity,
                    CASE WHEN sq.owner_id IS NULL OR sq.owner_id = rc.partner_id
                         THEN 'company' ELSE 'subcontractor' END AS ownership,
                    mv.last_in_date AS last_in_date
                FROM stock_quant sq
                JOIN res_company rc ON rc.id = sq.company_id
                JOIN stock_location subloc ON subloc.id = rc.subcontracting_location_id
                JOIN stock_location loc ON loc.id = sq.location_id
                LEFT JOIN LATERAL (
                    SELECT MAX(sml.date) AS last_in_date
                    FROM stock_move_line sml
                    WHERE sml.product_id = sq.product_id
                      AND sml.location_dest_id = sq.location_id
                      AND sml.location_id != sq.location_id
                      AND sml.state = 'done'
                      AND (sq.lot_id IS NULL OR sml.lot_id = sq.lot_id)
                ) mv ON true
                WHERE rc.subcontracting_location_id IS NOT NULL
                  AND loc.parent_path LIKE subloc.parent_path || '%%'
                  AND sq.quantity != 0
            )
        """)

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        # _auto=False view models aren't covered by the ORM's usual
        # flush-before-read heuristics (there's no field dependency graph
        # for a raw SQL view), so a quant/location just written in the same
        # transaction can silently be invisible here until something else
        # happens to flush. Always flush first - this view is read
        # constantly and cheaply, unlike a heavy stored-field recompute.
        self.env.flush_all()
        return super().search(domain, offset=offset, limit=limit, order=order)

    @api.depends('location_id')
    def _compute_partner_id(self):
        locations = self.location_id
        partners = self.env['res.partner'].search([('property_stock_subcontractor', 'in', locations.ids)])
        by_location = {p.property_stock_subcontractor.id: p for p in partners}
        for rec in self:
            rec.partner_id = by_location.get(rec.location_id.id, False)

    @api.depends('product_id', 'quantity')
    def _compute_value(self):
        for rec in self:
            rec.value = round(rec.quantity * (rec.product_id.standard_price or 0.0), 2)

    @api.depends('last_in_date')
    def _compute_age(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        b1 = int(get_param('bs_subcontracting_stock_dashboard.bucket_1_max', DEFAULT_BUCKET_1_MAX))
        b2 = int(get_param('bs_subcontracting_stock_dashboard.bucket_2_max', DEFAULT_BUCKET_2_MAX))
        b3 = int(get_param('bs_subcontracting_stock_dashboard.bucket_3_max', DEFAULT_BUCKET_3_MAX))
        today = fields.Date.context_today(self)
        for rec in self:
            if rec.last_in_date:
                in_date = rec.last_in_date.date() if hasattr(rec.last_in_date, 'date') else rec.last_in_date
                age = (today - in_date).days
            else:
                age = 0
            rec.age_days = age
            if age <= b1:
                rec.aging_bucket = 'b1'
            elif age <= b2:
                rec.aging_bucket = 'b2'
            elif age <= b3:
                rec.aging_bucket = 'b3'
            else:
                rec.aging_bucket = 'b4'

    @api.model
    def get_dashboard_summary(self, domain=None):
        records = self.search(domain or [])
        company = records.filtered(lambda r: r.ownership == 'company')
        subcontractor = records - company
        return {
            'total_quantity': sum(records.mapped('quantity')),
            'company_quantity': sum(company.mapped('quantity')),
            'subcontractor_quantity': sum(subcontractor.mapped('quantity')),
            'location_count': len(records.mapped('location_id')),
        }

    @api.model
    def get_ownership_split(self, domain=None):
        records = self.search(domain or [])
        company = sum(records.filtered(lambda r: r.ownership == 'company').mapped('quantity'))
        subcontractor = sum(records.filtered(lambda r: r.ownership == 'subcontractor').mapped('quantity'))
        return {'company': company, 'subcontractor': subcontractor}

    @api.model
    def get_stock_by_subcontractor(self, domain=None):
        records = self.search(domain or [])
        totals = {}
        for rec in records:
            key = rec.partner_id
            totals.setdefault(key, 0.0)
            totals[key] += rec.quantity
        return [{'partner': k.display_name if k else _('Unassigned'), 'quantity': v} for k, v in totals.items()]

    @api.model
    def get_breakdown_by_subcontractor(self, domain=None):
        records = self.search(domain or [])
        rows = {}
        for rec in records:
            key = (rec.partner_id.id, rec.location_id.id)
            row = rows.setdefault(key, {
                'partner': rec.partner_id.display_name if rec.partner_id else _('Unassigned'),
                'location': rec.location_id.display_name,
                'company_qty': 0.0, 'company_value': 0.0,
                'subcontractor_qty': 0.0, 'subcontractor_value': 0.0,
            })
            if rec.ownership == 'company':
                row['company_qty'] += rec.quantity
                row['company_value'] += rec.value
            else:
                row['subcontractor_qty'] += rec.quantity
                row['subcontractor_value'] += rec.value
        for row in rows.values():
            row['company_value'] = round(row['company_value'], 2)
            row['subcontractor_value'] = round(row['subcontractor_value'], 2)
        return list(rows.values())

    @api.model
    def get_aging_rows(self, domain=None):
        records = self.search((domain or []) + [('ownership', '=', 'company')])
        rows = [{
            'product': rec.product_id.display_name,
            'partner': rec.partner_id.display_name if rec.partner_id else _('Unassigned'),
            'location': rec.location_id.display_name,
            'age_days': rec.age_days,
            'quantity': rec.quantity,
            'value': rec.value,
            'aging_bucket': rec.aging_bucket,
        } for rec in records]
        return sorted(rows, key=lambda r: r['age_days'], reverse=True)

    @api.model
    def get_value_report(self, domain=None):
        records = self.search((domain or []) + [('ownership', '=', 'company')])
        rows = {}
        for rec in records:
            key = (rec.location_id.id, rec.partner_id.id)
            row = rows.setdefault(key, {
                'location': rec.location_id.display_name,
                'partner': rec.partner_id.display_name if rec.partner_id else _('Unassigned'),
                'value': 0.0,
            })
            row['value'] += rec.value
        for row in rows.values():
            row['value'] = round(row['value'], 2)
        rows = list(rows.values())
        return {'rows': rows, 'total_at_risk': round(sum(r['value'] for r in rows), 2)}

    @api.model
    def cron_check_overdue_alerts(self):
        get_param = self.env['ir.config_parameter'].sudo().get_param
        if get_param('bs_subcontracting_stock_dashboard.enable_alerts', 'True') != 'True':
            return
        alert_days = int(get_param('bs_subcontracting_stock_dashboard.alert_days', DEFAULT_ALERT_DAYS))
        notification_type = get_param('bs_subcontracting_stock_dashboard.notification_type', 'activity')

        records = self.search([('ownership', '=', 'company')])
        overdue_by_partner = {}
        for rec in records:
            if rec.age_days >= alert_days and rec.partner_id:
                overdue_by_partner.setdefault(rec.partner_id, []).append(rec)

        activity_type = self.env.ref('mail.mail_activity_data_todo')
        for partner, recs in overdue_by_partner.items():
            summary = _("%(count)d component(s) at %(partner)s beyond %(days)d days without the expected receipt") % {
                'count': len(recs), 'partner': partner.display_name, 'days': alert_days,
            }
            if notification_type == 'email':
                partner.message_post(body=summary, subtype_xmlid='mail.mt_note')
            else:
                for user in self.env.ref('stock.group_stock_manager').user_ids:
                    self.env['mail.activity'].create({
                        'res_model_id': self.env['ir.model']._get_id('res.partner'),
                        'res_id': partner.id,
                        'activity_type_id': activity_type.id,
                        'summary': summary,
                        'user_id': user.id,
                    })
