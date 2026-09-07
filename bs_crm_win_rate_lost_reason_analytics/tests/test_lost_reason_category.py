from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLostReasonCategory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reason_pricing = cls.env['crm.lost.reason'].create({
            'name': 'Too pricey (test)',
            'category': 'pricing',
        })
        cls.reason_timing = cls.env['crm.lost.reason'].create({
            'name': 'Bad timing (test)',
            'category': 'timing',
        })
        cls.lead = cls.env['crm.lead'].create({'name': 'Test Lead'})

    def test_category_required_defaults_to_other(self):
        reason = self.env['crm.lost.reason'].create({'name': 'No category given (test)'})
        self.assertEqual(reason.category, 'other')

    def test_lost_reason_category_mirrors_reason(self):
        self.lead.write({'lost_reason_id': self.reason_pricing.id})
        self.assertEqual(self.lead.lost_reason_category, 'pricing')

        self.lead.write({'lost_reason_id': self.reason_timing.id})
        self.assertEqual(self.lead.lost_reason_category, 'timing')

    def test_lost_reason_category_clears_when_reason_cleared(self):
        self.lead.write({'lost_reason_id': self.reason_pricing.id})
        self.lead.write({'lost_reason_id': False})
        self.assertFalse(self.lead.lost_reason_category)

    def test_reopen_clears_lost_note_and_category(self):
        self.lead.action_set_lost(lost_reason_id=self.reason_pricing.id, lost_note='Went with a competitor')
        self.assertEqual(self.lead.lost_reason_category, 'pricing')
        self.assertEqual(self.lead.lost_note, 'Went with a competitor')

        self.lead.action_unarchive()
        self.assertFalse(self.lead.lost_reason_id)
        self.assertFalse(self.lead.lost_reason_category)
        self.assertFalse(self.lead.lost_note)
