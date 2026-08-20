from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class AutomotiveVehicleInspection(models.Model):
    _name = 'automotive.vehicle.inspection'
    _description = 'Vehicle Check-in/Check-out Inspection'
    _inherit = ['mail.thread', 'automotive.deletion.request.mixin']
    _order = 'datetime desc'

    repair_order_id = fields.Many2one(
        'automotive.repair.order', required=True, ondelete='cascade', index=True,
    )
    vehicle_id = fields.Many2one(related='repair_order_id.vehicle_id', store=True)
    inspection_type = fields.Selection([
        ('checkin', 'Check-in'),
        ('checkout', 'Check-out'),
    ], required=True)
    datetime = fields.Datetime(default=fields.Datetime.now, required=True)
    recorded_by = fields.Many2one('res.users', string='Recorded By')

    media_ids = fields.Many2many(
        'ir.attachment', string='Photos/Videos',
        help="Standard ir.attachment mechanism — Odoo's own file storage, "
             'not a custom one.',
    )
    item_ids = fields.One2many(
        'automotive.vehicle.inspection.item', 'inspection_id', string='Belongings/Condition Notes',
    )
    customer_signature = fields.Binary(string='Customer Signature')
    signature_full_name = fields.Char(string='Signed By')

    @api.onchange('repair_order_id')
    def _onchange_repair_order_id(self):
        if self.repair_order_id and not self.signature_full_name:
            self.signature_full_name = self.repair_order_id.partner_id.name

    @api.onchange('repair_order_id', 'inspection_type')
    def _onchange_prefill_checkout_items(self):
        """Check-out should list the same belongings recorded at check-in,
        so the user is confirming/ticking a known list rather than
        re-typing it from memory (and potentially dropping something)."""
        if self.inspection_type == 'checkout' and self.repair_order_id and not self.item_ids:
            checkin = self.repair_order_id.inspection_ids.filtered(
                lambda i: i.inspection_type == 'checkin'
            )[:1]
            if checkin.item_ids:
                self.item_ids = [
                    (0, 0, {'description': item.description, 'quantity': item.quantity})
                    for item in checkin.item_ids
                ]

    _one_per_type_per_order = models.Constraint(
        'unique(repair_order_id, inspection_type)',
        'A repair order can only have one check-in and one check-out inspection.',
    )

    @api.constrains('inspection_type', 'item_ids')
    def _check_checkout_items_returned(self):
        for inspection in self:
            if inspection.inspection_type != 'checkout':
                continue
            checkin = inspection.repair_order_id.inspection_ids.filtered(
                lambda i: i.inspection_type == 'checkin'
            )[:1]
            if checkin.item_ids and not inspection.item_ids:
                raise ValidationError(_(
                    'This vehicle had belongings recorded at check-in — they must be '
                    'listed and confirmed as returned before check-out can be saved.'
                ))
            if inspection.item_ids.filtered(lambda i: not i.returned):
                raise ValidationError(_(
                    'All belongings must be ticked as returned before this check-out '
                    'can be saved.'
                ))

    def _is_locked(self):
        self.ensure_one()
        return bool(self.recorded_by)

    def write(self, vals):
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager'):
            for inspection in self:
                if inspection._is_locked() and set(vals.keys()) - {'media_ids', 'item_ids'}:
                    raise AccessError(_(
                        'This inspection was already recorded by %s and cannot be edited — '
                        'handover documentation is kept immutable for dispute protection.'
                    ) % inspection.recorded_by.display_name)
        return super().write(vals)

    def unlink(self):
        if not self.env.user.has_group('bs_automotive_repair_management.group_shop_manager'):
            for inspection in self:
                if inspection._is_locked():
                    raise AccessError(_('Recorded inspections cannot be deleted.'))
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals.setdefault('recorded_by', self.env.user.id)
        inspections = super().create(vals_list)
        checkouts = inspections.filtered(lambda i: i.inspection_type == 'checkout')
        for inspection in checkouts:
            inspection.repair_order_id.part_ids.filtered(
                lambda p: not p.warranty_start_date
            ).write({'warranty_start_date': inspection.datetime.date()})
        for inspection in inspections:
            inspection._send_inspection_email()
        return inspections

    def _send_inspection_email(self):
        self.ensure_one()
        if not self.repair_order_id.partner_id.email:
            return
        self.message_post_with_source(
            'bs_automotive_repair_management.mail_template_inspection_recorded',
            subtype_xmlid='mail.mt_comment',
            attachment_ids=[(6, 0, self.media_ids.ids)],
        )
