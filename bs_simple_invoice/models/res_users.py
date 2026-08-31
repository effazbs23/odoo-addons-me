from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        users._sync_simple_invoicing_group()
        return users

    def write(self, vals):
        res = super().write(vals)
        if 'company_id' in vals or 'share' in vals:
            self._sync_simple_invoicing_group()
        return res

    def _sync_simple_invoicing_group(self):
        """Keep 'Simple Invoicing User' membership in lockstep with each
        user's own company setting and share status -- the single place
        this module decides who is eligible, so res.company.write() (bulk,
        on toggle) and this method (per-user, on create/company change)
        never disagree. Portal/public users (share=True) are never
        eligible: this group implies account.group_account_invoice, which
        grants real CRUD on invoices/payments/journals, not just a UI
        preference -- a share user must never gain that."""
        group = self.env.ref('bs_simple_invoice.simple_invoicing_group')
        to_add = self.filtered(lambda u: not u.share and u.company_id.simple_invoicing_mode)
        to_remove = self - to_add
        if to_add:
            group.sudo().write({'user_ids': [(4, user.id) for user in to_add]})
        if to_remove:
            group.sudo().write({'user_ids': [(3, user.id) for user in to_remove]})
