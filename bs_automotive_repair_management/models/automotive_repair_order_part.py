from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

CONSUMPTION_LOCATION_XMLID = 'bs_automotive_repair_management.stock_location_repair_consumption'
PICKING_TYPE_XMLID = 'bs_automotive_repair_management.stock_picking_type_repair'


class AutomotiveRepairOrderPart(models.Model):
    _name = 'automotive.repair.order.part'
    _description = 'Repair Order Part Line'

    order_id = fields.Many2one(
        'automotive.repair.order', required=True, ondelete='cascade', index=True,
    )
    order_type = fields.Selection(related='order_id.order_type')
    product_id = fields.Many2one('product.product', string='Part', required=True)
    quantity = fields.Float(default=1.0, required=True)
    unit_cost = fields.Float(string='Unit Cost')

    stock_move_id = fields.Many2one('stock.move', readonly=True, copy=False)
    lot_id = fields.Many2one(
        'stock.lot', string='Lot/Serial',
        help='Populated automatically from the stock move once the part is '
             'consumed — this IS the warranty tracking number (§2), not a '
             'duplicate field.',
    )
    manual_tracking_ref = fields.Char(
        string='Manual Tracking Ref',
        help='Fallback for non-lot-tracked parts (bulk fluids, generic '
             'hardware) where a batch/vendor-invoice reference is still '
             'wanted on file.',
    )

    warranty_months = fields.Integer()
    warranty_start_date = fields.Date()
    warranty_end_date = fields.Date(compute='_compute_warranty_end_date', store=True)
    covered_by_warranty = fields.Boolean(string='Covered by Warranty')

    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='order_id.currency_id')

    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('quantity', 'unit_cost', 'covered_by_warranty')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = 0.0 if line.covered_by_warranty else line.quantity * line.unit_cost

    @api.depends('product_id.display_name', 'order_id.name', 'quantity', 'lot_id.name', 'manual_tracking_ref')
    def _compute_display_name(self):
        """Part lines have no 'name' field of their own, so without this the
        default fallback is a bare id — useless in a selection dropdown like
        the warranty claim's origin_part_line_id (§the "which part is this"
        confusion). Identify the line by product + order + tracking ref."""
        for line in self:
            label = line.product_id.display_name or _('Part')
            if line.order_id.name:
                label = _('%(product)s — %(order)s') % {'product': label, 'order': line.order_id.name}
            tracking = line.lot_id.name or line.manual_tracking_ref
            if tracking:
                label = '%s [%s]' % (label, tracking)
            if line.quantity and line.quantity != 1:
                label = _('%(label)s (qty %(qty)s)') % {'label': label, 'qty': line.quantity}
            line.display_name = label

    @api.depends('warranty_start_date', 'warranty_months')
    def _compute_warranty_end_date(self):
        for line in self:
            if line.warranty_start_date and line.warranty_months:
                line.warranty_end_date = line.warranty_start_date + relativedelta(months=line.warranty_months)
            else:
                line.warranty_end_date = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.unit_cost = self.product_id.standard_price
            self.warranty_months = self.product_id.warranty_months

    @api.onchange('order_id')
    def _onchange_order_id(self):
        if self.order_id and self.order_id.order_type == 'warranty_claim':
            self.covered_by_warranty = True

    # ------------------------------------------------------------------
    # Stock move lifecycle — one draft stock.move per part line, grouped
    # under the order's picking, consumed on action_start() (§ build step 3)
    # ------------------------------------------------------------------

    def _get_or_create_picking(self):
        order = self.order_id
        if order.picking_id:
            return order.picking_id
        picking_type = self._get_repair_picking_type(order.company_id)
        source_location = self.env['stock.warehouse'].search(
            [('company_id', '=', order.company_id.id)], limit=1,
        ).lot_stock_id
        dest_location = self.env.ref(CONSUMPTION_LOCATION_XMLID)
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'origin': order.name,
            'partner_id': order.partner_id.id,
        })
        order.picking_id = picking
        return picking

    def _get_repair_picking_type(self, company):
        """One stock.picking.type per company. A stock.picking's company
        must match its picking type's company, so the single picking type
        seeded by data/stock_data.xml only works for whichever company
        happens to be base.main_company — every other company needs its
        own, created lazily here on first use rather than pre-seeded for
        companies that don't exist yet at install time."""
        picking_type = self.env['stock.picking.type'].search([
            ('company_id', '=', company.id),
            ('sequence_code', '=', 'RPARTS'),
        ], limit=1)
        if picking_type:
            return picking_type
        base_type = self.env.ref(PICKING_TYPE_XMLID)
        if base_type.company_id == company:
            return base_type
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company.id)], limit=1)
        if not warehouse:
            raise UserError(_(
                'No warehouse is configured for company %s — cannot set up parts '
                'consumption for repair orders in that company.'
            ) % company.name)
        sequence = self.env['ir.sequence'].create({
            'name': _('Repair Order Parts (%s)') % company.name,
            'code': 'stock.picking.repair',
            'company_id': company.id,
            'prefix': 'RPARTS/',
            'padding': 5,
        })
        return self.env['stock.picking.type'].create({
            'name': base_type.name,
            'code': 'internal',
            'sequence_id': sequence.id,
            'sequence_code': 'RPARTS',
            'default_location_src_id': warehouse.lot_stock_id.id,
            'default_location_dest_id': base_type.default_location_dest_id.id,
            'company_id': company.id,
        })

    def _prepare_stock_move_vals(self, picking):
        self.ensure_one()
        return {
            'product_id': self.product_id.id,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'company_id': self.order_id.company_id.id,
        }

    def _sync_stock_move(self):
        for line in self:
            if not line.product_id:
                continue
            if line.stock_move_id and line.stock_move_id.state == 'done':
                continue
            picking = line._get_or_create_picking()
            if line.stock_move_id:
                line.stock_move_id.write(line._prepare_stock_move_vals(picking))
            else:
                line.stock_move_id = self.env['stock.move'].create(line._prepare_stock_move_vals(picking))

    def _default_cost_vals(self, vals):
        """Fill in unit_cost/warranty_months from the product server-side.

        unit_cost is hidden from non-managers in the view (§10), which means
        the field is stripped from the arch for them and never reaches
        create()/write() at all — relying on the client-side onchange alone
        silently leaves it at 0, the same trap the discount cap and
        covered_by_warranty defaults had to avoid. Only fills in when the key
        is genuinely absent, so a manager who explicitly enters 0 is
        respected."""
        if vals.get('product_id') and 'unit_cost' not in vals:
            product = self.env['product.product'].browse(vals['product_id'])
            vals['unit_cost'] = product.standard_price
            if 'warranty_months' not in vals:
                vals['warranty_months'] = product.warranty_months
        return vals

    def _check_manager_only_fields(self, vals, order=None):
        """unit_cost/covered_by_warranty control what the customer is
        billed. Both are stripped from the view arch for non-managers (§10),
        but that is a client-side courtesy only — the ORM has no idea a
        write came from outside the intended UI, so without this check any
        Technician-level API session could set unit_cost directly, or flip
        covered_by_warranty to zero out a line's subtotal on a standard
        (non-warranty) order. covered_by_warranty is compared against its
        natural system-derived value rather than blocked outright, since
        _onchange_order_id()/create() legitimately pre-fill it True for
        warranty_claim orders and that value must still round-trip through
        a Technician's save."""
        if 'unit_cost' in vals:
            raise AccessError(_('Only a Shop Manager can set the unit cost on a part line.'))
        if 'covered_by_warranty' in vals:
            natural_value = bool(order and order.order_type == 'warranty_claim')
            if bool(vals['covered_by_warranty']) != natural_value:
                raise AccessError(_(
                    'Only a Shop Manager can mark a part line as covered by warranty on a '
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
            self._default_cost_vals(vals)
        lines = super().create(vals_list)
        lines._sync_stock_move()
        lines.mapped('order_id')._apply_pricing_rules()
        return lines

    def write(self, vals):
        if vals.keys() & {'product_id', 'quantity'}:
            for line in self:
                if line.stock_move_id and line.stock_move_id.state == 'done':
                    raise UserError(_(
                        'Part line for %s has already been consumed from stock and can no '
                        'longer be changed.'
                    ) % line.product_id.display_name)
        if (vals.keys() & {'unit_cost', 'covered_by_warranty'}
                and not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager')):
            for line in self:
                self._check_manager_only_fields(vals, order=line.order_id)
        if 'product_id' in vals:
            self._default_cost_vals(vals)
        res = super().write(vals)
        if vals.keys() & {'product_id', 'quantity'}:
            self._sync_stock_move()
        self.mapped('order_id')._apply_pricing_rules()
        return res

    def unlink(self):
        moves = self.mapped('stock_move_id').filtered(lambda m: m.state != 'done')
        orders = self.mapped('order_id')
        res = super().unlink()
        moves._action_cancel()
        orders._apply_pricing_rules()
        return res
