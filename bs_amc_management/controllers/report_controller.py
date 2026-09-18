import json

import werkzeug.exceptions
from werkzeug.urls import url_parse

from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.safe_eval import safe_eval, time
from odoo.addons.web.controllers import report

XLSX_MIMETYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


class ReportController(report.ReportController):
    """Serve ``report_type = 'xlsx'`` reports.

    Mirrors the routing the standard PDF and text reports go through, so an XLSX
    report action behaves like any other: the web client posts to ``/report/download``,
    which delegates to ``/report/xlsx/<report_name>[/<ids>]`` here.
    """

    @http.route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter != 'xlsx':
            return super().report_routes(reportname, docids=docids, converter=converter, **data)

        context = dict(request.env.context)
        if docids:
            docids = [int(one) for one in docids.split(',') if one.isdigit()]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            context.update(data['context'])

        rendered = request.env['ir.actions.report'].with_context(context)._render_xlsx(
            reportname, docids, data=data)
        if not rendered:
            raise werkzeug.exceptions.NotFound()
        content = rendered[0]
        return request.make_response(content, headers=[
            ('Content-Type', XLSX_MIMETYPE),
            ('Content-Length', len(content)),
        ])

    @http.route()
    def report_download(self, data, context=None, **kwargs):
        requestcontent = json.loads(data)
        url, type_ = requestcontent[0], requestcontent[1]
        if type_ != 'xlsx':
            return super().report_download(data, context=context, **kwargs)

        reportname = url.split('/report/xlsx/')[1].split('?')[0]
        docids = None
        if '/' in reportname:
            reportname, docids = reportname.split('/', 1)

        if docids:
            response = self.report_routes(
                reportname, docids=docids, converter='xlsx', context=context)
        else:
            # Report driven by a wizard: its options ride in the query string, and the
            # context found there has to be merged onto the user context the client
            # posted, exactly as the standard PDF path does.
            query = url_parse(url).decode_query(cls=dict)
            if 'context' in query:
                merged = {**json.loads(context or '{}'), **json.loads(query.pop('context'))}
                context = json.dumps(merged)
            response = self.report_routes(
                reportname, converter='xlsx', context=context, **query)

        report_action = request.env['ir.actions.report']._get_report_from_name(reportname)
        response.headers.add(
            'Content-Disposition',
            content_disposition(self._amc_xlsx_filename(report_action, docids)))
        return response

    def _amc_xlsx_filename(self, report_action, docids):
        """Downloaded file name, honouring print_report_name for single-record reports."""
        filename = '%s.xlsx' % report_action.name
        if not report_action.print_report_name or not docids:
            return filename
        ids = [int(one) for one in docids.split(',') if one.isdigit()]
        records = request.env[report_action.model].browse(ids)
        if len(records) > 1:
            return filename
        try:
            return '%s.xlsx' % safe_eval(
                report_action.print_report_name, {'object': records, 'time': time})
        except (ValueError, SyntaxError, TypeError, KeyError, AttributeError):
            # A print_report_name that does not evaluate is not worth failing a
            # download over; the report's own name is a fine fallback.
            return filename
