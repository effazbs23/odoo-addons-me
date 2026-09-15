from odoo import fields, models


class MrpBomVariantMatrixWizard(models.TransientModel):
    _name = 'mrp.bom.variant.matrix.wizard'
    _description = 'Variant-Aware BOM Matrix'

    bom_id = fields.Many2one(
        'mrp.bom', string='Bill of Materials', required=True,
        default=lambda self: self.env.context.get('active_id'))
