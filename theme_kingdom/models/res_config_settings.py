# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    kingdom_coming_soon_enabled = fields.Boolean(
        related='website_id.kingdom_coming_soon_enabled',
        readonly=False,
    )
    kingdom_coming_soon_title = fields.Char(
        related='website_id.kingdom_coming_soon_title',
        readonly=False,
    )
    kingdom_coming_soon_subtitle = fields.Text(
        related='website_id.kingdom_coming_soon_subtitle',
        readonly=False,
    )
    kingdom_coming_soon_launch_datetime = fields.Datetime(
        related='website_id.kingdom_coming_soon_launch_datetime',
        readonly=False,
    )
    kingdom_coming_soon_show_countdown = fields.Boolean(
        related='website_id.kingdom_coming_soon_show_countdown',
        readonly=False,
    )
    kingdom_coming_soon_bg_image = fields.Image(
        related='website_id.kingdom_coming_soon_bg_image',
        readonly=False,
    )
    kingdom_coming_soon_show_admin_login = fields.Boolean(
        related='website_id.kingdom_coming_soon_show_admin_login',
        readonly=False,
    )
    kingdom_coming_soon_login_show_header_footer = fields.Boolean(
        related='website_id.kingdom_coming_soon_login_show_header_footer',
        readonly=False,
    )

    def action_preview_coming_soon(self):
        self.ensure_one()
        return self.website_id.action_preview_coming_soon()
