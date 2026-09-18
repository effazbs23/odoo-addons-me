import io
import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AmcReportXlsx(models.AbstractModel):
    """Base for the module's XLSX reports.

    Subclasses implement ``generate_xlsx_report(workbook, data, records)``; everything
    around it -- the in-memory workbook, closing it and handing the bytes back to the
    controller -- is handled here. Deliberately self-contained so installing this
    module never requires a third-party reporting addon: xlsxwriter already ships with
    Odoo.
    """
    _name = 'amc.report.xlsx'
    _description = 'AMC XLSX Report'

    def _get_objs_for_report(self, docids, data):
        """Records the report runs on.

        A report launched from a wizard passes no ids and carries its filters in
        ``data`` instead, so an empty recordset is the normal case there.
        """
        if docids:
            if isinstance(docids, str):
                docids = [int(one) for one in docids.split(',') if one.strip().isdigit()]
            return self.env[self.env.context['active_model']].browse(docids)
        active_model = self.env.context.get('active_model')
        return self.env[active_model].browse() if active_model else self.env['amc.contract'].browse()

    def _render_xlsx(self, docids, data=None):
        import xlsxwriter

        objs = self._get_objs_for_report(docids, data)
        output = io.BytesIO()
        # in_memory keeps the whole workbook off disk, which matters on multi-worker
        # deployments where the temp directory is not shared.
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        self.generate_xlsx_report(workbook, data or {}, objs)
        workbook.close()
        output.seek(0)
        return output.read(), 'xlsx'

    def generate_xlsx_report(self, workbook, data, records):
        raise NotImplementedError(
            'generate_xlsx_report must be implemented by %s' % self._name)
