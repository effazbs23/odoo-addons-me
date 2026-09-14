import io
import json

from odoo import http
from odoo.http import request

SHEETS = {
    'per_subcontractor': (
        'get_breakdown_by_subcontractor',
        ['Subcontractor', 'Location', 'Company Qty', 'Company Value', 'Subcontractor Qty', 'Subcontractor Value'],
        ['partner', 'location', 'company_qty', 'company_value', 'subcontractor_qty', 'subcontractor_value'],
    ),
    'aging_report': (
        'get_aging_rows',
        ['Component', 'Subcontractor', 'Location', 'Days at Subcontractor', 'Quantity', 'Value', 'Aging Bucket'],
        ['product', 'partner', 'location', 'age_days', 'quantity', 'value', 'aging_bucket'],
    ),
}


class SubcontractingExportController(http.Controller):

    @http.route('/bs_subcontracting_stock_dashboard/export.xlsx', type='http', auth='user')
    def export_xlsx(self, mode='per_subcontractor', domain='[]', **kwargs):
        import xlsxwriter

        report = request.env['subcontracting.stock.report']
        domain = json.loads(domain)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#EEEEEE'})

        if mode == 'value_report':
            sheet = workbook.add_worksheet('Value Report')
            result = report.get_value_report(domain)
            headers = ['Location', 'Subcontractor', 'Value']
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_fmt)
            for row_idx, row in enumerate(result['rows'], start=1):
                sheet.write_row(row_idx, 0, [row['location'], row['partner'], row['value']])
            sheet.write(len(result['rows']) + 1, 0, 'Total at Risk', header_fmt)
            sheet.write(len(result['rows']) + 1, 2, result['total_at_risk'])
        else:
            method_name, headers, keys = SHEETS.get(mode, SHEETS['per_subcontractor'])
            sheet = workbook.add_worksheet('Report')
            rows = getattr(report, method_name)(domain)
            for col, header in enumerate(headers):
                sheet.write(0, col, header, header_fmt)
            for row_idx, row in enumerate(rows, start=1):
                sheet.write_row(row_idx, 0, [row[key] for key in keys])

        workbook.close()
        output.seek(0)

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', 'attachment; filename="subcontracting_stock_report.xlsx"'),
            ],
        )
