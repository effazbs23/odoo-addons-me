# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    valuation_total = fields.Monetary(
        string='Total Valuation',
        currency_field='company_currency_id',
        compute='_compute_valuation_total',
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
        compute='_compute_valuation_total',
    )

    journal_entry_count = fields.Integer(
        string='Journal Entries',
        compute='_compute_valuation_total',
    )

    @api.depends('move_ids.value', 'move_ids.is_in', 'move_ids.is_out', 'move_ids.is_dropship',
                 'move_ids.account_move_id', 'state')
    def _compute_valuation_total(self):
        for picking in self:
            valued_moves = picking.move_ids.filtered(
                lambda m: m.state == 'done' and (m.is_in or m.is_out or m.is_dropship)
            )
            picking.valuation_total = sum(abs(m.value) for m in valued_moves)
            picking.valued_move_count = len(valued_moves)
            journal_entries = valued_moves.mapped('account_move_id').filtered(bool)
            picking.journal_entry_count = len(journal_entries)

    def action_view_picking_valuation(self):
        """Open the valuation details for this picking."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'bs_inventory_valuation_details.action_stock_move_valuation'
        )
        action['domain'] = [
            ('picking_id', '=', self.id),
            ('state', '=', 'done'),
        ]
        action['context'] = {
            'default_picking_id': self.id,
            'search_default_picking_id': self.id,
        }
        action['display_name'] = f'Valuation: {self.name}'
        return action

    def action_view_valuation_journal_entries(self):
        """Open all journal entries created for this picking's stock moves."""
        self.ensure_one()
        valued_moves = self.move_ids.filtered(
            lambda m: m.state == 'done' and (m.is_in or m.is_out or m.is_dropship)
        )
        journal_entry_ids = valued_moves.mapped('account_move_id').filtered(bool).ids
        return {
            'name': f'Journal Entries: {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', journal_entry_ids)],
            'context': {'default_move_type': 'entry'},
        }

