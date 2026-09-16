from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    intercompany_manufacturer_id = fields.Many2one(
        'res.company',
        string='Produced By Company',
        help="If set, this marks that this component is actually manufactured "
             "by a different company within THIS SAME Odoo database (a "
             "standard multi-company setup, not two separate Odoo "
             "instances). When a manufacturing order in another company of "
             "this database needs this product as a raw material and cannot "
             "fulfill the needed quantity from stock, this module can "
             "automatically create an intercompany purchase from -- and, "
             "when necessary, a manufacturing order in -- this company.",
    )
