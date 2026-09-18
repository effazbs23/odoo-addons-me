from odoo import api, fields, models, _


class AmcSite(models.Model):
    """A place a maintenance contract is served at: a building, a plant, a floor.

    Contracts, purchase order lines and the journal entries they generate all point
    at a site, which is what lets the schedule report group a vendor's contracts by
    the place they cover rather than only by the order they were bought on.
    """
    _name = 'amc.site'
    _description = 'AMC Site'
    _order = 'code, name'

    name = fields.Char(string='Site Name', required=True, translate=True)
    code = fields.Char(string='Code', required=True,
                       help='Short reference printed as the CODE column of the AMC schedule.')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company, index=True)
    partner_id = fields.Many2one('res.partner', string='Address',
                                 help='Contact carrying the postal address of the site.')
    # Provision entries copy this onto their lines, so a site can feed straight into
    # the analytic reporting the customer already runs.
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account',
        check_company=True,
        help='Stamped on the AMC provision and reversal entry lines raised for this site.')
    manager_id = fields.Many2one('res.users', string='Site Manager')
    note = fields.Text(string='Notes')

    contract_ids = fields.One2many('amc.contract', 'site_id', string='Contracts',
                                   domain=[('parent_amc_id', '=', False)])
    contract_count = fields.Integer(string='Contract Count', compute='_compute_contract_count')

    _code_company_uniq = models.Constraint(
        'UNIQUE(code, company_id)',
        'A site with this code already exists for this company.',
    )

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        # A site with no contract yet is the common case, so group rather than loop.
        counts = dict(self.env['amc.contract']._read_group(
            [('site_id', 'in', self.ids), ('parent_amc_id', '=', False)],
            groupby=['site_id'], aggregates=['__count']))
        for site in self:
            site.contract_count = counts.get(site, 0)

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for site in self:
            site.display_name = '%s - %s' % (site.code, site.name) if site.code else site.name

    def _amc_analytic_distribution(self):
        """Analytic distribution to stamp on entries raised for this site, or {}."""
        self.ensure_one()
        if not self.analytic_account_id:
            return {}
        return {str(self.analytic_account_id.id): 100}

    def action_view_contracts(self):
        self.ensure_one()
        return {
            'name': _('AMC Contracts'),
            'type': 'ir.actions.act_window',
            'res_model': 'amc.contract',
            'view_mode': 'list,form',
            'domain': [('site_id', '=', self.id), ('parent_amc_id', '=', False)],
            'context': {'create': False},
        }
