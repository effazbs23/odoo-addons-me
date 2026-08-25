# -*- coding: utf-8 -*-
from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    kingdom_coming_soon_enabled = fields.Boolean(
        string='Enable Coming Soon',
        default=False,
        help='When enabled, public visitors hitting the homepage are redirected '
             'to the Coming Soon page. Website designers keep normal access.',
    )
    kingdom_coming_soon_title = fields.Char(
        string='Coming Soon Title',
        default='Coming Soon',
        translate=True,
    )
    kingdom_coming_soon_subtitle = fields.Text(
        string='Coming Soon Subtitle',
        default='We are preparing something special. Stay tuned!',
        translate=True,
    )
    kingdom_coming_soon_launch_datetime = fields.Datetime(
        string='Launch Date',
        help='Countdown ends at this date/time (stored in UTC).',
    )
    kingdom_coming_soon_show_countdown = fields.Boolean(
        string='Show Countdown',
        default=True,
    )
    kingdom_coming_soon_bg_image = fields.Image(
        string='Background Image',
        max_width=2560,
        max_height=1440,
    )
    kingdom_coming_soon_show_admin_login = fields.Boolean(
        string='Show Admin Login Link',
        default=True,
        help='Show a “Login as Admin” link on the Coming Soon page.',
    )
    kingdom_coming_soon_login_show_header_footer = fields.Boolean(
        string='Login Page Header & Footer',
        default=False,
        help='When enabled, /web/login keeps the website header and footer. '
             'When disabled, the login page is shown without header/footer.',
    )

    def kingdom_coming_soon_countdown_end_ms(self):
        """UTC epoch ms for the Coming Soon countdown JS."""
        self.ensure_one()
        if not self.kingdom_coming_soon_launch_datetime:
            return 0
        return int(self.kingdom_coming_soon_launch_datetime.timestamp() * 1000)

    def kingdom_coming_soon_countdown_iso(self):
        """ISO string in visitor timezone for data-deal-countdown."""
        self.ensure_one()
        if not self.kingdom_coming_soon_launch_datetime:
            return ''
        dt_local = fields.Datetime.context_timestamp(
            self, self.kingdom_coming_soon_launch_datetime
        )
        return dt_local.isoformat()

    def kingdom_coming_soon_bg_url(self):
        self.ensure_one()
        if self.kingdom_coming_soon_bg_image:
            return '/web/image/website/%s/kingdom_coming_soon_bg_image' % self.id
        return '/theme_kingdom/static/src/images/cover.webp'

    def action_preview_coming_soon(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/coming-soon',
            'target': 'new',
        }
