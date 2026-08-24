# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

# Deliberately small and conservative — the goal is only to skip pure
# noise ("by the", "for") so the review list stays signal, not to do real
# NLP stopword filtering.
_STOPWORDS = {
    'a', 'an', 'the', 'by', 'of', 'in', 'on', 'for', 'to', 'and', 'or',
    'this', 'that', 'with', 'is', 'are', 'me', 'my', 'show', 'give',
    'what', 'please', 'get',
}


class AiDashboardUnmatchedPhrase(models.Model):
    """Telemetry only. Rows are written from the low-confidence branch of
    SmartKpiDashboardController.generate() so admins have a reviewable
    list of prompts the local parser couldn't confidently resolve —
    turning a recurring miss into new vocabulary (via action_create_synonym)
    is the only live effect a row here ever has.
    """
    _name = 'ai.dashboard.unmatched_phrase'
    _description = 'Smart KPI Dashboard — Unmatched Prompt Phrase'
    _order = 'hit_count desc, last_seen desc'

    phrase = fields.Char(required=True, index=True)
    hit_count = fields.Integer(default=1, required=True)
    last_seen = fields.Datetime(default=fields.Datetime.now, required=True)
    candidate_model = fields.Many2one(
        'ir.model', ondelete='set null',
        help="Model the parser DID resolve, if any, at the moment this "
             "leftover text couldn't be. Empty means the prompt didn't "
             "resolve a model either.")
    state = fields.Selection([
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    ], default='new', required=True, index=True)

    @api.model
    def _is_noise(self, phrase):
        words = phrase.split()
        if len(phrase) < 2 or not words:
            return True
        return all(w in _STOPWORDS for w in words)

    @api.model
    def log_unmatched(self, phrase, candidate_model_name=None):
        """Upsert one telemetry row. Bumps hit_count/last_seen on an
        existing 'new' row for the same normalized phrase instead of
        creating a duplicate every time the same miss recurs. Callers are
        expected to wrap this in their own try/except (see
        controllers/main.py) — kept free of any of that defensiveness
        itself so what it does stays easy to audit.
        """
        phrase = (phrase or '').strip().lower()
        if self._is_noise(phrase):
            return self.browse()

        model_id = False
        if candidate_model_name:
            model = self.env['ir.model'].sudo().search(
                [('model', '=', candidate_model_name)], limit=1)
            model_id = model.id if model else False

        existing = self.sudo().search(
            [('phrase', '=', phrase), ('state', '=', 'new')], limit=1)
        if existing:
            existing.write({
                'hit_count': existing.hit_count + 1,
                'last_seen': fields.Datetime.now(),
            })
            return existing

        return self.sudo().create({
            'phrase': phrase,
            'candidate_model': model_id,
            'hit_count': 1,
            'last_seen': fields.Datetime.now(),
        })

    def action_dismiss(self):
        self.write({'state': 'dismissed'})

    def action_create_synonym(self):
        """Manual path: pre-fill a synonym form, leave slot_type/value/
        model to the admin. Pure UI convenience — creating the synonym
        itself still goes through the normal ai.dashboard.synonym form,
        no shortcut around any validation.
        """
        self.ensure_one()
        self.state = 'reviewed'
        return {
            'type': 'ir.actions.act_window',
            'name': _("New Synonym"),
            'res_model': 'ai.dashboard.synonym',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_phrase': self.phrase,
                'default_model_id': self.candidate_model.id if self.candidate_model else False,
            },
        }
