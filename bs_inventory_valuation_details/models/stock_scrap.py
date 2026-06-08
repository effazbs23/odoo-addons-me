# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    valuation_total = fields.Monetary(
        string='Scrap Valuation',
        currency_field='company_currency_id',
        compute='_compute_scrap_valuation_total',
        store=False,
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True,
    )
    valued_move_count = fields.Integer(
        string='Valued Moves',
        compute='_compute_scrap_valuation_total',
    )

    @api.depends('move_ids.value', 'move_ids.is_out', 'move_ids.state')
    def _compute_scrap_valuation_total(self):
        for scrap in self:
            # Scrap moves are outgoing (stock → scrap location), so is_out = True
            valued_moves = scrap.move_ids.filtered(
                lambda m: m.state == 'done' and (m.is_out or m.is_in)
            )
            scrap.valuation_total = sum(abs(m.value) for m in valued_moves)
            scrap.valued_move_count = len(valued_moves)

    def action_view_scrap_valuation(self):
        """Open the valuation details for this scrap order."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bs_inventory_valuation_details.action_stock_move_valuation'
        )
        action['domain'] = [
            ('scrap_id', '=', self.id),
            ('state', '=', 'done'),
        ]
        action['context'] = {
            'default_scrap_id': self.id,
        }
        action['display_name'] = f'Scrap Valuation: {self.name}'
        return action

