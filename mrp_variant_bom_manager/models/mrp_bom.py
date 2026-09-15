from odoo import models
from odoo.exceptions import UserError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    def _variant_matrix_variants(self):
        self.ensure_one()
        return self.product_tmpl_id.product_variant_ids.filtered('active')

    def _variant_matrix_line_applies(self, line, variant):
        required = line.bom_product_template_attribute_value_ids
        if not required:
            return True
        variant_ptavs = variant.product_template_attribute_value_ids
        return all(ptav in variant_ptavs for ptav in required)

    def get_variant_matrix_data(self):
        """Build the row/column data for the Variant Matrix widget."""
        self.ensure_one()
        variants = self._variant_matrix_variants()

        rows = []
        for line in self.bom_line_ids:
            cells = {}
            for variant in variants:
                cells[variant.id] = self._variant_matrix_line_applies(line, variant)
            rows.append({
                'line_id': line.id,
                'name': line.product_id.display_name,
                'code': line.product_id.default_code or '',
                'qty': line.product_qty,
                'cells': cells,
            })

        warnings = []
        for variant in variants:
            if not any(row['cells'][variant.id] for row in rows):
                warnings.append({
                    'variant_id': variant.id,
                    'message': "%s has zero applicable BOM lines and will "
                               "fail to manufacture." % variant.display_name,
                })

        return {
            'bom_id': self.id,
            'product_tmpl_name': self.product_tmpl_id.display_name,
            'variants': [{
                'id': variant.id,
                'name': ', '.join(
                    variant.product_template_attribute_value_ids.mapped('name')
                ) or variant.display_name,
            } for variant in variants],
            'rows': rows,
            'warnings': warnings,
        }

    def set_variant_matrix_cell(self, line_id, variant_id, applies):
        """Toggle a single (line, variant) cell.

        `bom_product_template_attribute_value_ids` only supports an
        AND-of-attribute-values filter (a line applies to every variant
        whose combination is a superset of the chosen values), it cannot
        encode an arbitrary subset of variants directly. To keep this a
        UI/UX layer with no new data model (per specs.md), each toggle is
        resolved by recomputing the *smallest common set of attribute
        values* shared by every variant that should end up "on" for this
        line. When no such exact set exists (the requested on/off pattern
        can't be expressed as a single AND-filter), the underlying filter
        is left untouched and `exact` is returned False so the UI can warn
        the user instead of silently applying something else.
        """
        line = self.env['mrp.bom.line'].browse(line_id)
        line.ensure_one()
        variants = self._variant_matrix_variants()
        current_on = {v.id for v in variants if self._variant_matrix_line_applies(line, v)}
        if applies:
            current_on.add(variant_id)
        else:
            current_on.discard(variant_id)

        exact = self._apply_line_variant_set(line, variants, current_on)
        return {'exact': exact, 'matrix': self.get_variant_matrix_data()}

    def set_variant_matrix_bulk(self, line_ids, variant_ids, applies):
        """Apply/remove several lines x several variants in one action."""
        variants = self._variant_matrix_variants()
        results = {}
        for line in self.env['mrp.bom.line'].browse(line_ids):
            current_on = {v.id for v in variants if self._variant_matrix_line_applies(line, v)}
            if applies:
                current_on |= set(variant_ids)
            else:
                current_on -= set(variant_ids)
            results[line.id] = self._apply_line_variant_set(line, variants, current_on)
        return {'exact': all(results.values()), 'matrix': self.get_variant_matrix_data()}

    def _apply_line_variant_set(self, line, all_variants, on_variant_ids):
        """Try to express `on_variant_ids` as a single AND-of-ptav filter on
        `line`. Returns True and writes the filter if an exact set exists,
        False (no write) otherwise."""
        on_variants = all_variants.filtered(lambda v: v.id in on_variant_ids)
        off_variants = all_variants - on_variants

        if not on_variants:
            # "Applies to nobody" cannot be expressed by this field (an
            # empty filter means "applies to everybody"). Leave untouched.
            return False

        ptav_sets = [set(v.product_template_attribute_value_ids.ids) for v in on_variants]
        common = set.intersection(*ptav_sets) if ptav_sets else set()

        if common:
            conflicting = off_variants.filtered(
                lambda v: common.issubset(set(v.product_template_attribute_value_ids.ids)))
            if not conflicting:
                line.bom_product_template_attribute_value_ids = [(6, 0, list(common))]
                return True

        if len(on_variants) == len(all_variants):
            # Applies to every variant: clearing the filter is exact.
            line.bom_product_template_attribute_value_ids = [(5, 0, 0)]
            return True

        return False

    def action_open_variant_matrix(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Variant Matrix',
            'res_model': 'mrp.bom.variant.matrix.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_bom_id': self.id},
        }

    def action_preview_variant(self, variant_id):
        self.ensure_one()
        variant = self.env['product.product'].browse(variant_id)
        if not variant.exists():
            raise UserError("Select a valid variant to preview.")
        boms, lines = self.explode(variant, 1.0)
        rows = []
        for bom_line, line_data in lines:
            rows.append({
                'name': bom_line.product_id.display_name,
                'code': bom_line.product_id.default_code or '',
                'qty': line_data.get('qty', bom_line.product_qty),
            })
        return {
            'variant_id': variant.id,
            'variant_name': variant.display_name,
            'rows': rows,
        }

    def action_copy_variant_bom(self, source_variant_id, target_variant_id):
        """Copy every line's applicability from source_variant onto
        target_variant, leaving other variants' applicability untouched
        where representable."""
        self.ensure_one()
        variants = self._variant_matrix_variants()
        all_exact = True
        for line in self.bom_line_ids:
            applies_to_source = self._variant_matrix_line_applies(
                line, self.env['product.product'].browse(source_variant_id))
            current_on = {v.id for v in variants if self._variant_matrix_line_applies(line, v)}
            if applies_to_source:
                current_on.add(target_variant_id)
            else:
                current_on.discard(target_variant_id)
            if not self._apply_line_variant_set(line, variants, current_on):
                all_exact = False
        return {'exact': all_exact, 'matrix': self.get_variant_matrix_data()}
