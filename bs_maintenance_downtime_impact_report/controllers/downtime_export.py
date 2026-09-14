import io
import json

from odoo import http
from odoo.http import request

HEADERS = ['Date', 'Equipment', 'Work Center', 'Manufacturing Orders', 'Downtime (h)', 'Cost', 'Status']
KEYS = ['date', 'equipment', 'workcenter', 'productions', 'downtime_hours', 'cost', 'status']


class DowntimeExportController(http.Controller):

    @http.route('/bs_maintenance_downtime_impact_report/export.xlsx', type='http', auth='user')
    def export_xlsx(self, domain='[]', **kwargs):
        import xlsxwriter

        report = request.env['maintenance.downtime.impact.report']
        rows = report.get_details(json.loads(domain))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#EEEEEE'})
        sheet = workbook.add_worksheet('Downtime Impact')
        for col, header in enumerate(HEADERS):
            sheet.write(0, col, header, header_fmt)
        for row_idx, row in enumerate(rows, start=1):
            sheet.write_row(row_idx, 0, [str(row[key]) for key in KEYS])
        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="downtime_impact_report.xlsx"'),
            ],
        )
