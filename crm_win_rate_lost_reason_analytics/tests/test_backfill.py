from odoo.tests.common import TransactionCase, tagged

from ..hooks import post_init_hook


@tagged('post_install', '-at_install')
class TestBackfill(TransactionCase):
    """post_init_hook is the defensive backfill for data that pre-dates
    this module's install. crm.lost.reason.category can't actually end up
    blank after install (required=True gives it a NOT NULL DB constraint
    on top of its field-level default - verified empirically, a raw SQL
    NULL write to it is rejected by Postgres itself), so the only
    meaningful backfill left is crm.lead.lost_reason_category, which has
    no such constraint.

    To simulate a genuinely pre-existing row (one this module's Python
    code never touched, so nothing in the ORM cache is "dirty" and could
    self-heal it via autoflush before the hook runs), we write it
    entirely with raw SQL rather than through action_set_lost() - and
    only ever read it back with raw SQL too, via a plain UPDATE on a
    freshly-created lead. This is exactly the state a lead lost before
    this module existed would be in: lost_reason_id set, but the
    lost_reason_category column this module adds never computed.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reason = cls.env['crm.lost.reason'].create({'name': 'Legacy reason (test)', 'category': 'pricing'})

        cls.lead_stale = cls.env['crm.lead'].create({'name': 'Lost before install (test)'})
        cls.env.cr.execute(
            """UPDATE crm_lead
               SET active = false, probability = 0, automated_probability = 0,
                   won_status = 'lost', lost_reason_id = %s, lost_reason_category = NULL
               WHERE id = %s""",
            (cls.reason.id, cls.lead_stale.id),
        )

        cls.lead_no_reason = cls.env['crm.lead'].create({'name': 'Lost with no reason (test)'})
        cls.env.cr.execute(
            """UPDATE crm_lead
               SET active = false, probability = 0, automated_probability = 0, won_status = 'lost'
               WHERE id = %s""",
            (cls.lead_no_reason.id,),
        )

    def _raw_category(self, lead_id):
        self.env.cr.execute("SELECT lost_reason_category FROM crm_lead WHERE id = %s", (lead_id,))
        return self.env.cr.fetchone()[0]

    def test_hook_recomputes_stale_lead_category(self):
        self.assertIsNone(self._raw_category(self.lead_stale.id))
        post_init_hook(self.env)
        # the real install lifecycle flushes automatically after hooks run;
        # do it explicitly here so the raw SQL check below sees the write.
        self.env.flush_all()
        self.assertEqual(self._raw_category(self.lead_stale.id), 'pricing')

    def test_hook_does_not_invent_a_category_for_no_reason_leads(self):
        post_init_hook(self.env)
        self.assertIsNone(self._raw_category(self.lead_no_reason.id))

    def test_no_reason_lead_still_counts_as_lost_in_win_rate(self):
        post_init_hook(self.env)
        domain = [('id', '=', self.lead_no_reason.id)]
        # a lone lost lead with no reason must show up as a real 0% win
        # rate (silently excluded would instead return False/"No data")
        self.assertEqual(self.env['crm.lead'].get_win_rate(domain), 0.0)
