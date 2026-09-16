import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class MrpProductionIntercompanyLink(models.Model):
    """Tracks one intercompany component supply: Company A's manufacturing
    order (`parent_production_id`) needs a component flagged as produced by
    another company, so this module raised an intercompany purchase order
    (mirrored by core `sale_purchase_inter_company_rules` into a sales order
    in the producing company) and, once that sale order is confirmed and the
    producing company can't fulfill it from stock alone, a manufacturing
    order there (`child_production_id`).

    Only meaningful for same-database multi-company setups: `child_company_id`
    is another company row in THIS database, and `child_production_id` is a
    `mrp.production` record this module reads/writes directly (via sudo() /
    with_company()) across the company boundary. There is no cross-instance
    sync of any kind.
    """
    _name = 'mrp.production.intercompany.link'
    _description = 'Manufacturing Intercompany Supply Link'
    _order = 'create_date desc'
    _rec_name = 'product_id'

    parent_production_id = fields.Many2one(
        'mrp.production', string='Parent Manufacturing Order',
        required=True, ondelete='cascade', index=True,
        help="The Company A manufacturing order that needs this component.")
    child_production_id = fields.Many2one(
        'mrp.production', string='Child Manufacturing Order',
        help="The Company B manufacturing order that will produce this "
             "component. Left empty until the supplying company's sales "
             "order is confirmed and manufacturing there turns out to be "
             "necessary (stock alone isn't enough).")
    parent_company_id = fields.Many2one(
        'res.company', string='Requesting Company', required=True)
    child_company_id = fields.Many2one(
        'res.company', string='Supplying Company', required=True)
    product_id = fields.Many2one(
        'product.product', string='Component', required=True)
    product_qty = fields.Float(string='Quantity', default=0.0)
    sale_order_id = fields.Many2one(
        'sale.order', string='Intercompany Sales Order',
        help="The sales order core `sale_purchase_inter_company_rules` is "
             "expected to auto-generate in the supplying company when "
             "`purchase_order_id` is confirmed. Left empty until this "
             "module can find it (best-effort match, see module "
             "CHANGELOG.md) -- a scheduled job or the Retry button pick it "
             "up once it exists.")
    purchase_order_id = fields.Many2one(
        'purchase.order', string='Intercompany Purchase Order')
    state = fields.Selection([
        ('po_created', 'Purchase Order Created'),
        ('so_confirmed', 'Sales Order Confirmed'),
        ('mo_created', 'Child MO Created'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ], string='Status', default='po_created', required=True, index=True)

    progress_percentage = fields.Float(
        string='Progress %', compute='_compute_progress_percentage')
    has_due_date_exception = fields.Boolean(
        string='Due-Date Exception', compute='_compute_due_date_exception',
        store=True)
    exception_message = fields.Char(
        string='Exception Message', compute='_compute_due_date_exception',
        store=True)
    status_display = fields.Char(
        string='Status', compute='_compute_status_display')

    @api.depends(
        'product_qty',
        'child_production_id.qty_produced',
        'child_production_id.product_qty',
        'child_production_id.workorder_ids.duration',
        'child_production_id.workorder_ids.duration_expected',
    )
    def _compute_progress_percentage(self):
        """Progress formula (no native Community `mrp.production` "percent
        complete" field exists to read from, see CHANGELOG.md):
        1. If `product_qty` is known: `qty_produced / product_qty * 100`,
           read off the child production (sudo, cross-company).
        2. Else, if the child production has work orders: ratio of actual
           `duration` logged to `duration_expected` across its work orders,
           as a rough stand-in for physical progress.
        3. Else: 0.
        Capped at 100 either way.
        """
        for link in self:
            child = link.child_production_id.sudo()
            if not child:
                link.progress_percentage = 0.0
                continue
            qty = link.product_qty or child.product_qty
            if qty:
                link.progress_percentage = min(
                    100.0, (child.qty_produced / qty) * 100.0)
                continue
            workorders = child.workorder_ids
            expected = sum(workorders.mapped('duration_expected'))
            if expected:
                done = sum(workorders.mapped('duration'))
                link.progress_percentage = min(100.0, (done / expected) * 100.0)
            else:
                link.progress_percentage = 0.0

    @api.depends(
        'child_production_id.date_finished',
        'parent_production_id.date_deadline',
        'parent_production_id.date_start',
        'child_production_id',
    )
    def _compute_due_date_exception(self):
        """Reference "needed by" date on the parent: `date_deadline` (the
        customer/commitment date) when set, since that's the more
        semantically correct "must have this component by" date, falling
        back to `date_start` (when the parent MO itself is planned
        to start, i.e. when it would consume the component) when no
        deadline is set. See CHANGELOG.md for this choice.

        `date_finished` on `mrp.production` matches the field name
        this repo's own `mrp_finite_capacity_scheduler` module already
        assumed for the Odoo 17 target -- kept consistent with that.
        """
        for link in self:
            child = link.child_production_id.sudo()
            parent = link.parent_production_id
            needed_by = parent.date_deadline or parent.date_start
            if not child or not child.date_finished or not needed_by:
                link.has_due_date_exception = False
                link.exception_message = False
                continue
            if child.date_finished > needed_by:
                days_late = max((child.date_finished - needed_by).days, 1)
                link.has_due_date_exception = True
                link.exception_message = _(
                    "%(child)s (%(company)s) is forecast to finish %(days)s "
                    "day(s) after %(parent)s needs this component. Action "
                    "may be required to avoid delaying the parent order.",
                    child=child.name or _('the child MO'),
                    company=link.child_company_id.name or '',
                    days=days_late,
                    parent=parent.name or _('the parent MO'),
                )
            else:
                link.has_due_date_exception = False
                link.exception_message = False

    @api.depends('state', 'progress_percentage', 'child_company_id')
    def _compute_status_display(self):
        for link in self:
            company_name = link.child_company_id.name or _('the supplying company')
            if link.state == 'failed':
                link.status_display = _(
                    "Intercompany supply failed -- see chatter, then Retry.")
            elif link.state == 'po_created':
                link.status_display = _(
                    "Waiting on %s -- purchase order created", company_name)
            elif link.state == 'so_confirmed':
                link.status_display = _(
                    "Waiting on %s -- sales order confirmed, manufacturing "
                    "not started yet", company_name)
            elif link.state == 'mo_created':
                link.status_display = _(
                    "Waiting on %(company)s -- %(pct)s%% complete",
                    company=company_name, pct=int(link.progress_percentage))
            elif link.state == 'done':
                link.status_display = _("Supplied by %s -- complete", company_name)
            else:
                link.status_display = _("Unknown status")

    def action_view_child_production(self):
        self.ensure_one()
        if not self.child_production_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Manufacturing Order'),
            'res_model': 'mrp.production',
            'view_mode': 'form',
            'res_id': self.child_production_id.id,
            'target': 'current',
            'context': {'allowed_company_ids': [self.child_company_id.id]},
        }

    def action_retry(self):
        """Manual re-attempt of whatever step is currently stuck: look for
        the mirrored sales order if not found yet, create the child
        production if the sales order is confirmed and it's missing, or
        mark the link done if the child production already finished.
        Never raises -- logs and flips the link to 'failed' instead, so a
        bad retry does not disrupt anything else on the form.
        """
        for link in self:
            try:
                if link.state == 'failed' and link.purchase_order_id:
                    link.state = 'po_created'
                if not link.sale_order_id:
                    link._find_matching_sale_order()
                if (link.sale_order_id
                        and link.sale_order_id.sudo().state == 'sale'
                        and not link.child_production_id):
                    link._create_child_production()
                if (link.child_production_id
                        and link.child_production_id.sudo().state == 'done'):
                    link.state = 'done'
            except Exception:
                _logger.warning(
                    "mrp_intercompany_wo_sync: retry failed for link %s",
                    link.id, exc_info=True)
                link.state = 'failed'
        return True

    def _find_matching_sale_order(self):
        """Best-effort discovery of the sales order core
        `sale_purchase_inter_company_rules` is expected to auto-generate in
        the supplying company when `purchase_order_id` is confirmed.

        UNVERIFIED: no vendored copy of core `sale_purchase_inter_company_rules`
        source was available in this environment to confirm the exact field
        that links a generated PO back to its mirrored SO (candidates
        include `origin`/`client_order_ref` carrying the PO name, or a
        dedicated reference field on `res.company`/`sale.order`). This
        searches by the PO's name showing up in the SO's `origin` or
        `client_order_ref`, matched to a sale order in the child company for
        the requesting company's commercial partner. If nothing is found,
        this is a no-op -- the cron or a later Retry will pick it up once
        the sale order exists.
        """
        self.ensure_one()
        if self.sale_order_id or not self.purchase_order_id:
            return
        po = self.purchase_order_id.sudo()
        partner = self.parent_company_id.partner_id.commercial_partner_id
        if not partner:
            return
        SaleOrder = self.env['sale.order'].sudo().with_company(self.child_company_id)
        domain = [
            ('company_id', '=', self.child_company_id.id),
            ('partner_id.commercial_partner_id', '=', partner.id),
            '|',
            ('origin', 'like', po.name),
            ('client_order_ref', 'like', po.name),
        ]
        sale_order = SaleOrder.search(domain, limit=1)
        if not sale_order:
            return
        self.sale_order_id = sale_order.id
        if sale_order.state == 'sale':
            self.state = 'so_confirmed'

    def _child_company_can_fulfill_from_stock(self):
        """Whether the supplying company can deliver `product_qty` of
        `product_id` from its own free stock alone, in which case no child
        manufacturing order is needed -- the intercompany delivery/transfer
        handles it, same as any ordinary intercompany sale."""
        self.ensure_one()
        product = self.product_id.sudo().with_company(self.child_company_id)
        return product.free_qty >= self.product_qty

    def _get_bom_for_product(self, product, company):
        """Best-effort BOM lookup. `mrp.bom._bom_find`'s exact signature has
        changed across Odoo versions and no vendored core `mrp` source was
        available here to confirm the Odoo 17 one precisely, so this call is
        wrapped defensively: any failure just returns False (no BOM set on
        the created production, which core `mrp.production` tolerates -- it
        simply won't auto-populate components)."""
        try:
            result = self.env['mrp.bom'].sudo()._bom_find(
                product, company_id=company.id)
            if isinstance(result, dict):
                return result.get(product) or False
            return result or False
        except Exception:
            _logger.warning(
                "mrp_intercompany_wo_sync: BOM lookup failed for %s in %s",
                product.display_name, company.display_name, exc_info=True)
            return False

    def _create_child_production(self):
        """Create the Company B manufacturing order for this link, once its
        sales order is confirmed and stock alone can't cover it. Called by
        the cron and by `action_retry()`."""
        self.ensure_one()
        if self.child_production_id or not self.child_company_id:
            return
        product = self.product_id.sudo()
        child_company = self.child_company_id
        bom = self._get_bom_for_product(product, child_company)
        vals = {
            'product_id': product.id,
            'product_qty': self.product_qty,
            'product_uom_id': product.uom_id.id,
            'company_id': child_company.id,
            'origin': self.purchase_order_id.name or self.parent_production_id.name,
        }
        if bom:
            vals['bom_id'] = bom.id
        production = self.env['mrp.production'].sudo().with_company(
            child_company).create(vals)
        try:
            production.action_confirm()
        except Exception:
            _logger.warning(
                "mrp_intercompany_wo_sync: could not auto-confirm child "
                "production %s", production.name, exc_info=True)
        self.child_production_id = production.id
        self.state = 'mo_created'

    @api.model
    def _cron_sync_intercompany_links(self):
        """Scheduled sync (see data/ir_cron_data.xml): for every open link
        (not yet 'done' or 'failed'), try to advance it one step, and
        refresh the due-date-exception / progress fields for all of them.
        Never lets one link's failure stop the others."""
        links = self.sudo().search([('state', 'not in', ('done', 'failed'))])
        for link in links:
            try:
                if not link.sale_order_id:
                    link._find_matching_sale_order()
                if (link.sale_order_id
                        and link.sale_order_id.sudo().state == 'sale'
                        and not link.child_production_id):
                    if not link._child_company_can_fulfill_from_stock():
                        bom = link._get_bom_for_product(
                            link.product_id.sudo(), link.child_company_id)
                        if bom:
                            link._create_child_production()
                if (link.child_production_id
                        and link.child_production_id.sudo().state == 'done'):
                    link.state = 'done'
            except Exception:
                _logger.warning(
                    "mrp_intercompany_wo_sync: cron sync failed for link %s",
                    link.id, exc_info=True)
        # Explicit recompute pass per spec, even though the store=True
        # due-date fields already recompute on the underlying field writes
        # above -- this also catches drift on links this run did not touch
        # (e.g. the child production's schedule slipped from elsewhere).
        open_links = self.sudo().search([('state', 'not in', ('done', 'failed'))])
        open_links._compute_progress_percentage()
        open_links._compute_due_date_exception()
        return True
