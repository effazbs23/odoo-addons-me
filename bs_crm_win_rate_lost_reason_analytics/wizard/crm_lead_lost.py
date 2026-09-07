from odoo import fields, models, _
from odoo.exceptions import UserError


class CrmLeadLost(models.TransientModel):
    _inherit = 'crm.lead.lost'

    lost_note = fields.Text(
        string='Lost Note',
        help='Optional free-text context, stored on the lead for '
             'dashboard drill-down (separate from the Closing Note above, '
             'which is only posted to the chatter).',
    )

    def action_lost_reason_apply(self):
        """A lost reason is now mandatory before a lead can be marked
        lost — this is the only UI path to lose a lead (both the kanban
        "Lost" button and the form "Mark Lost" button open this wizard),
        so enforcing it here closes the gap without touching
        action_set_lost() itself, which is also called with no reason by
        the /lead/case_mark_lost email-link controller route."""
        self.ensure_one()
        if not self.lost_reason_id:
            raise UserError(_('Please select a lost reason before marking this lead as lost.'))
        res = super().action_lost_reason_apply()
        if self.lost_note:
            self.lead_ids.write({'lost_note': self.lost_note})
        return res
