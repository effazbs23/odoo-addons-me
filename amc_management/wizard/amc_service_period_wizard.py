from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AmcServicePeriodWizardMixin(models.AbstractModel):
    """Shared plumbing for the three service-period closure wizards."""
    _name = 'amc.service.period.wizard.mixin'
    _description = 'AMC Service Period Wizard Mixin'

    service_period_id = fields.Many2one('amc.contract', string='Service Period',
                                        required=True, readonly=True, ondelete='cascade')
    amc_id = fields.Many2one('amc.contract', string='Mother AMC',
                             related='service_period_id.parent_amc_id', readonly=True)
    site_id = fields.Many2one('amc.site', string='Site', compute='_compute_site_id')
    start_date = fields.Date(string='Start Date', related='service_period_id.start_date', readonly=True)
    end_date = fields.Date(string='End Date', related='service_period_id.end_date', readonly=True)
    total_days = fields.Integer(string='Total Days', related='service_period_id.service_days',
                                readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,
                                  default=lambda self: self.env.company.currency_id)

    @api.depends('service_period_id')
    def _compute_site_id(self):
        """Site of the period, falling back to its Mother AMC and then to the order line."""
        for wizard in self:
            period = wizard.service_period_id
            contract = period.parent_amc_id or period
            wizard.site_id = period.site_id or contract.site_id \
                or (contract._amc_site() if contract else False)

    def _store_service_report(self, period, report, filename, extra_attachment_ids=None):
        """Persist the wizard's uploads onto the service period."""
        vals = {}
        if report:
            vals.update({'service_report': report, 'service_report_filename': filename})
        if extra_attachment_ids:
            vals['other_attachment_ids'] = [(4, attachment_id) for attachment_id in extra_attachment_ids]
        if vals:
            period.write(vals)


class AmcMarkDoneWizard(models.TransientModel):
    _name = 'amc.mark.done.wizard'
    _description = 'Mark AMC Service Period as Done'
    _inherit = ['amc.service.period.wizard.mixin']

    service_report = fields.Binary(string='Service Report', required=True,
                                   help='Mandatory proof of service for this period.')
    service_report_filename = fields.Char(string='Service Report Filename')
    other_attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    remarks = fields.Text(string='Remarks')

    def action_confirm(self):
        self.ensure_one()
        period = self.service_period_id
        period._amc_check_period_editable()
        if not self.service_report:
            raise ValidationError(_("A service report must be attached before marking the period as done."))

        self._store_service_report(period, self.service_report, self.service_report_filename,
                                   self.other_attachment_ids.ids)
        period._amc_apply_done()
        if self.remarks:
            period.message_post(body=self.remarks)
        return {'type': 'ir.actions.act_window_close'}


class AmcPartialServiceWizard(models.TransientModel):
    _name = 'amc.partial.service.wizard'
    _description = 'Mark AMC Service Period as Partially Serviced'
    _inherit = ['amc.service.period.wizard.mixin']

    days_serviced = fields.Integer(string='Days Serviced', required=True)
    days_not_serviced = fields.Integer(string='Days Not Serviced', compute='_compute_days_not_serviced')
    reversal_amount = fields.Monetary(string='Reversal Amount', compute='_compute_days_not_serviced',
                                      currency_field='currency_id')
    service_report = fields.Binary(string='Service Report', required=True)
    service_report_filename = fields.Char(string='Service Report Filename')
    other_attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    remarks = fields.Text(string='Remarks')

    @api.depends('days_serviced', 'total_days', 'service_period_id')
    def _compute_days_not_serviced(self):
        for wizard in self:
            not_serviced = max(wizard.total_days - wizard.days_serviced, 0)
            wizard.days_not_serviced = not_serviced
            wizard.reversal_amount = wizard.service_period_id._amc_daily_rate() * not_serviced \
                if wizard.service_period_id else 0.0

    @api.constrains('days_serviced')
    def _check_days_serviced(self):
        for wizard in self:
            if wizard.days_serviced <= 0 or wizard.days_serviced >= wizard.total_days:
                raise ValidationError(_(
                    "Days serviced must be between 1 and %(total)s. "
                    "A fully serviced period should be marked as Done instead.",
                    total=wizard.total_days,
                ))

    def action_confirm(self):
        self.ensure_one()
        period = self.service_period_id
        period._amc_check_period_editable()
        if not self.service_report:
            raise ValidationError(_(
                "A service report must be attached before marking the period as partially serviced."))

        self._store_service_report(period, self.service_report, self.service_report_filename,
                                   self.other_attachment_ids.ids)
        reversal = period._amc_apply_partial_service(self.days_serviced)
        body = _("Marked as Partially Serviced: %(done)s of %(total)s days serviced.",
                 done=self.days_serviced, total=self.total_days)
        if self.remarks:
            body = '%s<br/>%s' % (body, self.remarks)
        if reversal:
            body = '%s<br/>%s' % (body, _("Reversal entry %s created in draft.", reversal.ref))
        period.message_post(body=body)
        return {'type': 'ir.actions.act_window_close'}


class AmcExpirePeriodWizard(models.TransientModel):
    _name = 'amc.expire.period.wizard'
    _description = 'Expire AMC Service Period'
    _inherit = ['amc.service.period.wizard.mixin']

    reason = fields.Text(string='Reason for Expiry', required=True)
    reversal_amount = fields.Monetary(string='Reversal Amount', compute='_compute_reversal_amount',
                                      currency_field='currency_id')

    @api.depends('service_period_id', 'total_days')
    def _compute_reversal_amount(self):
        for wizard in self:
            # An expired period was never serviced, so the whole period is reversed.
            wizard.reversal_amount = wizard.service_period_id._amc_daily_rate() * wizard.total_days \
                if wizard.service_period_id else 0.0

    def action_confirm(self):
        self.ensure_one()
        period = self.service_period_id
        period._amc_check_period_editable()
        if not (self.reason or '').strip():
            raise ValidationError(_("A reason is required to expire a service period."))

        reversal = period._amc_apply_expiry(self.reason.strip())
        body = _("Service period expired. Reason: %s", self.reason.strip())
        if reversal:
            body = '%s<br/>%s' % (body, _("Reversal entry %s created in draft.", reversal.ref))
        period.message_post(body=body)
        return {'type': 'ir.actions.act_window_close'}
