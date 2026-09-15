from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class BsTraceLookupWizard(models.TransientModel):
    _name = 'bs.trace.lookup.wizard'
    _description = 'Batch Traceability Lookup'

    lot_id = fields.Many2one('stock.lot', string='Lot/Serial Number')
    direction = fields.Selection([
        ('backward', 'Where did this come from? (backward)'),
        ('forward', 'Where did this go? (forward)'),
        ('both', 'Both directions'),
    ], required=True, default='both')
    max_depth = fields.Integer(
        default=lambda self: self.env['bs.traceability.engine'].MAX_DEPTH_DEFAULT,
        help='Maximum number of manufacturing-order hops to follow in each direction.')

    summary_text = fields.Text(string='Plain-Language Summary', readonly=True)
    chain_html = fields.Html(string='Full Chain', readonly=True, sanitize=False)
    has_result = fields.Boolean(readonly=True)
    status_class = fields.Selection([
        ('success', 'Cleared'),
        ('warning', 'Partial'),
        ('info', 'In Stock'),
        ('secondary', 'Backward Trace Only'),
    ], readonly=True, string='Status')

    def _compute_status_class(self, forward_nodes):
        if forward_nodes is None:
            return 'secondary'
        if len(forward_nodes) == 1 and forward_nodes[0]['boundary'] == 'no_history':
            return 'info'
        # Something has moved out, but the lot isn't necessarily fully
        # cleared - part of its quantity may still sit on hand (e.g. 60
        # of 100 units consumed into an MO, 40 still in stock). Only
        # report "Cleared" once nothing of this lot remains anywhere.
        on_hand = self.env['bs.traceability.engine'].lot_on_hand_qty(self.lot_id)
        rounding = self.lot_id.product_id.uom_id.rounding
        return 'success' if float_is_zero(on_hand, precision_rounding=rounding) else 'warning'

    def action_search(self):
        self.ensure_one()
        if not self.lot_id:
            raise UserError(self.env._('Pick or scan a lot/serial number first.'))
        engine = self.env['bs.traceability.engine']
        backward = engine.backward_trace(self.lot_id, self.max_depth) if self.direction in ('backward', 'both') else None
        forward = engine.forward_trace(self.lot_id, self.max_depth) if self.direction in ('forward', 'both') else None
        summary = engine.build_summary(self.lot_id, backward, forward)
        nodes = (backward or []) + (forward or [])
        self.write({
            'summary_text': summary,
            'chain_html': engine.render_chain_html(nodes),
            'has_result': True,
            'status_class': self._compute_status_class(forward),
        })
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Trace Lookup'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_export_pdf(self):
        self.ensure_one()
        if not self.lot_id or not self.has_result:
            raise UserError(self.env._('Search a lot first, then export.'))
        self.env['bs.traceability.export.log'].create({
            'lot_id': self.lot_id.id,
            'direction': self.direction,
        })
        action = self.env.ref('bs_lot_traceability_lookup.action_report_bs_trace_export').report_action(self)
        # Close this target=new dialog automatically once the PDF has
        # downloaded, instead of leaving it open behind the download.
        action['close_on_report_download'] = True
        return action
