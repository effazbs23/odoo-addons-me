# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True,
    )
    valuation_finished_total = fields.Monetary(
        string='Finished Product Valuation',
        currency_field='company_currency_id',
        compute='_compute_production_valuation',
        store=False,
        help='Total value of finished product / byproduct moves for this Manufacturing Order.',
    )
    valuation_component_total = fields.Monetary(
        string='Component Cost',
        currency_field='company_currency_id',
        compute='_compute_production_valuation',
        store=False,
        help='Total value of component (raw material) moves consumed in this Manufacturing Order.',
    )
    valued_move_count = fields.Integer(
        string='Valued Moves',
        compute='_compute_production_valuation',
    )

    @api.depends(
        'move_finished_ids.value', 'move_finished_ids.state',
        'move_raw_ids.value', 'move_raw_ids.state',
    )
    def _compute_production_valuation(self):
        for production in self:
            # Finished product + byproduct moves (production_id set, is_in = True)
            finished_moves = production.move_finished_ids.filtered(
                lambda m: m.state == 'done' and (m.is_in or m.is_out)
            )
            # Component/raw material moves (raw_material_production_id set, is_out = True)
            raw_moves = production.move_raw_ids.filtered(
                lambda m: m.state == 'done' and (m.is_in or m.is_out)
            )
            production.valuation_finished_total = sum(abs(m.value) for m in finished_moves)
            production.valuation_component_total = sum(abs(m.value) for m in raw_moves)
            production.valued_move_count = len(finished_moves) + len(raw_moves)

    def action_view_production_valuation(self):
        """Open full valuation breakdown for this Manufacturing Order."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bs_inventory_valuation_details.action_stock_move_valuation'
        )
        # Moves linked to production: either as finished product (production_id)
        # or as consumed component (raw_material_production_id)
        finished_ids = self.move_finished_ids.ids
        raw_ids = self.move_raw_ids.ids
        all_move_ids = finished_ids + raw_ids
        action['domain'] = [
            ('id', 'in', all_move_ids),
            ('state', '=', 'done'),
        ]
        action['context'] = {
            'search_default_group_product': 1,
        }
        action['display_name'] = f'Valuation: {self.name}'
        return action

