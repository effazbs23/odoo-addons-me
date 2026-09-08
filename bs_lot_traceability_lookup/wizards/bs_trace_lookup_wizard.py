from odoo import fields, models
from odoo.exceptions import UserError


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
        })
        return True

    def action_export_pdf(self):
        self.ensure_one()
        if not self.lot_id or not self.has_result:
            raise UserError(self.env._('Search a lot first, then export.'))
        self.env['bs.traceability.export.log'].create({
            'lot_id': self.lot_id.id,
            'direction': self.direction,
        })
        return self.env.ref('bs_lot_traceability_lookup.action_report_bs_trace_export').report_action(self)
