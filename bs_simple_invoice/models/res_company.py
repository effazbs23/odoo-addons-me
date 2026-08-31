from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    simple_invoicing_mode = fields.Boolean(
        string="Enable Simple Invoice",
        default=True,
        help="Default the simplified invoicing menu, form and status funnel "
             "for this company's users. Individual users can still be added "
             "to or removed from the 'Simple Invoicing User' group by hand "
             "afterwards to mix simple-mode staff with full-access "
             "accountants on the same database.",
    )

    def write(self, vals):
        res = super().write(vals)
        if 'simple_invoicing_mode' in vals:
            for company in self:
                users = self.env['res.users'].sudo().search([('company_id', '=', company.id)])
                # _sync_simple_invoicing_group is the single source of truth
                # for eligibility (it excludes share/portal users) -- this
                # loop must never write group membership directly, or a
                # future caller could re-introduce the share-user leak.
                users._sync_simple_invoicing_group()
        return res
