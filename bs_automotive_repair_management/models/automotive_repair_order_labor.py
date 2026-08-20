from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class AutomotiveRepairOrderLabor(models.Model):
    _name = 'automotive.repair.order.labor'
    _description = 'Repair Order Labor Line'

    order_id = fields.Many2one(
        'automotive.repair.order', required=True, ondelete='cascade', index=True,
    )
    order_type = fields.Selection(related='order_id.order_type')
    vehicle_id = fields.Many2one('automotive.vehicle', related='order_id.vehicle_id', store=True)
    technician_id = fields.Many2one('hr.employee', string='Technician')
    work_date = fields.Date(
        default=fields.Date.context_today,
        help='The day this labor was actually performed — used for employee '
             'hours-worked stats, not tied to the order state.',
    )
    service_id = fields.Many2one(
        'automotive.service.catalog', string='Service',
        help='Optional catalog lookup — pre-fills description/hours/rate but '
             'stays fully editable for ad hoc work outside the catalog.',
    )
    description = fields.Char(required=True)
    hours = fields.Float(default=0.0)
    hourly_rate = fields.Float()
    covered_by_warranty = fields.Boolean(
        string='Covered by Warranty',
        help='Only meaningful on warranty_claim orders (§6). Zeroes this '
             "line's contribution to billing when set.",
    )
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='order_id.currency_id')

    @api.depends('hours', 'hourly_rate', 'covered_by_warranty')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = 0.0 if line.covered_by_warranty else line.hours * line.hourly_rate

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.description = self.service_id.name
            self.hours = self.service_id.estimated_hours
            self.hourly_rate = self.service_id.default_hourly_rate

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        order = self.env['automotive.repair.order'].browse(self.env.context.get('default_order_id'))
        if order and order.order_type == 'warranty_claim':
            vals['covered_by_warranty'] = True
        return vals

    def _default_rate_vals(self, vals):
        """Fill in hourly_rate/description/hours from the service catalog
        entry server-side — hourly_rate is hidden from non-managers in the
        view (§10), so the field is stripped from the arch for them and
        never reaches create()/write() at all. Relying on the client-side
        onchange alone silently leaves it at 0. Only fills in when the key
        is genuinely absent, so a manager who explicitly enters a rate is
        respected."""
        if vals.get('service_id'):
            service = self.env['automotive.service.catalog'].browse(vals['service_id'])
            if 'hourly_rate' not in vals:
                vals['hourly_rate'] = service.default_hourly_rate
            if 'hours' not in vals:
                vals['hours'] = service.estimated_hours
            if 'description' not in vals:
                vals['description'] = service.name
        return vals

    def _check_manager_only_fields(self, vals, order=None):
        """hourly_rate/covered_by_warranty control what the customer is
        billed. Both are stripped from the view arch for non-managers (§10),
        but that is a client-side courtesy only — the ORM has no idea a
        write came from outside the intended UI, so without this check any
        Technician-level API session could set hourly_rate directly, or
        flip covered_by_warranty to zero out a line's subtotal on a
        standard (non-warranty) order. covered_by_warranty is compared
        against its natural system-derived value rather than blocked
        outright, since default_get()/create() legitimately pre-fill it
        True for warranty_claim orders and that value must still round-trip
        through a Technician's save."""
        if 'hourly_rate' in vals:
            raise AccessError(_('Only a Shop Manager can set the hourly rate on a labor line.'))
        if 'covered_by_warranty' in vals:
            natural_value = bool(order and order.order_type == 'warranty_claim')
            if bool(vals['covered_by_warranty']) != natural_value:
                raise AccessError(_(
                    'Only a Shop Manager can mark a labor line as covered by warranty on a '
                    'standard (non-warranty-claim) order.'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        is_manager = self.env.user.has_group('bs_automotive_repair_management.group_shop_manager')
        for vals in vals_list:
            order = self.env['automotive.repair.order'].browse(vals.get('order_id'))
            if not is_manager:
                self._check_manager_only_fields(vals, order=order)
            if 'covered_by_warranty' not in vals and order and order.order_type == 'warranty_claim':
                vals['covered_by_warranty'] = True
            self._default_rate_vals(vals)
        lines = super().create(vals_list)
        lines.order_id._apply_pricing_rules()
        return lines

    def write(self, vals):
        if (vals.keys() & {'hourly_rate', 'covered_by_warranty'}
                and not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager')):
            for line in self:
                self._check_manager_only_fields(vals, order=line.order_id)
        if 'service_id' in vals:
            self._default_rate_vals(vals)
        res = super().write(vals)
        self.mapped('order_id')._apply_pricing_rules()
        return res

    def unlink(self):
        orders = self.mapped('order_id')
        res = super().unlink()
        orders._apply_pricing_rules()
        return res
