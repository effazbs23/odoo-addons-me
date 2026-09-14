from odoo import api, fields, models


class AmcScheduleReportWizard(models.TransientModel):
    _name = 'amc.schedule.report.wizard'
    _description = 'AMC Schedule Report'

    def _default_year(self):
        return str(fields.Date.context_today(self).year)

    @api.model
    def _year_selection(self):
        current = fields.Date.context_today(self).year
        return [(str(year), str(year)) for year in range(current - 5, current + 6)]

    product_categ_id = fields.Many2one('product.category', string='Product Category',
                                       help='Leave blank to include every category. The category '
                                            'name is used in the report title.')
    site_ids = fields.Many2many('amc.site', string='Sites',
                                help='Leave blank to include every site.')
    year = fields.Selection(selection='_year_selection', string='Year', required=True,
                            default=_default_year)

    def action_generate_report(self):
        self.ensure_one()
        data = {
            'year': int(self.year),
            'product_categ_id': self.product_categ_id.id or False,
            'product_categ_name': self.product_categ_id.name or '',
            'site_ids': self.site_ids.ids,
        }
        # config=False: with no external report layout set on the company, report_action
        # otherwise swaps the report for the "configure your document layout" wizard.
        # That layout governs PDF headers and has no bearing on a spreadsheet.
        return self.env.ref('amc_management.report_amc_schedule').report_action(
            [], data=data, config=False)
