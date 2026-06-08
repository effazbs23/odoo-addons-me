# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_categ_id = fields.Many2one("product.category", related="product_id.categ_id")

    # ------------------------------------------------------------------ #
    #  Journal Entry lines (real JE — only when location has valuation    #
    #  account set, which is uncommon in standard Odoo 19 setup)          #
    # ------------------------------------------------------------------ #
    account_move_line_ids = fields.One2many(
        related='account_move_id.line_ids',
        string='Journal Items',
    )
    account_move_ref = fields.Char(
        related='account_move_id.name',
        string='Journal Entry Ref',
    )
    account_move_date = fields.Date(
        related='account_move_id.date',
        string='Accounting Date',
    )
    account_move_journal_id = fields.Many2one(
        related='account_move_id.journal_id',
        string='Journal',
    )

    # ------------------------------------------------------------------ #
    #  Simulated Journal Entry                                             #
    #  In Odoo 19 most moves don't create a JE per-move — valuation is    #
    #  reconciled at period closing via one journal entry. These fields    #
    #  show what the expected debit/credit lines WOULD look like.         #
    # ------------------------------------------------------------------ #
    sim_debit_account_id = fields.Many2one(
        'account.account',
        string='Expected Debit Account',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_credit_account_id = fields.Many2one(
        'account.account',
        string='Expected Credit Account',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_debit_label = fields.Char(
        string='Debit Label',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_credit_label = fields.Char(
        string='Credit Label',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_amount = fields.Monetary(
        string='Expected Amount',
        currency_field='company_currency_id',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_note = fields.Char(
        string='Valuation Note',
        compute='_compute_simulated_journal',
        store=False,
    )
    sim_has_accounts = fields.Boolean(
        string='Has Simulated Accounts',
        compute='_compute_simulated_journal',
        store=False,
    )

    # ------------------------------------------------------------------ #
    #  Valuation method (periodic vs real_time) — for display/filter      #
    # ------------------------------------------------------------------ #
    product_valuation = fields.Selection(
        [('periodic', 'Periodic'), ('real_time', 'Perpetual')],
        string='Valuation Method',
        related='product_id.valuation',
        store=False,
    )
    product_is_storable = fields.Boolean(
        string='Is Storable',
        related='product_id.is_storable',
        store=False,
    )

    # ------------------------------------------------------------------ #
    #  Cost Method                                                         #
    # ------------------------------------------------------------------ #
    cost_method = fields.Selection(
        [
            ('standard', 'Standard Price'),
            ('average', 'Average Cost (AVCO)'),
            ('fifo', 'First In First Out (FIFO)'),
        ],
        string='Cost Method',
        compute='_compute_valuation_display',
        store=False,
    )

    # ------------------------------------------------------------------ #
    #  Move Direction                                                      #
    # ------------------------------------------------------------------ #
    move_direction = fields.Char(
        string='Direction / Type',
        compute='_compute_valuation_display',
        store=False,
    )

    # ------------------------------------------------------------------ #
    #  Source Document                                                     #
    # ------------------------------------------------------------------ #
    source_document_type = fields.Selection(
        [
            ('picking', 'Transfer / Picking'),
            ('production_output', 'MRP: Finished Product'),
            ('production_component', 'MRP: Component'),
            ('scrap', 'Scrap'),
            ('unbuild_output', 'Unbuild: Product Disassembly'),
            ('unbuild_component', 'Unbuild: Component Return'),
            ('other', 'Other'),
        ],
        string='Document Type',
        compute='_compute_valuation_display',
        store=False,
    )
    source_document_ref = fields.Char(
        string='Source Document',
        compute='_compute_valuation_display',
        store=False,
    )

    # ------------------------------------------------------------------ #
    #  Monetary helpers                                                    #
    # ------------------------------------------------------------------ #
    price_unit_display = fields.Float(
        string='Unit Cost',
        compute='_compute_price_unit_display',
        digits='Product Price',
        store=False,
    )
    abs_value = fields.Monetary(
        string='Valuation',
        currency_field='company_currency_id',
        compute='_compute_abs_value',
        store=False,
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Currency',
        readonly=True,
    )

    # ------------------------------------------------------------------ #
    #  Simulated Journal Entry Compute                                     #
    # ------------------------------------------------------------------ #
    @api.depends(
        'value', 'is_in', 'is_out', 'is_dropship', 'state',
        'product_id', 'product_id.is_storable', 'product_id.valuation',
        'product_id.categ_id',
        'product_id.categ_id.property_stock_valuation_account_id',
        'scrap_id',
        'picking_id.picking_type_code',
        'account_move_id',
    )
    def _compute_simulated_journal(self):
        _EMPTY = dict(
            sim_debit_account_id=False,
            sim_credit_account_id=False,
            sim_debit_label=False,
            sim_credit_label=False,
            sim_amount=0.0,
            sim_note=False,
            sim_has_accounts=False,
        )

        for move in self:
            # ── Guard 1: not a valued move at all ──────────────────────
            if not (move.is_in or move.is_out or move.is_dropship) or move.state != 'done':
                move.update(_EMPTY)
                continue

            # ── Guard 2: non-storable product (service / untracked consumable) ──
            if not move.product_id.is_storable:
                move.update(_EMPTY)
                move.sim_note = (
                    'No valuation: product is a Service or a Consumable '
                    'without inventory tracking enabled.'
                )
                continue

            # ── Guard 3: real journal entry already exists ─────────────
            if move.account_move_id:
                move.update(_EMPTY)
                continue

            # ── Resolve Odoo 19 accounts ───────────────────────────────
            accounts = move.product_id.with_company(move.company_id)._get_product_accounts()
            stock_valuation_acc = accounts.get('stock_valuation')
            stock_variation_acc = accounts.get('stock_variation')
            expense_acc = accounts.get('expense')

            if not stock_variation_acc:
                stock_variation_acc = move.company_id.expense_account_id or expense_acc

            wip_account = move.company_id._get_field_value_safe('account_production_wip_account_id')

            # ── Periodic valuation note prefix ────────────────────────
            is_periodic = (move.product_id.valuation == 'periodic')
            periodic_prefix = (
                'Periodic valuation — accounting is posted at period closing, not per move. '
                if is_periodic else ''
            )

            debit_acc = credit_acc = False
            debit_label = credit_label = ''
            note = ''

            production_id = move._get_field_value('production_id')
            raw_material_production_id = move._get_field_value('raw_material_production_id')

            if move.is_dropship:
                debit_acc = stock_variation_acc
                credit_acc = stock_variation_acc
                debit_label = 'Stock Variation (Dropship)'
                credit_label = 'Stock Variation (Dropship)'
                note = periodic_prefix + 'Dropship: goods flow supplier→customer without entering stock.'

            elif production_id and move.is_in:
                debit_acc = stock_valuation_acc
                credit_acc = wip_account or stock_variation_acc
                debit_label = 'Stock Valuation (Finished Product In)'
                credit_label = 'Production WIP / Stock Variation'
                note = periodic_prefix + 'Finished product received from Manufacturing Order into stock.'

            elif raw_material_production_id and move.is_out:
                debit_acc = wip_account or stock_variation_acc
                credit_acc = stock_valuation_acc
                debit_label = 'Production WIP / Stock Variation (Component Out)'
                credit_label = 'Stock Valuation'
                note = periodic_prefix + 'Raw material component consumed by Manufacturing Order.'

            elif move.scrap_id and move.is_out:
                debit_acc = expense_acc or stock_variation_acc
                credit_acc = stock_valuation_acc
                debit_label = 'Expense / Scrap Account'
                credit_label = 'Stock Valuation'
                note = periodic_prefix + 'Product scrapped — value removed from stock into expense.'

            elif move.is_in:
                debit_acc = stock_valuation_acc
                credit_acc = stock_variation_acc or expense_acc
                debit_label = 'Stock Valuation'
                credit_label = 'Stock Variation'
                if is_periodic:
                    note = (
                        'Periodic valuation: this incoming move increases inventory value. '
                        'The accounting entry will be posted at the next period closing.'
                    )
                else:
                    note = (
                        'Perpetual (Odoo 19): inventory value tracked on stock.move.value. '
                        'Accounting is reconciled at period closing via a single journal entry.'
                    )

            elif move.is_out:
                picking_type_code = move.picking_id.picking_type_code if move.picking_id else False
                if picking_type_code == 'outgoing':
                    debit_acc = expense_acc or stock_variation_acc
                    credit_acc = stock_valuation_acc
                    debit_label = 'Expense / COGS'
                    credit_label = 'Stock Valuation'
                    if is_periodic:
                        note = (
                            'Periodic valuation: COGS for this delivery will be posted '
                            'at the next period closing, not immediately.'
                        )
                    else:
                        note = (
                            'Perpetual (Odoo 19): COGS tracked on stock.move.value. '
                            'Accounting reconciled at period closing.'
                        )
                else:
                    debit_acc = stock_variation_acc or expense_acc
                    credit_acc = stock_valuation_acc
                    debit_label = 'Stock Variation'
                    credit_label = 'Stock Valuation'
                    note = periodic_prefix + 'Outgoing move (non-sales): stock value reduced.'

            move.sim_debit_account_id = debit_acc or False
            move.sim_credit_account_id = credit_acc or False
            move.sim_debit_label = debit_label
            move.sim_credit_label = credit_label
            move.sim_amount = abs(move.value)
            move.sim_note = note
            move.sim_has_accounts = bool(debit_acc and credit_acc)

    def _get_field_value(self, field_name):
        """Safely get a relational field value that may not exist if MRP not installed."""
        try:
            return self[field_name]
        except (KeyError, AttributeError):
            return False

    # ------------------------------------------------------------------ #
    #  Combined display compute                                            #
    # ------------------------------------------------------------------ #
    @api.depends(
        'product_id.categ_id.property_cost_method',
        'is_in', 'is_out', 'is_dropship',
        'picking_id', 'picking_id.picking_type_code',
        'origin_returned_move_id',
        'scrap_id',
        'reference',
    )
    def _compute_valuation_display(self):
        for move in self:
            move.cost_method = move.product_id.categ_id.property_cost_method or 'standard'

            if move.scrap_id:
                move.source_document_type = 'scrap'
                move.source_document_ref = move.scrap_id.name
                move.move_direction = 'Scrap'
                continue

            production_id = move._get_field_value('production_id')
            raw_material_production_id = move._get_field_value('raw_material_production_id')
            unbuild_id = move._get_field_value('unbuild_id')
            consume_unbuild_id = move._get_field_value('consume_unbuild_id')

            if production_id:
                move.source_document_type = 'production_output'
                move.source_document_ref = production_id.name if hasattr(production_id, 'name') else move.reference
                move.move_direction = 'MRP: Finished Product'
                continue

            if raw_material_production_id:
                move.source_document_type = 'production_component'
                move.source_document_ref = raw_material_production_id.name if hasattr(raw_material_production_id, 'name') else move.reference
                move.move_direction = 'MRP: Component Used'
                continue

            if unbuild_id:
                move.source_document_type = 'unbuild_output'
                move.source_document_ref = unbuild_id.name if hasattr(unbuild_id, 'name') else move.reference
                move.move_direction = 'Unbuild: Product'
                continue

            if consume_unbuild_id:
                move.source_document_type = 'unbuild_component'
                move.source_document_ref = consume_unbuild_id.name if hasattr(consume_unbuild_id, 'name') else move.reference
                move.move_direction = 'Unbuild: Component'
                continue

            if move.picking_id:
                move.source_document_type = 'picking'
                move.source_document_ref = move.picking_id.name
                picking_type_code = move.picking_id.picking_type_code
                is_return = bool(move.origin_returned_move_id)

                if move.is_dropship:
                    move.move_direction = 'Dropship'
                elif is_return and move.is_in:
                    move.move_direction = 'Return (Customer → Stock)'
                elif is_return and move.is_out:
                    move.move_direction = 'Return (Stock → Vendor)'
                elif picking_type_code == 'incoming' and move.is_in:
                    move.move_direction = 'Receipt'
                elif picking_type_code == 'outgoing' and move.is_out:
                    move.move_direction = 'Delivery'
                elif picking_type_code == 'internal' and move.is_in:
                    move.move_direction = 'Transfer In'
                elif picking_type_code == 'internal' and move.is_out:
                    move.move_direction = 'Transfer Out'
                elif move.is_in:
                    move.move_direction = 'Incoming'
                elif move.is_out:
                    move.move_direction = 'Outgoing'
                else:
                    move.move_direction = '-'
                continue

            move.source_document_type = 'other'
            move.source_document_ref = move.reference or '-'
            move.move_direction = 'Incoming' if move.is_in else ('Outgoing' if move.is_out else '-')

    @api.depends('value', 'quantity')
    def _compute_price_unit_display(self):
        for move in self:
            move.price_unit_display = abs(move.value) / move.quantity if move.quantity else 0.0

    @api.depends('value')
    def _compute_abs_value(self):
        for move in self:
            move.abs_value = abs(move.value)
