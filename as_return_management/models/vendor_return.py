from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Command
from odoo.tools import float_compare, float_is_zero


class ReturnRequest(models.Model):
    _inherit = 'return.request'

    return_operation_type = fields.Selection([
        ('vendor', 'Vendor Return'),
    ], string='Operation Type', default='vendor', required=True, index=True)

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        copy=False,
        required=True,
        domain="[('partner_id', '=', partner_id), ('state', 'in', ('purchase', 'done'))]",
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        copy=False,
        domain="[('move_type', '=', 'in_invoice'), ('state', '=', 'posted'), "
               "('line_ids.purchase_line_id.order_id', '=', purchase_order_id)]",
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Receipt (reference)',
        copy=False,
        domain="[('picking_type_code', '=', 'incoming'), ('state', '=', 'done'), "
               "('move_ids.purchase_line_id.order_id', '=', purchase_order_id)]",
        help='Incoming receipt of the selected PO for reference only. '
             'The actual return ships from the source location chosen below.',
    )

    return_source_location_id = fields.Many2one(
        'stock.location',
        string='Return From Location',
        copy=False,
        domain="[('usage', '=', 'internal'), ('company_id', 'in', (company_id, False))]",
        help='Location the goods will be shipped back from. Defaults to the PO '
             'warehouse stock location; for QC rejections pick the failure location.',
    )

    @api.constrains('return_operation_type', 'purchase_order_id')
    def _check_vendor_po_required(self):
        for record in self:
            if record.return_operation_type == 'vendor' and not record.purchase_order_id:
                raise ValidationError(_(
                    'Purchase Order is mandatory for vendor returns.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('return_operation_type') == 'vendor' and vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('vendor.return.request') or _('New')
        return super().create(vals_list)

    @api.onchange('purchase_order_id')
    def _onchange_vendor_purchase_order(self):
        if self.return_operation_type != 'vendor':
            return
        if not self.purchase_order_id:
            return
        po = self.purchase_order_id
        self.picking_id = False
        self.invoice_id = False
        self.partner_id = po.partner_id
        if not self.return_source_location_id:
            # default to where receipts actually land (the incoming picking
            # type's destination -- e.g. a QC holding area before putaway),
            # not the warehouse's generic stock location: goods may never
            # pass through the latter, which left on-hand at 0 there and
            # silently dropped lot-tracked lines (delivered_qty capped to 0)
            self.return_source_location_id = (
                po.picking_type_id.default_location_dest_id
                or po.picking_type_id.warehouse_id.lot_stock_id)
        self._generate_po_return_lines()

    @api.onchange('return_source_location_id')
    def _onchange_vendor_source_location(self):
        """Regenerate return lines when the return location changes so that
        delivered_qty reflects what is actually at the new location."""
        if self.return_operation_type == 'vendor' and self.purchase_order_id:
            self._generate_po_return_lines()

    def _pol_origin_moves(self, pol):
        """Original DONE incoming receipt moves of a purchase order line,
        newest first. Excludes internal chain moves (e.g. two-step reception
        storage moves) which also carry purchase_line_id and would double the
        apparent coverage. Shared by line generation and picking creation."""
        return pol.move_ids.filtered(
            lambda m: m.state == 'done' and not m.origin_returned_move_id
            and m.location_dest_id.usage != 'supplier'
            and m.picking_id.picking_type_id.code == 'incoming'
        ).sorted(key=lambda m: (m.date, m.id), reverse=True)

    def _generate_po_return_lines(self):
        """Generate return lines from the purchase order.

        Quantities are expressed in the product's UoM. For untracked products,
        one line per goods line of the PO, received quantity capped by what is
        physically on-hand at the selected return source location. For
        lot/serial-tracked products, one line PER LOT actually received
        against the PO line, each capped by that specific lot's on-hand at the
        location -- so the user can only claim a lot that was really received
        and is really still there, never an aggregate across lots.
        """
        self.return_line_ids = [(5, 0, 0)]
        line_vals = []
        po = self.purchase_order_id
        location = self.return_source_location_id
        Quant = self.env['stock.quant']

        for pol in po.order_line:
            product = pol.product_id
            if not product or product.type not in ('product', 'consu'):
                continue
            uom = product.uom_id
            price = pol.price_unit * (1 - (pol.discount or 0.0) / 100.0)
            common_vals = {
                'description': pol.name or product.display_name,
                'ordered_qty': pol.product_uom_id._compute_quantity(pol.product_qty, uom),
                'invoiced_qty': pol.product_uom_id._compute_quantity(max(pol.qty_invoiced, 0.0), uom),
                'price_unit': pol.product_uom_id._compute_price(price, uom),
                'purchase_line_id': pol.id,
                'move_id': False,
            }

            if product.tracking == 'none':
                on_hand = Quant._get_available_quantity(product, location) if location else 0.0
                received = pol.product_uom_id._compute_quantity(
                    max(pol.qty_received, 0.0), uom)
                delivered_qty = min(received, on_hand) if location else received
                line_vals.append((0, 0, dict(
                    common_vals, product_id=product.id, delivered_qty=delivered_qty, lot_id=False)))
                continue

            # lot/serial-tracked: one line per lot actually received, capped
            # by that lot's own on-hand at the location (never aggregated)
            received_by_lot = defaultdict(float)
            for move in self._pol_origin_moves(pol):
                for ml in move.move_line_ids.filtered('lot_id'):
                    received_by_lot[ml.lot_id] += ml.product_uom_id._compute_quantity(ml.quantity, uom)

            for lot, received in received_by_lot.items():
                on_hand = Quant._get_available_quantity(product, location, lot_id=lot) if location else 0.0
                delivered_qty = min(received, on_hand) if location else received
                # always show the line, same as the untracked branch above --
                # delivered_qty can legitimately be 0 (wrong/default location
                # picked, or the lot fully consumed/returned elsewhere), but
                # DROPPING the row entirely made lot-tracked products silently
                # vanish from line generation while untracked ones still
                # appeared, with no indication to the user why
                line_vals.append((0, 0, dict(
                    common_vals, product_id=product.id, delivered_qty=delivered_qty, lot_id=lot.id)))
        self.return_line_ids = line_vals

    def _vendor_return_done_qty_for_pol(self, pol, lot_id=None):
        """Quantity of this request's return-picking chain already DONE for the
        given purchase order line (in product UoM), optionally scoped to a
        specific lot. That portion is already netted out of pol.qty_received.

        Lot scoping reads move_line_ids rather than the move-level aggregate
        quantity: a single move can legitimately carry several lots' lines.
        """
        self.ensure_one()
        total = 0.0
        pending = self.return_picking_id
        while pending:
            moves = pending.move_ids.filtered(
                lambda m: m.state == 'done' and m.purchase_line_id == pol)
            if lot_id:
                for ml in moves.move_line_ids.filtered(lambda ml: ml.lot_id == lot_id):
                    total += ml.product_uom_id._compute_quantity(ml.quantity, pol.product_id.uom_id)
            else:
                for move in moves:
                    total += move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
            pending = self.env['stock.picking'].search([('backorder_id', 'in', pending.ids)])
        return total

    def action_process(self):
        vendor = self.filtered(lambda r: r.return_operation_type == 'vendor')
        for request in vendor:
            request._action_process_vendor()
        return super(ReturnRequest, self - vendor).action_process()

    def _action_process_vendor(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved vendor return requests can be processed.'))
        if not self.return_source_location_id:
            raise UserError(_('Please set the return source location before processing.'))
        lines = self.return_line_ids.filtered(lambda l: l.return_qty > 0)
        if not lines:
            raise UserError(_('Please specify return quantities before processing.'))

        self._check_source_location_stock(lines)
        # compute the refund plan FIRST: it can raise (D3) and must do so
        # before any document is created
        plan = breakdown = None
        if not self.credit_note_id:
            plan, breakdown = self._prepare_vendor_refund_plan(lines)
        if not self.return_picking_id:
            self._create_po_return_picking(lines)
        if plan is not None:
            if plan:
                bill = next(iter(plan)).move_id
                self._reverse_bill_partial(
                    bill, {aml.id: qty for aml, qty in plan.items()})
            self.message_post(body=_('Refund decision:') + '<br/>'
                              + '<br/>'.join(breakdown))

        self.state = 'processing'
        self.message_post(body=_('Vendor return request processed.'))

    def _check_source_location_stock(self, lines):
        """Block processing when the chosen source location cannot cover the
        requested quantities (goods may have been moved, scrapped or consumed)."""
        self.ensure_one()
        location = self.return_source_location_id
        if not location:
            raise UserError(_('Please set the location the goods will be returned from.'))
        Quant = self.env['stock.quant']
        for line in lines:
            on_hand = Quant._get_available_quantity(
                line.product_id, location, lot_id=line.lot_id or None)
            if float_compare(line.return_qty, on_hand,
                             precision_rounding=line.product_id.uom_id.rounding) > 0:
                raise UserError(_(
                    'Not enough stock of %(product)s%(lot)s at %(location)s: %(on_hand)s on hand, '
                    '%(requested)s requested. Move the goods there first or pick the '
                    'location where they actually are.',
                    product=line.product_id.display_name,
                    lot=_(' (lot %s)') % line.lot_id.name if line.lot_id else '',
                    location=location.complete_name,
                    on_hand=on_hand, requested=line.return_qty))

    def _create_po_return_picking(self, lines):
        """Create ONE return-to-vendor picking for a PO-anchored request,
        shipping from the selected source location.

        Unlike the receipt-anchored path (native return wizard), this supports
        goods received through several receipts, moved by multi-step reception,
        or rerouted to a QC failure location. Each return move is chained to an
        original receipt move (newest first) for traceability/valuation and
        carries purchase_line_id + to_refund so the PO received quantity drops
        on validation.
        """
        self.ensure_one()
        po = self.purchase_order_id
        picking_type = po.picking_type_id.return_picking_type_id
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'outgoing'),
                ('warehouse_id', '=', po.picking_type_id.warehouse_id.id),
            ], limit=1)
        if not picking_type:
            raise UserError(_(
                'No return operation type is configured for %s and no outgoing '
                'operation type exists in its warehouse.') % po.picking_type_id.display_name)

        location_dest = self.partner_id.property_stock_supplier
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'location_id': self.return_source_location_id.id,
            'location_dest_id': location_dest.id,
            'origin': _('%(request)s - Return of %(po)s', request=self.name, po=po.name),
            'company_id': self.company_id.id,
        })

        for line in lines:
            pol = line.purchase_line_id
            if not pol:
                raise UserError(_(
                    'Line %s has no purchase order line reference; regenerate the '
                    'lines from the purchase order.') % line.product_id.display_name)
            rounding = line.product_id.uom_id.rounding
            origin_moves = self._pol_origin_moves(pol)
            remaining = line.return_qty
            for origin_move in origin_moves:
                if float_compare(remaining, 0.0, precision_rounding=rounding) <= 0:
                    break
                if line.lot_id:
                    # scope coverage to THIS lot's move lines -- a single
                    # origin move can carry several lots, and a lot-A return
                    # line must never claim against lot-B's portion of it
                    origin_qty = sum(
                        ml.product_uom_id._compute_quantity(ml.quantity, line.product_id.uom_id)
                        for ml in origin_move.move_line_ids if ml.lot_id == line.lot_id
                    )
                else:
                    origin_qty = origin_move.product_uom._compute_quantity(
                        origin_move.quantity, line.product_id.uom_id)
                take = min(remaining, origin_qty)
                if float_compare(take, 0.0, precision_rounding=rounding) <= 0:
                    continue
                move = self.env['stock.move'].create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': take,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id': picking.location_id.id,
                    'location_dest_id': picking.location_dest_id.id,
                    'company_id': self.company_id.id,
                    'origin_returned_move_id': origin_move.id,
                    'purchase_line_id': pol.id,
                    'to_refund': True,
                    'origin': picking.origin,
                })
                if line.lot_id:
                    # Force the exact lot onto the move instead of leaving lot
                    # selection to action_assign()'s own quant-removal
                    # strategy (which would pick whichever lot's quants are
                    # available, not necessarily this one). Creating the move
                    # line up front makes stock.move.line.create()'s reserved-
                    # quantity bookkeeping run immediately for this lot, and
                    # move.quantity (a stored compute = sum(move_line_ids.quantity))
                    # already equals product_uom_qty before action_confirm()/
                    # action_assign() run -- verified empirically: the move's
                    # state flips straight to 'assigned' on move-line creation
                    # (stock.move.line.create() -> _recompute_state()), so
                    # picking.action_confirm()'s state=='draft' filter skips it
                    # entirely below. Do NOT "simplify" this by deleting the
                    # move line and calling bare action_assign() -- that
                    # reintroduces Odoo's own lot auto-selection.
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': line.product_id.id,
                        'product_uom_id': line.product_id.uom_id.id,
                        'lot_id': line.lot_id.id,
                        'quantity': take,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'picking_id': picking.id,
                    })
                remaining -= take
            if float_compare(remaining, 0.0, precision_rounding=rounding) > 0:
                raise UserError(_(
                    'Product %(product)s%(lot)s: %(qty)s exceeds what was received on %(po)s.',
                    product=line.product_id.display_name,
                    lot=_(' (lot %s)') % line.lot_id.name if line.lot_id else '',
                    qty=remaining, po=po.name))

        picking.action_confirm()
        picking.action_assign()
        self.return_picking_id = picking.id

    def _prepare_vendor_refund_plan(self, lines):
        """Compute {bill aml: qty to refund (aml UoM)} and a per-line breakdown.

        Refundable per line = min(returned, net billed qty of the POL); the
        rest is absorbed by future billing. Bills are considered newest first;
        per-aml remaining excludes quantities already refunded (draft AND
        posted refunds, to avoid double-drafting). The refundable total must
        fit a single bill: the explicitly selected one (invoice_id) or the
        newest one that covers every line, otherwise UserError (D3).
        """
        self.ensure_one()
        Aml = self.env['account.move.line']
        breakdown = []
        # refundable/absorbed per line, in product UoM. D1: the unbilled
        # capacity (received − billed) absorbs the return first — that part
        # self-corrects on the next bill; only what eats into already-billed
        # quantity gets refunded.
        needs = {}   # line -> refundable qty (product UoM)
        # unbilled capacity is a property of the POL, not of any one line --
        # with lot support, several lines can now share one purchase_line_id
        # (one per lot), so this pool must be shared and decremented as lines
        # claim it in order, or two lot-lines of the same POL would each
        # independently believe they have the FULL unbilled capacity and
        # over-absorb in aggregate (silently under-refunding the vendor).
        unbilled_remaining = {}   # purchase_line_id -> remaining unbilled qty (product UoM)
        for line in lines:
            pol = line.purchase_line_id
            if not pol:
                breakdown.append(_(
                    '%s: skipped — no purchase order line reference.',
                    line.product_id.display_name))
                continue
            uom = line.product_id.uom_id
            if pol.id not in unbilled_remaining:
                received = pol.product_uom_id._compute_quantity(
                    max(pol.qty_received, 0.0), uom)
                billed = pol.product_uom_id._compute_quantity(
                    max(pol.qty_invoiced, 0.0), uom)
                unbilled_remaining[pol.id] = max(received - billed, 0.0)
            absorbed = min(line.return_qty, unbilled_remaining[pol.id])
            unbilled_remaining[pol.id] -= absorbed
            refundable = line.return_qty - absorbed
            needs[line] = refundable
            rounding = line.product_id.uom_id.rounding
            parts = []
            if not float_is_zero(absorbed, precision_rounding=rounding):
                parts.append(_('%s deducted from unbilled quantity (future bills shrink)') % absorbed)
            if not float_is_zero(refundable, precision_rounding=rounding):
                parts.append(_('%s to refund') % refundable)
            breakdown.append('%s: %s returned — %s' % (
                line.product_id.display_name, line.return_qty,
                ', '.join(parts) or _('nothing to refund')))

        if all(float_is_zero(qty, precision_rounding=line.product_id.uom_id.rounding)
               for line, qty in needs.items()):
            breakdown.append(_('No vendor credit note needed: nothing returned was billed yet.'))
            return {}, breakdown

        # candidate bills, newest first
        pols = lines.mapped('purchase_line_id')
        bill_amls = Aml.search([
            ('purchase_line_id', 'in', pols.ids),
            ('move_id.move_type', '=', 'in_invoice'),
            ('move_id.state', '=', 'posted'),
            ('display_type', '=', 'product'),
        ])
        bills = bill_amls.mapped('move_id').sorted(
            key=lambda m: (m.invoice_date or fields.Date.today(), m.id), reverse=True)
        if self.invoice_id:
            if self.invoice_id not in bills:
                raise UserError(_(
                    'Bill %s is not a posted bill of purchase order %s.'
                ) % (self.invoice_id.name, self.purchase_order_id.name))
            bills = self.invoice_id

        def aml_remaining(aml):
            """billed qty on this aml minus refunds (draft+posted) already
            issued against its bill for the same POL, in aml UoM"""
            refund_amls = Aml.search([
                ('purchase_line_id', '=', aml.purchase_line_id.id),
                ('move_id.move_type', '=', 'in_refund'),
                ('move_id.state', 'in', ('draft', 'posted')),
                ('move_id.reversed_entry_id', '=', aml.move_id.id),
                ('display_type', '=', 'product'),
            ])
            refunded = sum(r.product_uom_id._compute_quantity(
                r.quantity, aml.product_uom_id) for r in refund_amls)
            return aml.quantity - refunded

        for bill in bills:
            plan = {}
            covered = True
            for line, refundable in needs.items():
                rounding = line.product_id.uom_id.rounding
                if float_is_zero(refundable, precision_rounding=rounding):
                    continue
                remaining_need = refundable
                for aml in bill_amls.filtered(
                        lambda a: a.move_id == bill
                        and a.purchase_line_id == line.purchase_line_id):
                    if float_compare(remaining_need, 0.0, precision_rounding=rounding) <= 0:
                        break
                    rem = aml.product_uom_id._compute_quantity(
                        max(aml_remaining(aml), 0.0), line.product_id.uom_id)
                    take = min(remaining_need, rem)
                    if float_compare(take, 0.0, precision_rounding=rounding) <= 0:
                        continue
                    plan[aml] = line.product_id.uom_id._compute_quantity(
                        take, aml.product_uom_id)
                    remaining_need -= take
                if float_compare(remaining_need, 0.0, precision_rounding=rounding) > 0:
                    covered = False
                    break
            if covered:
                breakdown.append(_('Refund allocated to bill %s.') % bill.name)
                return plan, breakdown

        raise UserError(_(
            'The refundable quantity does not fit a single vendor bill of %s. '
            'Select the bill to refund against on the request (the rest will be '
            'deducted from future billing), or split the return into one request '
            'per bill.') % self.purchase_order_id.name)

    def _reverse_bill_partial(self, bill, qty_by_aml):
        """Draft partial reversal of a bill; qty_by_aml maps source bill line
        id -> refund quantity in that line's UoM. Shared by the receipt/bill
        anchored path and the PO-anchored refund engine."""
        self.ensure_one()
        ref = _('Reversal of: %s', bill.name)
        if self.reason:
            ref = _('Reversal of: %(bill)s, %(reason)s', bill=bill.name, reason=self.reason)
        reversal = bill._reverse_moves(default_values_list=[{
            'ref': ref,
            'invoice_date': fields.Date.context_today(self),
            'date': fields.Date.context_today(self),
            'invoice_origin': '%s - %s' % (self.name, bill.name),
        }], cancel=False)

        source_lines = bill.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product').sorted(lambda l: (l.sequence, l.id))
        reversal_lines = reversal.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product').sorted(lambda l: (l.sequence, l.id))
        if len(source_lines) != len(reversal_lines) or any(
                s.product_id != r.product_id for s, r in zip(source_lines, reversal_lines)):
            raise UserError(_(
                'Could not map the credit note lines back to the lines of bill %s.') % bill.name)

        commands = []
        for source, rev in zip(source_lines, reversal_lines):
            wanted = qty_by_aml.get(source.id, 0.0)
            rounding = source.product_uom_id.rounding or source.product_id.uom_id.rounding
            if float_is_zero(wanted, precision_rounding=rounding):
                commands.append(Command.unlink(rev.id))
            elif float_compare(wanted, rev.quantity, precision_rounding=rounding) < 0:
                commands.append(Command.update(rev.id, {'quantity': wanted}))
        if commands:
            reversal.write({'invoice_line_ids': commands})

        self.credit_note_id = reversal.id
        return reversal

    def _vendor_return_chain_open(self):
        """True while the return picking or any of its backorders is neither
        done nor cancelled."""
        self.ensure_one()
        pending = self.return_picking_id
        chain = self.env['stock.picking']
        while pending:
            chain |= pending
            pending = self.env['stock.picking'].search([('backorder_id', 'in', pending.ids)])
        return any(picking.state not in ('done', 'cancel') for picking in chain)

    def _vendor_returned_done_qty(self):
        """Total quantity actually shipped back (done moves of the return
        picking chain), in each product's UoM."""
        self.ensure_one()
        total = 0.0
        pending = self.return_picking_id
        while pending:
            for move in pending.move_ids.filtered(lambda m: m.state == 'done'):
                total += move.product_uom._compute_quantity(move.quantity, move.product_id.uom_id)
            pending = self.env['stock.picking'].search([('backorder_id', 'in', pending.ids)])
        return total


