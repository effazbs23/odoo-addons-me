from odoo import api, fields, models


class QualityPoint(models.Model):
    _inherit = 'quality.point'

    test_type = fields.Selection(
        selection_add=[('tolerance_check', 'Tolerance Check')],
        ondelete={'tolerance_check': 'set default'})

    tolerance_mode = fields.Selection([
        ('symmetric', 'Symmetric (±)'),
        ('range', 'Min / Max Range'),
    ], string='Tolerance Mode', default='symmetric')
    tolerance_deviation_type = fields.Selection([
        ('absolute', 'Absolute'),
        ('percentage', 'Percentage (%)'),
    ], string='Deviation Type', default='absolute')
    tolerance_target = fields.Float('Target Value')
    tolerance_deviation = fields.Float('Tolerance (±)')
    tolerance_min = fields.Float('Minimum')
    tolerance_max = fields.Float('Maximum')

    # `norm_unit` (Char) is reused as-is from core's existing 'measure'
    # test type to label the unit of the target/min/max/measured values
    # (e.g. "mm") -- no new unit field is added by this module.

    @api.onchange('tolerance_mode', 'tolerance_target', 'tolerance_deviation',
                  'tolerance_deviation_type')
    def _onchange_tolerance_symmetric(self):
        """Convenience auto-fill of min/max from target +/- deviation when
        in symmetric mode. This is a one-way onchange helper only: min/max
        remain plain, independently editable fields at all times (in
        'range' mode they are left completely untouched)."""
        for point in self:
            if point.tolerance_mode != 'symmetric':
                continue
            if point.tolerance_deviation_type == 'percentage':
                deviation = point.tolerance_target * (point.tolerance_deviation / 100.0)
            else:
                deviation = point.tolerance_deviation
            point.tolerance_min = point.tolerance_target - deviation
            point.tolerance_max = point.tolerance_target + deviation
