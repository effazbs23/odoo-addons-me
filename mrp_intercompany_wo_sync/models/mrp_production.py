import logging

from odoo import _, api, fields, models
from odoo.tools import float_compare

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    intercompany_link_ids = fields.One2many(
        'mrp.production.intercompany.link', 'parent_production_id',
        string='Intercompany Supply Links',
        help="Intercompany component-supply links where this manufacturing "
             "order is the requesting (Company A) side.")
    as_child_intercompany_link_id = fields.Many2one(
        'mrp.production.intercompany.link',
        string='Supplied Via Intercompany Link',
        compute='_compute_as_child_intercompany_link',
        help="Set when this manufacturing order itself exists because "
             "another company's manufacturing order needed this product as "
             "a component (i.e. this production is the 'child' side of an "
             "intercompany supply link).")
    has_intercompany_supply = fields.Boolean(
        string='Needs Intercompany Supply Check',
        compute='_compute_has_intercompany_supply',
        help="True when at least one raw material on this order is flagged "
             "as produced by another company. Drives visibility of the "
             "'Check Intercompany Supply' button.")
    intercompany_status_display = fields.Char(
        string='Intercompany Supply Status',
        compute='_compute_intercompany_status_display')
    has_intercompany_due_date_exception = fields.Boolean(
        string='Has Intercompany Due-Date Exception',
        compute='_compute_intercompany_due_date_exception')
    intercompany_exception_message = fields.Char(
        string='Intercompany Exception Message',
        compute='_compute_intercompany_due_date_exception')

    @api.depends('intercompany_link_ids.child_production_id')
    def _compute_as_child_intercompany_link(self):
        Link = self.env['mrp.production.intercompany.link'].sudo()
        for production in self:
            production.as_child_intercompany_link_id = Link.search([
                ('child_production_id', '=', production.id),
            ], limit=1)

    @api.depends(
        'move_raw_ids.product_id',
        'move_raw_ids.product_uom_qty',
        'company_id',
    )
    def _compute_has_intercompany_supply(self):
        for production in self:
            production.has_intercompany_supply = bool(
                production._get_intercompany_shortage_moves())

    @api.depends('intercompany_link_ids.status_display', 'intercompany_link_ids.state')
    def _compute_intercompany_status_display(self):
        for production in self:
            links = production.intercompany_link_ids
            open_links = links.filtered(lambda l: l.state != 'done')
            link = open_links[:1] or links[:1]
            production.intercompany_status_display = link.status_display if link else False

    @api.depends(
        'intercompany_link_ids.has_due_date_exception',
        'intercompany_link_ids.exception_message',
    )
    def _compute_intercompany_due_date_exception(self):
        for production in self:
            exceptions = production.intercompany_link_ids.filtered('has_due_date_exception')
            production.has_intercompany_due_date_exception = bool(exceptions)
            production.intercompany_exception_message = (
                '\n'.join(exceptions.mapped('exception_message')) if exceptions else False
            )

    def _get_intercompany_shortage_moves(self):
        """Raw-material moves whose product is flagged as produced by
        another company and whose demand exceeds that other company's...
        no -- exceeds THIS company's own free-to-use quantity. Shortage is
        determined by comparing the move's demand (`product_uom_qty`)
        against the product's company-wide `free_qty` -- a deliberate
        simplification that does not scope to the move's specific
        warehouse/location; see CHANGELOG.md.
        """
        self.ensure_one()
        shortage_moves = self.env['stock.move']
        for move in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            product = move.product_id
            manufacturer = product.product_tmpl_id.sudo().intercompany_manufacturer_id
            if not manufacturer or manufacturer.id == self.company_id.id:
                continue
            free_qty = product.sudo().with_company(self.company_id).free_qty
            shortage_qty = move.product_uom_qty - free_qty
            if float_compare(shortage_qty, 0.0, precision_rounding=product.uom_id.rounding or 0.01) > 0:
                shortage_moves |= move
        return shortage_moves

    def action_confirm(self):
        res = super().action_confirm()
        for production in self:
            try:
                production.action_create_intercompany_supply()
            except Exception:
                # Defense in depth: an intercompany orchestration failure
                # must never block the MO's own confirmation, matching how
                # multichannel_overselling_guard's safety-net alert never
                # blocks a sale confirmation.
                _logger.warning(
                    "mrp_intercompany_wo_sync: automatic intercompany "
                    "supply check failed for %s", production.name,
                    exc_info=True)
        return res

    def action_create_intercompany_supply(self):
        """Create the intercompany purchase order (and the tracking link)
        for every raw-material shortage on this order that is covered by
        another company's manufacturing capability. Safe to call multiple
        times: an existing non-failed link for the same product is not
        duplicated. Callable automatically (from `action_confirm()`, wrapped
        there in try/except) or manually via the 'Check Intercompany
        Supply' button.
        """
        self.ensure_one()
        Link = self.env['mrp.production.intercompany.link']
        created_links = Link.browse()
        for move in self._get_intercompany_shortage_moves():
            product = move.product_id
            manufacturer = product.product_tmpl_id.sudo().intercompany_manufacturer_id
            free_qty = product.sudo().with_company(self.company_id).free_qty
            shortage_qty = move.product_uom_qty - free_qty

            existing = Link.sudo().search([
                ('parent_production_id', '=', self.id),
                ('product_id', '=', product.id),
                ('state', '!=', 'failed'),
            ], limit=1)
            if existing:
                continue

            link = self._create_intercompany_po_and_link(product, shortage_qty, manufacturer)
            if link:
                created_links |= link
        return created_links

    def _get_intercompany_price_unit(self, product, partner):
        """Price for the auto-created PO line: prefer a matching
        `product.supplierinfo` for this partner/product (the standard Odoo
        way to record an intercompany/vendor price), falling back to the
        product's own cost (`standard_price`) and, failing that, its sales
        price. Deliberately simple -- this module does not implement its
        own pricing/margin logic (see CHANGELOG.md)."""
        Supplierinfo = self.env['product.supplierinfo'].sudo()
        supplierinfo = Supplierinfo.search([
            ('partner_id', '=', partner.id),
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
        ], limit=1)
        if supplierinfo:
            return supplierinfo.price
        return product.standard_price or product.list_price

    def _create_intercompany_po_and_link(self, product, qty, manufacturer):
        """Create the intercompany PO to `manufacturer`'s partner, confirm
        it (relying on core `sale_purchase_inter_company_rules` to mirror it
        into a sales order in that company), and create the tracking link
        record. Never raises: any failure is logged and results in a
        'failed'-state link instead, so a bad intercompany setup on one
        product never blocks the rest of the MO's own confirmation flow.
        """
        self.ensure_one()
        partner = manufacturer.partner_id
        if not partner:
            _logger.warning(
                "mrp_intercompany_wo_sync: company %s has no partner_id, "
                "cannot raise an intercompany PO for %s",
                manufacturer.display_name, product.display_name)
            return False

        state = 'po_created'
        purchase_order = self.env['purchase.order']
        try:
            PurchaseOrder = self.env['purchase.order'].sudo().with_company(self.company_id)
            price_unit = self._get_intercompany_price_unit(product, partner)
            purchase_order = PurchaseOrder.create({
                'partner_id': partner.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'order_line': [(0, 0, {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_qty': qty,
                    'product_uom': (product.uom_po_id or product.uom_id).id,
                    'price_unit': price_unit,
                    'date_planned': fields.Datetime.now(),
                })],
            })
            if hasattr(purchase_order, 'button_confirm'):
                purchase_order.button_confirm()
            else:
                purchase_order.action_confirm()
        except Exception:
            _logger.warning(
                "mrp_intercompany_wo_sync: failed to create/confirm "
                "intercompany PO for %s on %s",
                product.display_name, self.name, exc_info=True)
            state = 'failed'

        link = self.env['mrp.production.intercompany.link'].sudo().create({
            'parent_production_id': self.id,
            'product_id': product.id,
            'product_qty': qty,
            'parent_company_id': self.company_id.id,
            'child_company_id': manufacturer.id,
            'purchase_order_id': purchase_order.id if purchase_order else False,
            'state': state,
        })
        if state == 'po_created':
            try:
                link._find_matching_sale_order()
            except Exception:
                _logger.warning(
                    "mrp_intercompany_wo_sync: could not look up mirrored "
                    "sale order for link %s", link.id, exc_info=True)
        return link
