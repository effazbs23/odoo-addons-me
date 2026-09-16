from odoo import fields, models, _
from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    """Minimal XLSX report support, so the module carries no third-party dependency.

    A report declared with ``report_type`` xlsx is rendered by the model named
    ``report.<report_name>``, which must inherit ``amc.report.xlsx`` and implement
    ``generate_xlsx_report``. The matching HTTP route lives in
    ``controllers/report_controller.py`` and the client-side action handler in
    ``static/src/js/xlsx_report_action.js``.
    """
    _inherit = 'ir.actions.report'

    report_type = fields.Selection(
        selection_add=[('xlsx', 'XLSX')],
        ondelete={'xlsx': 'cascade'},
    )

    def _render_xlsx(self, report_ref, docids, data=None):
        report = self._get_report(report_ref)
        report_model = self.env.get('report.%s' % report.report_name)
        if report_model is None:
            raise UserError(_(
                "The XLSX report '%s' has no rendering model. Expected a model named 'report.%s'.",
                report.report_name, report.report_name))
        return report_model.with_context(active_model=report.model)._render_xlsx(docids, data=data)
