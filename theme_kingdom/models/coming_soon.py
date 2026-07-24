# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import email_normalize


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
    kingdom_coming_soon_show_subscribe = fields.Boolean(
        string='Show Subscription Form',
        default=True,
    )
    kingdom_coming_soon_subscribe_text = fields.Char(
        string='Subscribe Placeholder',
        default='Enter your email to get notified',
        translate=True,
    )
    kingdom_coming_soon_subscribe_button = fields.Char(
        string='Subscribe Button Label',
        default='Notify Me',
        translate=True,
    )
    kingdom_coming_soon_bg_image = fields.Image(
        string='Background Image',
        max_width=2560,
        max_height=1440,
    )
    kingdom_coming_soon_subscriber_ids = fields.One2many(
        'kingdom.coming.soon.subscriber',
        'website_id',
        string='Subscribers',
    )
    kingdom_coming_soon_subscriber_count = fields.Integer(
        string='Subscriber Count',
        compute='_compute_kingdom_coming_soon_subscriber_count',
    )

    def _compute_kingdom_coming_soon_subscriber_count(self):
        Subscriber = self.env['kingdom.coming.soon.subscriber'].sudo()
        grouped = Subscriber._read_group(
            [('website_id', 'in', self.ids)],
            ['website_id'],
            ['__count'],
        )
        counts = {website.id: count for website, count in grouped}
        for website in self:
            website.kingdom_coming_soon_subscriber_count = counts.get(website.id, 0)

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

    def action_open_coming_soon_subscribers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Coming Soon Subscribers'),
            'res_model': 'kingdom.coming.soon.subscriber',
            'view_mode': 'list,form',
            'domain': [('website_id', '=', self.id)],
            'context': {'default_website_id': self.id},
        }

    def action_preview_coming_soon(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/coming-soon',
            'target': 'new',
        }


class KingdomComingSoonSubscriber(models.Model):
    _name = 'kingdom.coming.soon.subscriber'
    _description = 'Coming Soon Subscriber'
    _order = 'create_date desc, id desc'
    _rec_name = 'email'

    email = fields.Char(required=True, index=True)
    website_id = fields.Many2one(
        'website',
        required=True,
        ondelete='cascade',
        index=True,
        default=lambda self: self.env['website'].get_current_website(),
    )

    _email_website_uniq = models.Constraint(
        'unique(email, website_id)',
        'This email is already subscribed for this website.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            email = email_normalize(vals.get('email') or '')
            if not email:
                raise ValidationError(_('Please enter a valid email address.'))
            vals['email'] = email
        return super().create(vals_list)

    def write(self, vals):
        if 'email' in vals:
            email = email_normalize(vals.get('email') or '')
            if not email:
                raise ValidationError(_('Please enter a valid email address.'))
            vals = {**vals, 'email': email}
        return super().write(vals)
