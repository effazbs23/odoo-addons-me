from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PettyCashRequestLine(models.Model):
    _name = "petty.cash.request.line"
    _description = "Petty Cash Request Line"

    request_id = fields.Many2one(
        "petty.cash.request", "Request", required=True, ondelete="cascade"
    )
    purpose = fields.Char("Purpose", required=True)
    amount = fields.Monetary("Amount", required=True, currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", related="request_id.currency_id", store=True
    )
    company_id = fields.Many2one(
        "res.company", related="request_id.company_id", store=True
    )
    attachment = fields.Binary(attachment=True)
    attachment_filename = fields.Char("Filename")

    @api.onchange("amount")
    def _onchange_amount(self):
        """Trigger recomputation of total in parent"""
        if self.request_id:
            self.request_id._compute_amount()

    def unlink(self):
        # Group lines being deleted by their parent request
        for request in self.mapped("request_id"):
            if request.state != "submitted":
                continue
            lines_to_delete = self.filtered(lambda l: l.request_id == request)
            remaining = request.line_ids - lines_to_delete
            if not remaining:
                raise UserError(
                    _(
                        "The petty cash request '%(name)s' "
                        "must have at least one purpose line."
                    )
                    % {"name": request.name}
                )
        return super().unlink()
