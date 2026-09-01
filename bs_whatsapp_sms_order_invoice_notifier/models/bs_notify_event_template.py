from odoo import fields, models

EVENT_TYPE_SELECTION = [
    ('so_confirmed', 'Sales Order Confirmed'),
    ('delivery_shipped', 'Delivery Shipped'),
    ('invoice_posted', 'Invoice Posted'),
    ('payment_received', 'Payment Received'),
    ('invoice_overdue', 'Invoice Overdue'),
]


class BsNotifyEventTemplate(models.Model):
    _name = 'bs.notify.event.template'
    _description = 'Notification Event Template'

    event_type = fields.Selection(EVENT_TYPE_SELECTION, required=True)
    active = fields.Boolean(default=True)
    channel = fields.Selection(
        [('whatsapp', 'WhatsApp'), ('sms', 'SMS'), ('both', 'Both')],
        required=True, default='both',
    )
    message_template = fields.Text(required=True)
    company_id = fields.Many2one('res.company', help="Leave empty to apply to every company without its own override.")

    _event_company_uniq = models.Constraint(
        'unique(event_type, company_id)',
        "Only one template is allowed per event per company (use a company-specific row to override the global default).",
    )

    def _get_active(self, event_type, company):
        # company-specific row (if any) wins over the global (company_id
        # empty) default -- ordering by company_id puts the non-null value
        # first since NULL sorts last ascending.
        return self.search([
            ('event_type', '=', event_type),
            ('active', '=', True),
            ('company_id', 'in', (company.id, False)),
        ], order='company_id', limit=1)
