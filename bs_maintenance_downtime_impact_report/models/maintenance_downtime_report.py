from odoo import _, api, fields, models, tools


class MaintenanceDowntimeImpactReport(models.Model):
    _name = 'maintenance.downtime.impact.report'
    _description = 'Maintenance Downtime Impact Report (read-only view)'
    _auto = False
    _order = 'downtime_start desc'

    request_id = fields.Many2one('maintenance.request', 'Maintenance Request', readonly=True)
    equipment_id = fields.Many2one('maintenance.equipment', 'Equipment', readonly=True)
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center', readonly=True)
    production_id = fields.Many2one('mrp.production', 'Manufacturing Order', readonly=True)
    workorder_id = fields.Many2one('mrp.workorder', 'Work Order', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)
    downtime_start = fields.Datetime('Downtime Start', readonly=True)
    downtime_end = fields.Datetime('Downtime End', readonly=True)
    downtime_hours = fields.Float('Downtime (h)', readonly=True)
    planned_date_deadline = fields.Datetime('Planned Deadline', readonly=True)
    actual_date_finished = fields.Datetime('Actual Finish', readonly=True)
    production_state = fields.Char('MO Status', readonly=True)
    missed_due_date = fields.Boolean('Missed Due Date', readonly=True)
    estimated_cost = fields.Float('Estimated Cost', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW maintenance_downtime_impact_report AS (
                SELECT
                    row_number() OVER (ORDER BY mr.id, mp.id) AS id,
                    mr.id AS request_id,
                    mr.equipment_id AS equipment_id,
                    me.workcenter_id AS workcenter_id,
                    mp.id AS production_id,
                    mw.id AS workorder_id,
                    mr.company_id AS company_id,
                    mr.schedule_date AS downtime_start,
                    mr.schedule_end AS downtime_end,
                    mr.duration AS downtime_hours,
                    mp.date_deadline AS planned_date_deadline,
                    mp.date_finished AS actual_date_finished,
                    mp.state AS production_state,
                    CASE WHEN mp.date_deadline IS NOT NULL AND mp.date_finished IS NOT NULL
                              AND mp.date_finished > mp.date_deadline
                         THEN true ELSE false END AS missed_due_date,
                    wc.costs_hour * mr.duration AS estimated_cost
                FROM maintenance_request mr
                JOIN maintenance_equipment me ON me.id = mr.equipment_id
                JOIN mrp_workcenter wc ON wc.id = me.workcenter_id
                JOIN mrp_workorder mw ON mw.workcenter_id = wc.id
                JOIN mrp_production mp ON mp.id = mw.production_id
                WHERE mr.schedule_date IS NOT NULL
                  AND mr.schedule_end IS NOT NULL
                  AND me.workcenter_id IS NOT NULL
                  AND COALESCE(mw.date_start, mp.date_start) <= mr.schedule_end
                  AND COALESCE(mw.date_finished, mp.date_finished, mp.date_deadline, mr.schedule_end) >= mr.schedule_date
            )
        """)

    @api.model
    def search(self, domain, offset=0, limit=None, order=None):
        # _auto=False view models aren't covered by the ORM's usual
        # flush-before-read heuristics - see the equivalent note on
        # bs_subcontracting_stock_dashboard's report model.
        self.env.flush_all()
        return super().search(domain, offset=offset, limit=limit, order=order)

    @api.model
    def get_summary(self, domain=None):
        records = self.search(domain or [])
        productions = records.mapped('production_id')
        missed = records.filtered('missed_due_date').mapped('production_id')
        return {
            'total_downtime_hours': round(sum(records.mapped('downtime_hours')), 1),
            'affected_mo_count': len(productions),
            'missed_due_date_count': len(missed),
            'estimated_cost': round(sum(records.mapped('estimated_cost')), 2),
        }

    @api.model
    def get_downtime_trend(self, domain=None):
        records = self.search(domain or [])
        by_date = {}
        for rec in records:
            if not rec.downtime_start:
                continue
            key = rec.downtime_start.date()
            row = by_date.setdefault(key, {'hours': 0.0, 'missed': set()})
            row['hours'] += rec.downtime_hours
            if rec.missed_due_date:
                row['missed'].add(rec.production_id.id)
        dates = sorted(by_date.keys())
        return {
            'categories': [d.isoformat() for d in dates],
            'hours': [round(by_date[d]['hours'], 1) for d in dates],
            'missed_counts': [len(by_date[d]['missed']) for d in dates],
        }

    @api.model
    def get_impact_by_workcenter(self, domain=None):
        records = self.search(domain or [])
        totals = {}
        for rec in records:
            key = rec.workcenter_id
            totals.setdefault(key, 0.0)
            totals[key] += rec.estimated_cost
        return [{'workcenter': k.display_name, 'cost': round(v, 2)} for k, v in totals.items()]

    @api.model
    def get_top_equipment(self, domain=None, limit=5):
        records = self.search(domain or [])
        totals = {}
        for rec in records:
            key = rec.equipment_id
            totals.setdefault(key, 0.0)
            totals[key] += rec.downtime_hours
        rows = [{'equipment': k.display_name, 'hours': round(v, 1)} for k, v in totals.items()]
        return sorted(rows, key=lambda r: r['hours'], reverse=True)[:limit]

    @api.model
    def get_details(self, domain=None):
        records = self.search(domain or [])
        by_request = {}
        for rec in records:
            row = by_request.setdefault(rec.request_id.id, {
                'date': rec.downtime_start, 'equipment': rec.equipment_id.display_name,
                'workcenter': rec.workcenter_id.display_name, 'request': rec.request_id.display_name,
                'downtime_hours': rec.downtime_hours,
                'productions': [], 'missed': False, 'cost': 0.0,
                'window_start': rec.downtime_start, 'window_end': rec.downtime_end,
            })
            row['productions'].append(rec.production_id.display_name)
            row['missed'] = row['missed'] or rec.missed_due_date
            row['cost'] += rec.estimated_cost
        rows = list(by_request.values())
        for row in rows:
            row['productions'] = ', '.join(sorted(set(row['productions'])))
            row['cost'] = round(row['cost'], 2)
            row['status'] = _('Missed') if row['missed'] else _('On Track')
        return sorted(rows, key=lambda r: r['date'] or '', reverse=True)

    @api.model
    def get_recent_maintenance_events(self, limit=5):
        requests = self.env['maintenance.request'].search(
            [('schedule_date', '!=', False)], order='schedule_date desc', limit=limit)
        return [{
            'reference': f"{req.equipment_id.workcenter_id.display_name or ''} - {req.equipment_id.display_name}",
            'name': req.name,
            'date': req.schedule_date,
        } for req in requests]