class ReturnRequestLine(models.Model):
    _inherit = 'return.request.line'

    purchase_line_id = fields.Many2one(
        'purchase.order.line',
        string='Purchase Order Line',
        copy=False,
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial',
        copy=False,
        help='Lot/serial this line was received under. Only set for tracked '
             'products; one return line is generated per lot actually received '
             'against the purchase order line.',
    )

    ordered_qty = fields.Float(
        string='Ordered Quantity',
        digits='Product Unit of Measure',
    )

    qty_received_at_location = fields.Float(
        string='Received at Location',
        digits='Product Unit of Measure',
        compute='_compute_qty_received_at_location',
        help='Quantity of this product received through the PO that is currently '
             'at the selected return source location (traced via stock moves).',
    )

    qty_on_hand_at_source = fields.Float(
        string='On Hand at Source',
        digits='Product Unit of Measure',
        compute='_compute_qty_on_hand_at_source',
        help='Available quantity of the product at the selected return source location.',
    )

    @api.depends('product_id', 'return_request_id.return_source_location_id', 'lot_id')
    def _compute_qty_received_at_location(self):
        """Trace stock moves from the PO that landed at the selected location."""
        for line in self:
            location = line.return_request_id.return_source_location_id
            if line.product_id and location and line.purchase_line_id:
                loc_ids = self.env['stock.location'].search(
                    [('id', 'child_of', location.id)]).ids
                moves = line.purchase_line_id.move_ids.filtered(
                    lambda m, _locs=loc_ids: m.state == 'done'
                    and m.location_dest_id.usage == 'internal'
                    and m.location_dest_id.id in _locs
                )
                if line.lot_id:
                    # a single move can carry several lots' move lines --
                    # scope to this line's lot, not the whole move
                    qty = sum(
                        ml.product_uom_id._compute_quantity(ml.quantity, line.product_id.uom_id)
                        for m in moves for ml in m.move_line_ids
                        if ml.lot_id == line.lot_id
                    )
                else:
                    qty = sum(
                        m.product_uom._compute_quantity(m.quantity, line.product_id.uom_id)
                        for m in moves
                    )
                line.qty_received_at_location = qty
            else:
                line.qty_received_at_location = 0.0

    @api.depends('product_id', 'return_request_id.return_source_location_id', 'lot_id')
    def _compute_qty_on_hand_at_source(self):
        Quant = self.env['stock.quant']
        for line in self:
            location = line.return_request_id.return_source_location_id
            if line.product_id and location:
                line.qty_on_hand_at_source = Quant._get_available_quantity(
                    line.product_id, location, lot_id=line.lot_id or None)
            else:
                line.qty_on_hand_at_source = 0.0

    def _get_vendor_base_qty(self):
        """Quantity that can be claimed on this vendor return line, before
        deducting what was already returned.

        For PO-anchored returns the base is capped by the on-hand quantity
        at the selected return source location.
        """
        self.ensure_one()
        if self.purchase_line_id:
            # live POL value: already NET of previously validated returns
            pol = self.purchase_line_id
            received = pol.product_uom_id._compute_quantity(
                max(pol.qty_received, 0.0), self.product_id.uom_id)
            # cap by on-hand at the selected location (scoped to this line's
            # lot when tracked, so different lots of the same product never
            # share the same on-hand pool)
            location = self.return_request_id.return_source_location_id
            if location:
                Quant = self.env['stock.quant']
                on_hand = Quant._get_available_quantity(
                    self.product_id, location, lot_id=self.lot_id or None)
                return min(received, on_hand)
            return received
        request = self.return_request_id
        if request.invoice_id and request.picking_id:
            if self.invoiced_qty and self.delivered_qty:
                return min(self.invoiced_qty, self.delivered_qty)
            return self.invoiced_qty or self.delivered_qty
        if request.invoice_id:
            return self.invoiced_qty
        return self.delivered_qty

    def _get_pol_pending_return_qty(self):
        """Return quantity claimed by OTHER open vendor requests on the same
        purchase order line -- and the same lot when tracked, so two requests
        claiming different lots of the same product never block each other --
        not yet netted out of pol.qty_received (in product UoM, fresh search)."""
        self.ensure_one()
        pol = self.purchase_line_id
        if not pol or not self.product_id:
            return 0.0
        request = self.return_request_id
        other_lines = self.env['return.request.line'].search([
            ('purchase_line_id', '=', pol.id),
            ('lot_id', '=', self.lot_id.id if self.lot_id else False),
            ('return_request_id', '!=', request._origin.id or request.id),
            ('return_request_id.return_operation_type', '=', 'vendor'),
            ('return_request_id.state', 'in', ('submitted', 'approved', 'processing')),
        ])
        pending = 0.0
        for line in other_lines:
            other_request = line.return_request_id
            if other_request.state == 'processing':
                # the validated portion of their return chain is already
                # subtracted from qty_received; only the open remainder pends
                done = other_request._vendor_return_done_qty_for_pol(pol, lot_id=self.lot_id or None)
                pending += max(line.return_qty - done, 0.0)
            else:
                pending += line.return_qty
        return pending

    def _get_vendor_already_returned_qty(self):
        """Return quantity already claimed by OTHER vendor requests sharing
        the same anchor documents (fresh search, never the stored value)."""
        self.ensure_one()
        if self.purchase_line_id:
            return self._get_pol_pending_return_qty()
        request = self.return_request_id
        if not self.product_id or not (request.invoice_id or request.picking_id):
            return 0.0
        domain = [
            ('return_request_id.return_operation_type', '=', 'vendor'),
            ('return_request_id.state', 'not in', ('draft', 'cancelled')),
            ('return_request_id', '!=', request._origin.id or request.id),
            ('product_id', '=', self.product_id.id),
        ]
        anchors = []
        if request.invoice_id:
            anchors.append(('return_request_id.invoice_id', '=', request.invoice_id.id))
        if request.picking_id:
            anchors.append(('return_request_id.picking_id', '=', request.picking_id.id))
        if len(anchors) == 2:
            domain += ['|'] + anchors
        else:
            domain += anchors
        other_lines = self.env['return.request.line'].search(domain)
        return sum(other_lines.mapped('return_qty'))

    @api.depends('product_id', 'return_request_id.partner_id',
                 'return_request_id.return_operation_type',
                 'return_request_id.invoice_id', 'return_request_id.picking_id',
                 'return_request_id.return_source_location_id',
                 'purchase_line_id', 'lot_id')
    def _compute_already_returned_qty(self):
        vendor = self.filtered(lambda l: l.return_request_id.return_operation_type == 'vendor')
        for line in vendor:
            line.already_returned_qty = line._get_vendor_already_returned_qty()
        super(ReturnRequestLine, self - vendor)._compute_already_returned_qty()

    @api.depends('delivered_qty', 'already_returned_qty', 'invoiced_qty',
                 'return_request_id.return_operation_type',
                 'return_request_id.invoice_id', 'return_request_id.picking_id',
                 'return_request_id.return_source_location_id',
                 'purchase_line_id', 'lot_id')
    def _compute_available_qty(self):
        vendor = self.filtered(lambda l: l.return_request_id.return_operation_type == 'vendor')
        for line in vendor:
            line.available_qty = max(line._get_vendor_base_qty() - line.already_returned_qty, 0.0)
        super(ReturnRequestLine, self - vendor)._compute_available_qty()

    @api.constrains('return_qty', 'available_qty')
    def _check_return_qty(self):
        all_vendor = self.filtered(
            lambda l: l.return_request_id.return_operation_type == 'vendor')
        # cancelled/done requests reserve nothing: exempt them so unrelated
        # recomputes never re-validate their (now historical) quantities
        vendor = all_vendor.filtered(
            lambda l: l.return_request_id.state not in ('cancelled', 'done'))
        for line in vendor:
            rounding = line.product_id.uom_id.rounding or 0.01
            # recompute fresh: the stored already_returned_qty can be stale
            available = line._get_vendor_base_qty() - line._get_vendor_already_returned_qty()
            if float_compare(line.return_qty, available, precision_rounding=rounding) > 0:
                raise ValidationError(_(
                    'Return quantity for %(product)s exceeds the quantity available '
                    'to return (%(qty)s).',
                    product=line.product_id.display_name, qty=available))
        super(ReturnRequestLine, self - all_vendor)._check_return_qty()

    @api.constrains('return_qty', 'product_id')
    def _check_serial_return_qty(self):
        # no serial-tracked purchased products exist today, but a serial unit
        # is inherently indivisible -- guard against a future one silently
        # allowing a fractional/multi-unit return on a single serial line
        for line in self:
            if line.product_id.tracking == 'serial' and float_compare(
                    line.return_qty, 1.0, precision_rounding=line.product_id.uom_id.rounding) > 0:
                raise ValidationError(_(
                    'Return quantity for serial-tracked %s must be 0 or 1 per line.'
                ) % line.product_id.display_name)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    return_request_ids = fields.One2many(
        'return.request',
        'purchase_order_id',
        string='Return Requests',
    )

    return_request_count = fields.Integer(
        string='Return Request Count',
        compute='_compute_return_request_count',
    )

    @api.depends('return_request_ids')
    def _compute_return_request_count(self):
        for order in self:
            order.return_request_count = len(order.return_request_ids)

    def action_view_return_requests(self):
        """View vendor return requests anchored on this purchase order"""
        action = self.env.ref('as_return_management.action_vendor_return').read()[0]
        if len(self.return_request_ids) > 1:
            action['domain'] = [('id', 'in', self.return_request_ids.ids)]
        elif self.return_request_ids:
            action['views'] = [(self.env.ref('as_return_management.view_vendor_return_form').id, 'form')]
            action['res_id'] = self.return_request_ids.id
        return action


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _action_done(self):
        res = super()._action_done()
        done = self.filtered(lambda p: p.state == 'done')
        if not done:
            return res
        # climb to the root of the backorder chain so validating a backorder
        # also resolves to the return picking linked on the request
        roots = set()
        for picking in done:
            while picking.backorder_id:
                picking = picking.backorder_id
            roots.add(picking.id)
        requests = self.env['return.request'].sudo().search([
            ('return_picking_id', 'in', list(roots)),
            ('return_operation_type', '=', 'vendor'),
            ('state', '=', 'processing'),
        ])
        for request in requests:
            if request._vendor_return_chain_open():
                continue
            request.action_done()
            requested = sum(request.return_line_ids.filtered(
                lambda l: not float_is_zero(l.delivered_qty, precision_rounding=l.product_id.uom_id.rounding)
            ).mapped('return_qty'))
            returned = request._vendor_returned_done_qty()
            if float_compare(returned, requested, precision_rounding=0.0001) < 0:
                request.message_post(body=_(
                    'Only %(returned)s of the requested %(requested)s units were shipped back '
                    'to the vendor. Please adjust the draft vendor credit note %(credit_note)s '
                    'before posting it.',
                    returned=returned, requested=requested,
                    credit_note=request.credit_note_id.display_name or '-'))
        return res
