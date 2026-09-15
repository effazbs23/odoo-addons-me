from odoo import api, fields, models


class QualityCheck(models.Model):
    _inherit = 'quality.check'

    # Snapshotted from the point at check-creation time (plain stored
    # fields, NOT `related`) so a check's recorded tolerance stays frozen
    # for audit history even if the point's configuration changes later.
    tolerance_target = fields.Float('Target Value', readonly=True, copy=False)
    tolerance_min = fields.Float('Minimum', readonly=True, copy=False)
    tolerance_max = fields.Float('Maximum', readonly=True, copy=False)
    tolerance_norm_unit = fields.Char('Unit', readonly=True, copy=False)

    measured_value = fields.Float('Measured Value', copy=False)

    sibling_check_ids = fields.Many2many(
        'quality.check', compute='_compute_sibling_check_ids',
        string='Measurement History')

    @api.model_create_multi
    def create(self, vals_list):
        checks = super().create(vals_list)
        for check in checks:
            if check.point_id.test_type == 'tolerance_check':
                check.write({
                    'tolerance_target': check.point_id.tolerance_target,
                    'tolerance_min': check.point_id.tolerance_min,
                    'tolerance_max': check.point_id.tolerance_max,
                    'tolerance_norm_unit': check.point_id.norm_unit,
                })
        return checks

    def _tolerance_pass_fail(self):
        """Return 'pass'/'fail' for the current measured_value against the
        recorded tolerance range, or False if not applicable."""
        self.ensure_one()
        if self.point_id.test_type != 'tolerance_check' or not self.measured_value:
            return False
        if self.tolerance_min <= self.measured_value <= self.tolerance_max:
            return 'pass'
        return 'fail'

    @api.onchange('measured_value')
    def _onchange_measured_value(self):
        for check in self:
            state = check._tolerance_pass_fail()
            if state:
                check.quality_state = state

    def write(self, vals):
        res = super().write(vals)
        if 'measured_value' in vals:
            for check in self:
                if check.point_id.test_type != 'tolerance_check':
                    continue
                state = check._tolerance_pass_fail()
                if state and state != check.quality_state:
                    super(QualityCheck, check).write({'quality_state': state})
                    if state == 'fail':
                        check._create_tolerance_alert()
        return res

    def action_view_control_chart(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Control Chart',
            'res_model': 'quality.check',
            'view_mode': 'graph',
            'views': [(self.env.ref(
                'quality_tolerance_checks.view_quality_check_graph_control_chart').id,
                'graph')],
            'domain': [('point_id', '=', self.point_id.id)],
            'target': 'current',
        }

    def _create_tolerance_alert(self):
        self.ensure_one()
        point = self.point_id
        point_name = point.title or point.display_name
        unit = self.tolerance_norm_unit or ''
        unit_suffix = (' %s' % unit) if unit else ''
        description = (
            "Measured value %(measured)s%(unit)s is out of tolerance "
            "(target %(target)s%(unit)s, min %(min)s%(unit)s, "
            "max %(max)s%(unit)s)."
        ) % {
            'measured': self.measured_value,
            'target': self.tolerance_target,
            'min': self.tolerance_min,
            'max': self.tolerance_max,
            'unit': unit_suffix,
        }
        vals = {
            'title': "Out of tolerance: %s" % point_name,
            'description': description,
            'check_id': self.id,
            'product_id': self.product_id.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
        }
        # `quality.point` does not carry a `team_id` field in every core
        # version/edition; copy it defensively only if present, rather
        # than assuming it exists.
        if hasattr(point, 'team_id') and point.team_id:
            vals['team_id'] = point.team_id.id
        return self.env['quality.alert'].create(vals)

    @api.depends('point_id', 'point_id.test_type', 'measured_value')
    def _compute_sibling_check_ids(self):
        for check in self:
            if check.point_id and check.point_id.test_type == 'tolerance_check':
                check.sibling_check_ids = self.env['quality.check'].search([
                    ('point_id', '=', check.point_id.id),
                    ('measured_value', '!=', False),
                    ('id', '!=', check.id),
                ], order='create_date desc', limit=50)
            else:
                check.sibling_check_ids = False
