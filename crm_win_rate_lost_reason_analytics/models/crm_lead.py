from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lost_note = fields.Text(
        string='Lost Note',
        help='Optional free-text context captured when the lead was marked '
             'lost (e.g. "client went with competitor after our demo"). '
             'For drill-down reading only, not used for aggregation.',
    )
    # related + store=True so pivot/graph views can group by category
    # without a runtime join; automatically recomputed whenever
    # lost_reason_id changes (including being cleared on reactivation).
    lost_reason_category = fields.Selection(
        related='lost_reason_id.category',
        string='Lost Reason Category',
        store=True,
        readonly=True,
    )

    def action_unarchive(self):
        """Reopening a lost lead clears lost_note the same way core already
        clears lost_reason_id, so the dashboard doesn't keep counting a
        since-reopened lead under its old lost reason/note.
        lost_reason_category clears itself automatically since it's a
        related field on lost_reason_id."""
        activated = self.filtered(lambda rec: not rec.active)
        res = super().action_unarchive()
        if activated:
            activated.write({'lost_note': False})
        return res

    @api.model
    def get_win_rate(self, domain=None):
        """Won/(won+lost) percentage for the given domain, or False when
        there are no won or lost leads in it ("No data" case) — never
        divides by zero or returns a misleading 0%/100%."""
        domain = (domain or []) + [('won_status', 'in', ('won', 'lost'))]
        groups = self.with_context(active_test=False)._read_group(
            domain, ['won_status'], ['__count'],
        )
        counts = {won_status: count for won_status, count in groups}
        won = counts.get('won', 0)
        lost = counts.get('lost', 0)
        total = won + lost
        if not total:
            return False
        return (won / total) * 100.0
