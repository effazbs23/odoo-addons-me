from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpBomVariantMatrix(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        color_attr = cls.env['product.attribute'].create({
            'name': 'Test Color', 'create_variant': 'always',
        })
        cls.color_black, cls.color_white = cls.env['product.attribute.value'].create([
            {'name': 'Black', 'attribute_id': color_attr.id},
            {'name': 'White', 'attribute_id': color_attr.id},
        ])
        material_attr = cls.env['product.attribute'].create({
            'name': 'Test Material', 'create_variant': 'always',
        })
        cls.mat_fabric, cls.mat_leather = cls.env['product.attribute.value'].create([
            {'name': 'Fabric', 'attribute_id': material_attr.id},
            {'name': 'Leather', 'attribute_id': material_attr.id},
        ])

        cls.template = cls.env['product.template'].create({
            'name': 'Test Chair',
            'type': 'consu',
            'is_storable': True,
            'attribute_line_ids': [
                (0, 0, {
                    'attribute_id': color_attr.id,
                    'value_ids': [(6, 0, [cls.color_black.id, cls.color_white.id])],
                }),
                (0, 0, {
                    'attribute_id': material_attr.id,
                    'value_ids': [(6, 0, [cls.mat_fabric.id, cls.mat_leather.id])],
                }),
            ],
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component', 'type': 'consu',
        })
        cls.bom = cls.env['mrp.bom'].create({
            'product_tmpl_id': cls.template.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': cls.component.id,
                'product_qty': 1.0,
            })],
        })
        cls.line = cls.bom.bom_line_ids[0]

        def _variant(color, material):
            return cls.template.product_variant_ids.filtered(
                lambda v: color in v.product_template_attribute_value_ids.mapped('product_attribute_value_id')
                and material in v.product_template_attribute_value_ids.mapped('product_attribute_value_id')
            )

        cls.black_fabric = _variant(cls.color_black, cls.mat_fabric)
        cls.white_fabric = _variant(cls.color_white, cls.mat_fabric)
        cls.black_leather = _variant(cls.color_black, cls.mat_leather)
        cls.white_leather = _variant(cls.color_white, cls.mat_leather)

    def test_matrix_default_applies_to_all(self):
        data = self.bom.get_variant_matrix_data()
        row = data['rows'][0]
        self.assertTrue(all(row['cells'].values()))
        self.assertEqual(len(data['variants']), 4)

    def test_toggle_off_one_attribute_value_group_is_exact(self):
        result = self.bom.set_variant_matrix_cell(
            self.line.id, self.black_leather.id, False)
        self.assertFalse(result['exact'])  # single variant off, no shared attr with fabric ones off too

    def test_bulk_remove_whole_material_group_is_exact(self):
        result = self.bom.set_variant_matrix_bulk(
            [self.line.id],
            [self.black_leather.id, self.white_leather.id],
            False,
        )
        self.assertTrue(result['exact'])
        row = result['matrix']['rows'][0]
        self.assertFalse(row['cells'][self.black_leather.id])
        self.assertFalse(row['cells'][self.white_leather.id])
        self.assertTrue(row['cells'][self.black_fabric.id])
        self.assertTrue(row['cells'][self.white_fabric.id])

    def test_zero_applicable_lines_warning(self):
        self.bom.set_variant_matrix_bulk(
            [self.line.id],
            [self.black_leather.id, self.white_leather.id, self.black_fabric.id, self.white_fabric.id],
            False,
        )
        data = self.bom.get_variant_matrix_data()
        self.assertFalse(data['rows'][0]['cells'][self.black_fabric.id])
        self.assertTrue(any(
            w['variant_id'] == self.black_fabric.id for w in data['warnings']))

    def test_preview_variant_uses_core_explode(self):
        preview = self.bom.action_preview_variant(self.black_fabric.id)
        self.assertEqual(len(preview['rows']), 1)
        self.assertEqual(preview['rows'][0]['name'], self.component.display_name)

    def test_copy_variant_bom(self):
        self.bom.set_variant_matrix_bulk(
            [self.line.id], [self.black_leather.id, self.white_leather.id], False)
        result = self.bom.action_copy_variant_bom(
            self.black_leather.id, self.black_fabric.id)
        row = result['matrix']['rows'][0]
        # black_fabric should now mirror black_leather (line does not apply)
        self.assertFalse(row['cells'][self.black_fabric.id])
