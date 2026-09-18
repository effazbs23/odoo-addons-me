from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    recall_report_count = fields.Integer(
        compute='_compute_recall_report_count', string='Recall Reports')

    @api.depends('name')
    def _compute_recall_report_count(self):
        Report = self.env['lot.recall.report']
        for lot in self:
            lot.recall_report_count = Report.search_count(
                [('lot_ids', 'in', lot.id)])

    def action_generate_recall_report(self):
        self.ensure_one()
        report = self.env['lot.recall.report'].create({
            'lot_ids': [(6, 0, self.ids)],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recall Report',
            'res_model': 'lot.recall.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_recall_reports(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Recall Reports',
            'res_model': 'lot.recall.report',
            'view_mode': 'list,form',
            'domain': [('lot_ids', 'in', self.ids)],
        }
