# -*- coding: utf-8 -*-
import logging
from datetime import timedelta

from odoo import fields, models, api, _

_logger = logging.getLogger(__name__)

# Deliberately small and conservative — the goal is only to skip pure
# noise ("by the", "for") so the review list stays signal, not to do real
# NLP stopword filtering.
_STOPWORDS = {
    'a', 'an', 'the', 'by', 'of', 'in', 'on', 'for', 'to', 'and', 'or',
    'this', 'that', 'with', 'is', 'are', 'me', 'my', 'show', 'give',
    'what', 'please', 'get',
}


class AiDashboardUnmatchedPhrase(models.Model):
    """Telemetry only. Written to from one place — the low-confidence
    branch of SmartKpiDashboardController.generate() — and read from
    nowhere in the live query path. KpiPromptParser never touches this
    model and _validate_spec() never touches this model; a row existing
    here has zero effect on what any prompt can query until an admin
    manually turns it into an ai.dashboard.synonym row.
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

    # log_unmatched() is reachable by any authenticated user (it's called
    # from the low-confidence branch of every /generate request) and is
    # unthrottled per-user — a single user hammering the ask bar with
    # never-seen phrases can grow this table indefinitely. hit_count
    # already de-dupes *identical* repeats, but distinct nonsense phrases
    # each still get their own row forever. _cleanup(), run from the same
    # daily cron as vocabulary discovery, bounds that growth instead of
    # relying on an admin to notice and prune manually.
    _CLEANUP_DISMISSED_AFTER_DAYS = 90
    _CLEANUP_MAX_NEW_ROWS = 2000

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

    @api.model
    def _cleanup(self):
        """Bound the table's growth — see class-level comment above.
        Safe to call repeatedly (idempotent) and from a cron.
        """
        cutoff = fields.Datetime.now() - timedelta(days=self._CLEANUP_DISMISSED_AFTER_DAYS)

        stale_dismissed = self.sudo().search([
            ('state', '=', 'dismissed'),
            ('last_seen', '<', cutoff),
        ])
        removed = len(stale_dismissed)
        stale_dismissed.unlink()

        new_rows = self.sudo().search(
            [('state', '=', 'new')], order='hit_count desc, last_seen desc')
        overflow = new_rows[self._CLEANUP_MAX_NEW_ROWS:]
        removed += len(overflow)
        overflow.unlink()

        if removed:
            _logger.info(
                "Smart KPI Dashboard: cleaned up %d stale unmatched-phrase "
                "row(s) (%d dismissed >%dd old, %d 'new' rows beyond the "
                "%d-row cap).", removed, len(stale_dismissed),
                self._CLEANUP_DISMISSED_AFTER_DAYS, len(overflow),
                self._CLEANUP_MAX_NEW_ROWS)

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
