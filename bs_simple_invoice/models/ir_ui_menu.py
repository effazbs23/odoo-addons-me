from odoo import models

# ir.ui.menu.group_ids is a pure whitelist ("visible if member of any listed
# group, or no groups = visible to all") -- it has no way to hide an item
# from one specific group while leaving it visible to everyone else. Adding
# a group requirement via inherited <menuitem groups="..."/> XML would
# therefore restrict these menus for ALL users, not just simple-mode ones,
# breaking the "no behavior change for non-simple-mode users" requirement.
# A read-time filter is the only way to hide these for simple-mode users
# only, without touching the native menu records at all.
HIDDEN_MENU_XMLIDS = [
    'account.menu_finance_entries',       # Journal Entries / Reconciliation
    'account.menu_finance_reports',       # Tax / analytic reporting
    'account.menu_finance_configuration',  # Chart of Accounts, taxes, multi-currency, analytic config
]


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        menu_ids = super()._visible_menu_ids(debug=debug)
        user = self.env.user
        # Accountant-group-wins precedence (spec 9): a user in both groups
        # always sees the full menu.
        if user.has_group('bs_simple_invoice.simple_invoicing_group') \
                and not user.has_group('account.group_account_manager'):
            data = self.env['ir.model.data']
            hidden_ids = {
                data._xmlid_to_res_id(xmlid, raise_if_not_found=False)
                for xmlid in HIDDEN_MENU_XMLIDS
            }
            menu_ids = menu_ids - hidden_ids
        return menu_ids
