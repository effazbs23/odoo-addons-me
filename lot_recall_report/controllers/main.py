from odoo import http
from odoo.http import request


class LotRecallReportController(http.Controller):

    @http.route('/lot_recall_report/xlsx/<int:report_id>', type='http', auth='user')
    def download_xlsx(self, report_id, **kwargs):
        report = request.env['lot.recall.report'].browse(report_id)
        report.check_access('read')
        data = request.env['lot.recall.report.xlsx'].build(report)
        filename = 'Recall_Report_%s.xlsx' % (report.name or report_id)
        headers = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', 'attachment; filename="%s"' % filename),
            ('Content-Length', len(data)),
        ]
        return request.make_response(data, headers=headers)
