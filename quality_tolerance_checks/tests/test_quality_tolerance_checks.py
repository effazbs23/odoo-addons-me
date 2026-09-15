from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestQualityToleranceChecks(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Shaft Assembly',
            'type': 'consu',
        })
        cls.point = cls.env['quality.point'].create({
            'title': 'Outer Diameter',
            'product_ids': [(6, 0, [cls.product.id])],
            'test_type': 'tolerance_check',
            'tolerance_mode': 'range',
            'tolerance_target': 50.0,
            'tolerance_min': 49.0,
            'tolerance_max': 50.5,
            'norm_unit': 'mm',
        })

    def _create_check(self):
        return self.env['quality.check'].create({
            'product_id': self.product.id,
            'point_id': self.point.id,
        })

    def test_tolerance_snapshotted_on_create(self):
        check = self._create_check()
        self.assertEqual(check.tolerance_target, 50.0)
        self.assertEqual(check.tolerance_min, 49.0)
        self.assertEqual(check.tolerance_max, 50.5)
        self.assertEqual(check.tolerance_norm_unit, 'mm')

    def test_snapshot_is_frozen_after_point_change(self):
        check = self._create_check()
        self.point.write({'tolerance_min': 10.0, 'tolerance_max': 20.0})
        self.assertEqual(check.tolerance_min, 49.0)
        self.assertEqual(check.tolerance_max, 50.5)

    def test_passing_measurement_sets_pass_and_no_alert(self):
        check = self._create_check()
        alert_count_before = self.env['quality.alert'].search_count([])
        check.write({'measured_value': 50.1})
        self.assertEqual(check.quality_state, 'pass')
        self.assertEqual(self.env['quality.alert'].search_count([]), alert_count_before)

    def test_failing_measurement_sets_fail_and_creates_one_alert(self):
        check = self._create_check()
        alert_count_before = self.env['quality.alert'].search_count([])
        check.write({'measured_value': 60.0})
        self.assertEqual(check.quality_state, 'fail')
        alerts = self.env['quality.alert'].search([('check_id', '=', check.id)])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(
            self.env['quality.alert'].search_count([]), alert_count_before + 1)

    def test_onchange_symmetric_absolute(self):
        point = self.env['quality.point'].new({
            'test_type': 'tolerance_check',
            'tolerance_mode': 'symmetric',
            'tolerance_deviation_type': 'absolute',
            'tolerance_target': 100.0,
            'tolerance_deviation': 2.5,
        })
        point._onchange_tolerance_symmetric()
        self.assertEqual(point.tolerance_min, 97.5)
        self.assertEqual(point.tolerance_max, 102.5)

    def test_onchange_symmetric_percentage(self):
        point = self.env['quality.point'].new({
            'test_type': 'tolerance_check',
            'tolerance_mode': 'symmetric',
            'tolerance_deviation_type': 'percentage',
            'tolerance_target': 200.0,
            'tolerance_deviation': 5.0,
        })
        point._onchange_tolerance_symmetric()
        self.assertEqual(point.tolerance_min, 190.0)
        self.assertEqual(point.tolerance_max, 210.0)

    def test_onchange_range_mode_leaves_min_max_untouched(self):
        point = self.env['quality.point'].new({
            'test_type': 'tolerance_check',
            'tolerance_mode': 'range',
            'tolerance_target': 100.0,
            'tolerance_min': 80.0,
            'tolerance_max': 120.0,
        })
        point._onchange_tolerance_symmetric()
        self.assertEqual(point.tolerance_min, 80.0)
        self.assertEqual(point.tolerance_max, 120.0)

    def test_sibling_check_ids_history(self):
        check_1 = self._create_check()
        check_1.write({'measured_value': 50.1})
        check_2 = self._create_check()
        check_2.write({'measured_value': 49.9})
        check_3 = self._create_check()
        check_3.write({'measured_value': 60.0})

        self.assertIn(check_1, check_3.sibling_check_ids)
        self.assertIn(check_2, check_3.sibling_check_ids)
        self.assertNotIn(check_3, check_3.sibling_check_ids)
