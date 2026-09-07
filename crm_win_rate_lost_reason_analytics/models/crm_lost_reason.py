from odoo import fields, models

CATEGORY_SELECTION = [
    ('pricing', 'Pricing'),
    ('timing', 'Timing'),
    ('competitor', 'Competitor'),
    ('no_budget', 'No Budget'),
    ('no_response', 'No Response'),
    ('not_a_fit', 'Not a Fit'),
    ('other', 'Other'),
]


class CrmLostReason(models.Model):
    _inherit = 'crm.lost.reason'

    # default='other' so adding this required field backfills every
    # pre-existing crm.lost.reason row automatically during module install
    # (Odoo applies a field's Python default as the SQL default for
    # existing rows when the column is created).
    category = fields.Selection(
        CATEGORY_SELECTION,
        string='Category',
        required=True,
        default='other',
    )
