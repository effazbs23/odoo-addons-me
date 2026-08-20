from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    max_discount_percent = fields.Float(
        string='Max Discount %',
        default=100.0,
        help='Highest discount percentage this user is allowed to grant on '
             'a repair order. Enforced server-side on automotive.repair.order, '
             'not just in the UI. Defaults to 100 (effectively uncapped) so a '
             'fresh install does not block ordinary discounting before an '
             'admin has visited each user\'s Repair Shop settings tab — lower '
             'it per user to actually restrict discounting.',
    )
