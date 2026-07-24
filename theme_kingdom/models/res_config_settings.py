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
    kingdom_coming_soon_show_subscribe = fields.Boolean(
        related='website_id.kingdom_coming_soon_show_subscribe',
        readonly=False,
    )
    kingdom_coming_soon_subscribe_text = fields.Char(
        related='website_id.kingdom_coming_soon_subscribe_text',
        readonly=False,
    )
    kingdom_coming_soon_subscribe_button = fields.Char(
        related='website_id.kingdom_coming_soon_subscribe_button',
        readonly=False,
    )
    kingdom_coming_soon_bg_image = fields.Image(
        related='website_id.kingdom_coming_soon_bg_image',
        readonly=False,
    )
    kingdom_coming_soon_subscriber_count = fields.Integer(
        related='website_id.kingdom_coming_soon_subscriber_count',
        readonly=True,
    )

    def action_preview_coming_soon(self):
        self.ensure_one()
        return self.website_id.action_preview_coming_soon()

    def action_open_coming_soon_subscribers(self):
        self.ensure_one()
        return self.website_id.action_open_coming_soon_subscribers()
