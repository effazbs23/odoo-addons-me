from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpIntercompanyWoSync(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref('base.main_company')
        cls.company_b = cls.env['res.company'].create({
            'name': 'Test Company B (Manufacturer)',
        })
        # A company needs a partner_id to receive an intercompany PO; core
        # Odoo creates one automatically on company creation.
        cls.component = cls.env['product.product'].create({
            'name': 'Intercompany Test Component',
            'type': 'consu',
            'is_storable': True,
            'intercompany_manufacturer_id': cls.company_b.id,
        })
        cls.finished_good = cls.env['product.product'].create({
            'name': 'Intercompany Test Finished Good',
            'type': 'consu',
            'is_storable': True,
        })

    def _create_production_with_shortage(self):
        production = self.env['mrp.production'].with_company(self.company_a).create({
            'product_id': self.finished_good.id,
            'product_uom_id': self.finished_good.uom_id.id,
            'product_qty': 1.0,
            'company_id': self.company_a.id,
            'move_raw_ids': [(0, 0, {
                'name': self.component.display_name,
                'product_id': self.component.id,
                'product_uom_qty': 10.0,
                'product_uom': self.component.uom_id.id,
                'company_id': self.company_a.id,
            })],
        })
        return production

    def test_intercompany_manufacturer_field(self):
        self.assertEqual(self.component.intercompany_manufacturer_id, self.company_b)
        self.assertEqual(
            self.component.product_tmpl_id.intercompany_manufacturer_id, self.company_b)

    def test_action_create_intercompany_supply_creates_po_and_link(self):
        production = self._create_production_with_shortage()
        links = production.action_create_intercompany_supply()

        self.assertEqual(len(links), 1)
        link = links[0]
        self.assertTrue(link.purchase_order_id)
        self.assertEqual(link.parent_company_id, self.company_a)
        self.assertEqual(link.child_company_id, self.company_b)
        self.assertEqual(link.product_id, self.component)
        self.assertIn(link.state, ('po_created', 'so_confirmed', 'failed'))

    def test_action_create_intercompany_supply_no_duplicate_link(self):
        production = self._create_production_with_shortage()
        links_first = production.action_create_intercompany_supply()
        links_second = production.action_create_intercompany_supply()

        self.assertEqual(len(links_second), 0)
        all_links = self.env['mrp.production.intercompany.link'].search([
            ('parent_production_id', '=', production.id),
            ('product_id', '=', self.component.id),
        ])
        self.assertEqual(len(all_links), len(links_first))

    def test_progress_percentage_computation(self):
        production = self._create_production_with_shortage()
        child_production = self.env['mrp.production'].with_company(self.company_b).create({
            'product_id': self.component.id,
            'product_uom_id': self.component.uom_id.id,
            'product_qty': 10.0,
            'company_id': self.company_b.id,
        })
        link = self.env['mrp.production.intercompany.link'].create({
            'parent_production_id': production.id,
            'child_production_id': child_production.id,
            'parent_company_id': self.company_a.id,
            'child_company_id': self.company_b.id,
            'product_id': self.component.id,
            'product_qty': 10.0,
            'state': 'mo_created',
        })
        child_production.qty_produced = 6.0
        self.assertAlmostEqual(link.progress_percentage, 60.0)

    def test_has_due_date_exception_flips(self):
        production = self._create_production_with_shortage()
        production.date_deadline = fields.Datetime.now() + timedelta(days=2)
        child_production = self.env['mrp.production'].with_company(self.company_b).create({
            'product_id': self.component.id,
            'product_uom_id': self.component.uom_id.id,
            'product_qty': 10.0,
            'company_id': self.company_b.id,
            'date_start': fields.Datetime.now(),
            'date_finished': fields.Datetime.now() + timedelta(days=1),
        })
        link = self.env['mrp.production.intercompany.link'].create({
            'parent_production_id': production.id,
            'child_production_id': child_production.id,
            'parent_company_id': self.company_a.id,
            'child_company_id': self.company_b.id,
            'product_id': self.component.id,
            'product_qty': 10.0,
            'state': 'mo_created',
        })
        self.assertFalse(link.has_due_date_exception)

        child_production.date_finished = fields.Datetime.now() + timedelta(days=5)
        self.assertTrue(link.has_due_date_exception)
        self.assertTrue(link.exception_message)

    def test_cron_runs_without_error(self):
        # Empty link set.
        self.env['mrp.production.intercompany.link']._cron_sync_intercompany_links()

        # Typical, open link set.
        production = self._create_production_with_shortage()
        production.action_create_intercompany_supply()
        self.env['mrp.production.intercompany.link']._cron_sync_intercompany_links()
