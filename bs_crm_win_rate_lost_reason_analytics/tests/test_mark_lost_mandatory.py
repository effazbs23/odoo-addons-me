from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMarkLostMandatory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reason = cls.env['crm.lost.reason'].create({
            'name': 'Competitor won (test)',
            'category': 'competitor',
        })
        cls.lead = cls.env['crm.lead'].create({'name': 'Test Lead'})

    def test_blocks_without_reason(self):
        wizard = self.env['crm.lead.lost'].create({'lead_ids': [(6, 0, self.lead.ids)]})
        with self.assertRaises(UserError):
            wizard.action_lost_reason_apply()
        self.assertTrue(self.lead.active)

    def test_allows_with_reason_and_stores_note(self):
        wizard = self.env['crm.lead.lost'].create({
            'lead_ids': [(6, 0, self.lead.ids)],
            'lost_reason_id': self.reason.id,
            'lost_note': 'Chose a cheaper competitor',
        })
        wizard.action_lost_reason_apply()

        self.assertFalse(self.lead.active)
        self.assertEqual(self.lead.lost_reason_id, self.reason)
        self.assertEqual(self.lead.lost_reason_category, 'competitor')
        self.assertEqual(self.lead.lost_note, 'Chose a cheaper competitor')
