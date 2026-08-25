import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)

# States from which the order may be cancelled, per the architecture doc §1.
CANCELLABLE_STATES = ('draft', 'estimate', 'approved')


class AutomotiveRepairOrder(models.Model):
    _name = 'automotive.repair.order'
    _description = 'Repair Order (Job Card)'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'automotive.deletion.request.mixin']
    _order = 'id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True)

    vehicle_id = fields.Many2one(
        'automotive.vehicle', string='Vehicle', required=True, tracking=True,
        index=True,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Customer', related='vehicle_id.partner_id',
        store=True, readonly=True,
    )
    order_type = fields.Selection([
        ('standard', 'Standard'),
        ('warranty_claim', 'Warranty Claim'),
    ], default='standard', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('estimate', 'Estimate'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('quality_check', 'Quality Check'),
        ('ready', 'Ready'),
        ('invoiced', 'Invoiced'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, tracking=True, copy=False)

    lead_technician_id = fields.Many2one(
        'hr.employee', string='Lead Technician', tracking=True,
    )
    mileage_in = fields.Integer(string='Mileage In')
    customer_complaint = fields.Text()
    diagnosis_notes = fields.Text()

    actual_start_datetime = fields.Datetime(readonly=True, copy=False)
    actual_end_datetime = fields.Datetime(readonly=True, copy=False)
    expected_pickup_datetime = fields.Datetime(readonly=True, copy=False)

    workshop_resource_ids = fields.Many2many(
        'automotive.workshop.resource', string='Workshop Bays/Lifts',
        help='Which bay(s)/lift(s) this job uses. Drives the capacity-based '
             'pickup estimate in §5 of the architecture doc: backlog is '
             'compared only against other orders sharing at least one of '
             'these resources.',
    )

    labor_ids = fields.One2many(
        'automotive.repair.order.labor', 'order_id', string='Labor Lines',
    )
    part_ids = fields.One2many(
        'automotive.repair.order.part', 'order_id', string='Part Lines',
    )

    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True,
    )
    currency_id = fields.Many2one(related='company_id.currency_id')

    subtotal = fields.Monetary(compute='_compute_subtotal', store=True)
    discount_input_mode = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed_price', 'Fixed Price'),
    ], default='percentage', required=True)
    discount_percent = fields.Float(string='Discount %', default=0.0)
    final_price = fields.Monetary(string='Final Price')

    salesperson_id = fields.Many2one(
        'res.users', string='Salesperson', default=lambda self: self.env.user,
        tracking=True,
    )

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True, copy=False)
    picking_id = fields.Many2one('stock.picking', string='Parts Transfer', readonly=True, copy=False)

    inspection_ids = fields.One2many(
        'automotive.vehicle.inspection', 'repair_order_id', string='Inspections',
    )
    checkin_id = fields.Many2one(
        'automotive.vehicle.inspection', string='Check-in', compute='_compute_checkin_checkout',
        store=True,
    )
    checkout_id = fields.Many2one(
        'automotive.vehicle.inspection', string='Check-out', compute='_compute_checkin_checkout',
        store=True,
    )

    history_id = fields.Many2one('automotive.vehicle.history', readonly=True, copy=False)
    warranty_claim_id = fields.Many2one(
        'automotive.warranty.claim', string='Originating Warranty Claim',
        copy=False, tracking=True,
        help='The approved warranty claim this order resolves (§6). Picked '
             'by the user — usually via the "Create Repair Order" button on '
             'the claim — not generated automatically.',
    )

    @api.depends('labor_ids.subtotal', 'part_ids.subtotal')
    def _compute_subtotal(self):
        for order in self:
            order.subtotal = sum(order.labor_ids.mapped('subtotal')) + sum(order.part_ids.mapped('subtotal'))

    @api.depends('inspection_ids.inspection_type')
    def _compute_checkin_checkout(self):
        for order in self:
            order.checkin_id = order.inspection_ids.filtered(lambda i: i.inspection_type == 'checkin')[:1]
            order.checkout_id = order.inspection_ids.filtered(lambda i: i.inspection_type == 'checkout')[:1]

    # ------------------------------------------------------------------
    # CRUD — pricing recompute + discount cap enforcement
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('automotive.repair.order') or _('New')
        orders = super().create(vals_list)
        for order, vals in zip(orders, vals_list):
            order._apply_pricing_rules(final_price_explicit='final_price' in vals)
        orders._sync_warranty_claim_resolution()
        return orders

    def write(self, vals):
        track_scope_change = bool(vals.get('labor_ids') or vals.get('part_ids'))
        baseline = {}
        if track_scope_change:
            baseline = {
                order.id: (set(order.labor_ids.ids), set(order.part_ids.ids)) for order in self
            }
        res = super().write(vals)
        self._apply_pricing_rules(final_price_explicit='final_price' in vals)
        if 'warranty_claim_id' in vals:
            self._sync_warranty_claim_resolution()
        if track_scope_change:
            for order in self:
                if order.state not in ('approved', 'in_progress', 'quality_check'):
                    continue
                old_labor_ids, old_part_ids = baseline.get(order.id, (set(), set()))
                new_labor = order.labor_ids.filtered(lambda l: l.id not in old_labor_ids)
                new_parts = order.part_ids.filtered(lambda p: p.id not in old_part_ids)
                if new_labor or new_parts:
                    order._compute_expected_pickup_datetime()
                    order._send_scope_change_email(new_labor, new_parts)
        return res

    def _apply_pricing_rules(self, final_price_explicit=False):
        """Recompute whichever of discount_percent/final_price is derived
        from the other (per discount_input_mode), then enforce the acting
        salesperson's discount cap. Runs from create()/write() — not just
        onchange — so the cap holds for API calls, imports and server
        actions, not only the web client (§4).

        In fixed_price mode, final_price is only treated as the source of
        truth when the caller actually wrote a new final_price this call
        (final_price_explicit=True — a genuine user price edit). When
        subtotal moved instead because labor/part lines changed (the caller
        didn't touch final_price), the old fixed price would otherwise stay
        frozen against a bigger subtotal and its implied discount % would
        balloon past the cap — so in that case the last known discount % is
        kept fixed and final_price is rescaled from it instead, same as
        percentage mode."""
        for order in self:
            subtotal = order.subtotal
            if order.discount_input_mode == 'percentage':
                new_final_price = subtotal * (1 - order.discount_percent / 100.0)
                new_discount_percent = order.discount_percent
            elif final_price_explicit:
                new_discount_percent = (
                    (subtotal - order.final_price) / subtotal * 100.0
                ) if subtotal else 0.0
                new_final_price = order.final_price
            else:
                new_discount_percent = order.discount_percent
                new_final_price = subtotal * (1 - order.discount_percent / 100.0)

            derived_vals = {}
            if not float_is_zero(new_final_price - order.final_price, precision_digits=2):
                derived_vals['final_price'] = new_final_price
            if not float_is_zero(new_discount_percent - order.discount_percent, precision_digits=4):
                derived_vals['discount_percent'] = new_discount_percent
            if derived_vals:
                # bypass our own write() override — this is the derived-field
                # sync, not a user edit, so it must not re-trigger this method
                super(AutomotiveRepairOrder, order).write(derived_vals)

            effective_discount = derived_vals.get('discount_percent', order.discount_percent)
            salesperson = order.salesperson_id or self.env.user
            cap = salesperson.max_discount_percent
            if effective_discount - cap > 0.01:
                raise ValidationError(_(
                    'The discount of %(discount).2f%% on repair order %(order)s exceeds '
                    "%(salesperson)s's maximum allowed discount of %(cap).2f%%."
                ) % {
                    'discount': effective_discount,
                    'order': order.name,
                    'salesperson': salesperson.name,
                    'cap': cap,
                })

    @api.onchange('warranty_claim_id')
    def _onchange_warranty_claim_id(self):
        if self.warranty_claim_id:
            claim = self.warranty_claim_id
            self.order_type = 'warranty_claim'
            self.vehicle_id = claim.vehicle_id
            self.customer_complaint = claim.issue_description
            self.salesperson_id = claim.origin_repair_order_id.salesperson_id

    @api.constrains('warranty_claim_id', 'vehicle_id')
    def _check_warranty_claim_id(self):
        for order in self:
            claim = order.warranty_claim_id
            if not claim:
                continue
            if claim.state != 'approved':
                raise ValidationError(_(
                    'Warranty claim %s must be approved before a repair order can be '
                    'created against it.'
                ) % claim.name)
            if claim.resolution_repair_order_id and claim.resolution_repair_order_id != order:
                raise ValidationError(_(
                    'Warranty claim %s already has a resolution repair order (%s).'
                ) % (claim.name, claim.resolution_repair_order_id.name))
            if order.vehicle_id != claim.vehicle_id:
                raise ValidationError(_(
                    'Repair order for warranty claim %s must be for the same vehicle as '
                    'the claim (%s).'
                ) % (claim.name, claim.vehicle_id.display_name))

    def _sync_warranty_claim_resolution(self):
        for order in self:
            if order.warranty_claim_id and order.warranty_claim_id.resolution_repair_order_id != order:
                order.warranty_claim_id.resolution_repair_order_id = order.id

    @api.onchange('discount_percent', 'discount_input_mode', 'subtotal')
    def _onchange_discount_percent(self):
        if self.discount_input_mode == 'percentage':
            self.final_price = self.subtotal * (1 - self.discount_percent / 100.0)

    @api.onchange('final_price', 'discount_input_mode', 'subtotal')
    def _onchange_final_price(self):
        if self.discount_input_mode == 'fixed_price' and self.subtotal:
            self.discount_percent = (self.subtotal - self.final_price) / self.subtotal * 100.0

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _check_transition(self, allowed_states):
        for order in self:
            if order.state not in allowed_states:
                raise UserError(_(
                    'Cannot perform this action on repair order %(order)s from state %(state)s.'
                ) % {'order': order.name, 'state': order.state})

    def action_confirm_estimate(self):
        self._check_transition(('draft',))
        for order in self:
            if not order.partner_id.phone:
                raise ValidationError(_(
                    'Customer %s must have a phone number on file before the order can leave Draft.'
                ) % order.partner_id.display_name)
            if not (order.partner_id.street and order.partner_id.city):
                raise ValidationError(_(
                    'Customer %s must have an address on file before the order can leave Draft.'
                ) % order.partner_id.display_name)
            if not order.partner_id.email:
                raise ValidationError(_(
                    'Customer %s must have an email on file before the order can leave Draft — '
                    'it is used to send repair status updates.'
                ) % order.partner_id.display_name)
        self.write({'state': 'estimate'})

    def action_approve(self):
        """Approval locks in the negotiated price (discount_percent/
        final_price stop changing once the caller isn't recomputing
        subtotal-driven scope changes the same way) — gated to
        Salesperson+ so a Technician can't unilaterally approve their own
        estimate, matching the discount-cap-by-salesperson design elsewhere
        in this model."""
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_salesperson'):
            raise UserError(_('Only a Shop Salesperson or Manager can approve a repair order.'))
        self._check_transition(('estimate',))
        self.write({'state': 'approved'})
        for order in self:
            order._compute_expected_pickup_datetime()
            order._send_approved_email()

    def action_recalculate_pickup(self):
        """Manager-triggered manual recalculation, per §5/§10."""
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager'):
            raise UserError(_('Only a Shop Manager can recalculate the pickup estimate.'))
        for order in self:
            order._compute_expected_pickup_datetime()

    def action_start(self):
        self._check_transition(('approved',))
        for order in self:
            if not order.checkin_id:
                raise UserError(_(
                    'Cannot start work on repair order %s — a check-in inspection '
                    'must be recorded first.'
                ) % order.name)
        self.write({
            'state': 'in_progress',
            'actual_start_datetime': fields.Datetime.now(),
        })
        for order in self:
            order._consume_parts()

    def action_quality_check(self):
        self._check_transition(('in_progress',))
        self.write({'state': 'quality_check'})

    def action_ready(self):
        self._check_transition(('quality_check',))
        self.write({
            'state': 'ready',
            'actual_end_datetime': fields.Datetime.now(),
        })

    def action_invoice(self):
        """Invoicing creates real financial documents (sale.order,
        account.move) — gated to Salesperson+ for the same segregation-of-
        duties reason as action_approve()."""
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_salesperson'):
            raise UserError(_('Only a Shop Salesperson or Manager can invoice a repair order.'))
        self._check_transition(('ready',))
        for order in self:
            invoices = order._create_sale_invoice()
            order._send_invoice_email(invoices)
        self.write({'state': 'invoiced'})

    def action_close(self):
        """Closing is gated on the invoice actually being paid (ii): if it
        isn't, redirect the user to the invoice instead of closing, rather
        than silently blocking with just an error. Also requires a check-out
        inspection on file — the vehicle must have actually been handed back
        before the job can be considered closed."""
        self._check_transition(('invoiced',))
        for order in self:
            if not order.checkout_id:
                raise UserError(_(
                    'Cannot close repair order %s — a check-out inspection '
                    'must be recorded first.'
                ) % order.name)
        for order in self:
            invoice = order.sale_order_id.invoice_ids[:1]
            if invoice and invoice.payment_state not in ('paid', 'in_payment'):
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Unpaid Invoice — process payment before closing'),
                    'res_model': 'account.move',
                    'view_mode': 'form',
                    'res_id': invoice.id,
                    'target': 'current',
                }
        for order in self:
            order._create_vehicle_history()
            order._send_closed_email()
        self.write({'state': 'closed'})

    def action_cancel(self):
        self._check_transition(CANCELLABLE_STATES)
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self._check_transition(('cancelled',))
        self.write({'state': 'draft'})

    # ------------------------------------------------------------------
    # §5 — capacity-based expected pickup time
    # ------------------------------------------------------------------

    def _get_pickup_timezone(self):
        """The workshop's own operating timezone — used to render
        expected_pickup_datetime in emails/chatter so it matches the shop's
        physical clock, rather than falling back to UTC whenever the acting
        user's res.users.tz happens to be unset."""
        self.ensure_one()
        calendar = self.workshop_resource_ids[:1].resource_calendar_id or self.company_id.resource_calendar_id
        return calendar.tz if calendar else False

    def _get_planning_anchor(self):
        """The earliest moment work on this order can actually start: 'now',
        or later if a technician's labor line isn't scheduled (work_date)
        until a future day — otherwise the capacity-based estimate below
        could land before the technician has even started the job."""
        self.ensure_one()
        now = fields.Datetime.now()
        work_dates = self.labor_ids.mapped('work_date')
        latest_work_date = max(work_dates) if work_dates else False
        if latest_work_date and latest_work_date > now.date():
            return fields.Datetime.to_datetime(latest_work_date)
        return now

    def _compute_expected_pickup_datetime(self):
        # Fetched once for the whole batch rather than once per order — a
        # bulk operation touching many orders at once (e.g. a resource
        # reassignment) would otherwise re-run this same open-orders search
        # for every single order in self.
        all_open_orders = self.search([
            ('state', 'in', ('draft', 'estimate', 'approved', 'in_progress')),
        ])
        for order in self:
            resources = order.workshop_resource_ids or self.env['automotive.workshop.resource'].search([])
            calendar = (order.workshop_resource_ids[:1].resource_calendar_id
                        or self.env.company.resource_calendar_id)
            if not calendar:
                _logger.warning(
                    'No resource.calendar available to plan pickup time for order %s.', order.name)
                continue

            this_job_hours = sum(order.labor_ids.mapped('hours'))

            relevant_resource_ids = set(order.workshop_resource_ids.ids or resources.ids)
            other_orders = all_open_orders.filtered(
                lambda o, order=order: o.id != order.id
                and set(o.workshop_resource_ids.ids) & relevant_resource_ids
            )
            backlog_hours = sum(other._remaining_labor_hours() for other in other_orders)

            available_capacity = sum(
                (order.workshop_resource_ids or resources).mapped('concurrent_capacity')
            )
            queue_wait_hours = (backlog_hours / available_capacity) if available_capacity else 0.0

            total_hours_needed = queue_wait_hours + this_job_hours
            pickup = calendar.plan_hours(
                total_hours_needed, order._get_planning_anchor(), compute_leaves=True,
            )
            order.expected_pickup_datetime = pickup or False

    def _remaining_labor_hours(self):
        """Planned hours still outstanding for this order, used as the
        'backlog' contribution in §5's queue-wait computation. For an
        in_progress order, hours already worked (derived from elapsed
        working time since actual_start_datetime, not a separate timesheet
        field — see the build plan's gap-filling note) are subtracted."""
        self.ensure_one()
        planned_hours = sum(self.labor_ids.mapped('hours'))
        if self.state != 'in_progress' or not self.actual_start_datetime:
            return planned_hours
        calendar = self.workshop_resource_ids[:1].resource_calendar_id or self.env.company.resource_calendar_id
        if not calendar:
            return planned_hours
        elapsed_data = calendar.get_work_duration_data(
            self.actual_start_datetime, fields.Datetime.now(), compute_leaves=True,
        )
        elapsed_hours = elapsed_data.get('hours', 0.0)
        return max(0.0, planned_hours - elapsed_hours)

    # ------------------------------------------------------------------
    # Parts consumption (real stock moves, §2/§ build step 3)
    # ------------------------------------------------------------------

    def _consume_parts(self):
        self.ensure_one()
        moves = self.part_ids.mapped('stock_move_id').filtered(lambda m: m.state not in ('done', 'cancel'))
        if not moves:
            return
        moves._action_confirm()
        moves._action_assign()
        for move in moves:
            move._set_quantity_done(move.product_uom_qty)
        # `picked` only auto-computes True for move lines created fresh under
        # auto_pick_move_lines — lines already materialized by _action_assign's
        # reservation just get their quantity updated, so it never flips.
        # Set it explicitly rather than relying on that context trick.
        moves.move_line_ids.write({'picked': True})
        moves._action_done()
        for line in self.part_ids:
            if line.stock_move_id and not line.lot_id:
                lots = line.stock_move_id.move_line_ids.lot_id
                if lots:
                    line.lot_id = lots[0].id

    # ------------------------------------------------------------------
    # Invoicing / closing
    # ------------------------------------------------------------------

    def _get_invoicing_product(self):
        product = self.env.ref(
            'bs_automotive_repair_management.product_repair_order_service', raise_if_not_found=False,
        )
        if not product or not product.exists() or not product.active:
            raise UserError(_(
                'The "Repair Order Services" invoicing product is missing or archived — '
                'restore it (Sales > Products) before invoicing repair orders.'
            ))
        return product

    def _create_sale_invoice(self):
        self.ensure_one()
        if not self.sale_order_id:
            self.sale_order_id = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'order_line': [(0, 0, {
                    'product_id': self._get_invoicing_product().id,
                    'name': _('Repair Order %s — Labor & Parts') % self.name,
                    'product_uom_qty': 1,
                    'price_unit': self.final_price,
                })],
            })
        self.sale_order_id.action_confirm()
        invoices = self.sale_order_id._create_invoices()
        invoices.action_post()
        return invoices

    # ------------------------------------------------------------------
    # Customer notification emails (i) — each posts to the chatter via a
    # mail.template and is a no-op if the customer has no email, though
    # intake validation (action_confirm_estimate) already requires one.
    # ------------------------------------------------------------------

    def _send_approved_email(self):
        self.ensure_one()
        if not self.partner_id.email:
            return
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_ro_approved',
            subtype_xmlid='mail.mt_comment',
        )

    def _send_scope_change_email(self, new_labor, new_parts):
        self.ensure_one()
        if not self.partner_id.email:
            return
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_ro_scope_change',
            subtype_xmlid='mail.mt_comment',
            render_values={'new_labor_lines': new_labor, 'new_part_lines': new_parts},
        )

    def _send_invoice_email(self, invoices):
        self.ensure_one()
        if not self.partner_id.email:
            return
        attachment_ids = []
        if invoices:
            pdf_content, _report_type = self.env['ir.actions.report']._render_qweb_pdf(
                'account.account_invoices', invoices.ids,
            )
            attachment = self.env['ir.attachment'].create({
                'name': f'{invoices[0].name or self.name}.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf',
            })
            attachment_ids = [attachment.id]
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_ro_invoiced',
            subtype_xmlid='mail.mt_comment',
            attachment_ids=[(6, 0, attachment_ids)],
        )

    def _send_closed_email(self):
        self.ensure_one()
        if not self.partner_id.email:
            return
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_ro_closed',
            subtype_xmlid='mail.mt_comment',
        )

    def _create_vehicle_history(self):
        """automotive.vehicle.history is a system-generated service log, not
        user-authored content — Technicians/Salespersons have no create
        access to it (ir.model.access.csv) since it's only meant to be
        edited directly by Managers. action_close() has no group
        restriction of its own, though, so any role that reaches the
        'invoiced' state needs this write to succeed; sudo() here is
        narrowly scoped to this one log-record creation, not a blanket
        bypass."""
        self.ensure_one()
        if self.history_id:
            return
        self.history_id = self.env['automotive.vehicle.history'].sudo().create({
            'vehicle_id': self.vehicle_id.id,
            'repair_order_id': self.id,
            'date': fields.Date.context_today(self),
            'summary': _('%(order_type)s — %(complaint)s') % {
                'order_type': dict(self._fields['order_type'].selection).get(self.order_type),
                'complaint': self.customer_complaint or '',
            },
            'total_amount': self.final_price,
        })
