from odoo import Command
from odoo.tests import TransactionCase


class TraceabilityCommon(TransactionCase):
    """Fixture helpers shared by every test in this module. Kept in one
    place per the build plan: build the synthetic dataset once, reuse it
    for backward, forward, summary, depth-cap and performance tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env.ref('stock.warehouse0')
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.engine = cls.env['bs.traceability.engine']
        cls.vendor = cls.env['res.partner'].create({'name': 'Test Vendor'})
        cls.customer = cls.env['res.partner'].create({'name': 'Test Customer'})

    def _make_product(self, name, tracking='lot'):
        return self.env['product.product'].create({
            'name': name,
            'is_storable': True,
            'tracking': tracking,
        })

    def _make_bom(self, finished_product, component_lines):
        """component_lines: list of (product, qty)."""
        return self.env['mrp.bom'].create({
            'product_id': finished_product.id,
            'product_tmpl_id': finished_product.product_tmpl_id.id,
            'product_uom_id': self.uom_unit.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [Command.create({'product_id': p.id, 'product_qty': q}) for p, q in component_lines],
        })

    def _force_move_line(self, move, lot, qty):
        """Deterministically assign a specific lot (or no lot) + quantity to
        a move's line, ignoring whatever automatic reservation produced -
        needed so fixtures are reproducible instead of depending on the
        default removal strategy picking an arbitrary lot."""
        move.move_line_ids.unlink()
        vals = {
            'product_id': move.product_id.id,
            'product_uom_id': move.product_uom.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
            'quantity': qty,
            'picked': True,
        }
        if lot:
            vals['lot_id'] = lot.id
        move.move_line_ids = [Command.create(vals)]

    def _receive_from_vendor(self, product, lot_name, qty):
        """Receive `qty` of `product` from a vendor into a fresh lot; returns the lot."""
        lot = self.env['stock.lot'].create({'name': lot_name, 'product_id': product.id}) if product.tracking != 'none' else False
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.in_type_id.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'partner_id': self.vendor.id,
        })
        move = self.env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': self.uom_unit.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
            'picking_id': picking.id,
        })
        picking.action_confirm()
        picking.action_assign()
        self._force_move_line(move, lot, qty)
        picking.button_validate()
        return lot

    def _deliver_to_customer(self, product, lot, qty, partner=None):
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.warehouse.out_type_id.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'partner_id': (partner or self.customer).id,
        })
        move = self.env['stock.move'].create({
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': self.uom_unit.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
            'picking_id': picking.id,
        })
        picking.action_confirm()
        picking.action_assign()
        self._force_move_line(move, lot, qty)
        picking.button_validate()
        return picking

    def _produce(self, bom, finished_product, component_lots, finished_lot_name, qty=1.0):
        """Run one component set through `bom` and produce `qty` of
        `finished_product` into a fresh lot named `finished_lot_name`.
        component_lots: dict {component_product: lot_or_False}.
        Returns the finished good's stock.lot (or False if untracked).
        """
        production = self.env['mrp.production'].create({
            'product_id': finished_product.id,
            'bom_id': bom.id,
            'product_qty': qty,
            'product_uom_id': self.uom_unit.id,
        })
        production.action_confirm()
        production.action_assign()
        for move in production.move_raw_ids:
            lot = component_lots.get(move.product_id)
            component_qty = qty * next(l.product_qty for l in bom.bom_line_ids if l.product_id == move.product_id)
            self._force_move_line(move, lot, component_qty)
        finished_lot = False
        if finished_product.tracking != 'none':
            finished_lot = self.env['stock.lot'].create({'name': finished_lot_name, 'product_id': finished_product.id})
            production.lot_producing_ids = [Command.set([finished_lot.id])]
        production.move_raw_ids.picked = True
        production.button_mark_done()
        return finished_lot, production
