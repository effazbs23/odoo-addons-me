from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    simple_invoicing_mode = fields.Boolean(
        string="Enable Simple Invoice",
        help="Default the simplified invoicing menu, form and status funnel "
             "for this company's users. Individual users can still be added "
             "to or removed from the 'Simple Invoicing User' group by hand "
             "afterwards to mix simple-mode staff with full-access "
             "accountants on the same database.",
    )

    def write(self, vals):
        res = super().write(vals)
        if 'simple_invoicing_mode' in vals:
            group = self.env.ref('bs_simple_invoice.simple_invoicing_group')
            for company in self:
                users = self.env['res.users'].sudo().search([('company_id', '=', company.id)])
                if company.simple_invoicing_mode:
                    group.sudo().write({'users': [(4, user.id) for user in users]})
                else:
                    group.sudo().write({'users': [(3, user.id) for user in users]})
        return res
