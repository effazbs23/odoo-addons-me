from datetime import timedelta

from odoo import api, fields, models
from odoo.tools import date_utils

from .crm_lost_reason import CATEGORY_SELECTION

CATEGORY_LABELS = dict(CATEGORY_SELECTION)

# Anchors the frontend's date-range dropdown to a server-computed window,
# rather than trusting client-side dates (avoids timezone drift between
# browser and server). 'all' has no previous-period comparison.
DATE_RANGE_DAYS = {
    'last_7': 7,
    'last_30': 30,
    'last_90': 90,
}
DATE_RANGE_CALENDAR = {'this_month': 'month', 'this_quarter': 'quarter', 'this_year': 'year'}


def _pct_change(current, previous):
    """None when there's nothing to compare against (previous period had
    zero) - the frontend renders that as no arrow rather than a
    misleading +inf%/0%."""
    if not previous:
        return None
    return round((current - previous) / previous * 100.0, 1)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    lost_note = fields.Text(
        string='Lost Note',
        help='Optional free-text context captured when the lead was marked '
             'lost (e.g. "client went with competitor after our demo"). '
             'For drill-down reading only, not used for aggregation.',
    )
    # related + store=True so pivot/graph views can group by category
    # without a runtime join; automatically recomputed whenever
    # lost_reason_id changes (including being cleared on reactivation).
    lost_reason_category = fields.Selection(
        related='lost_reason_id.category',
        string='Lost Reason Category',
        store=True,
        readonly=True,
    )

    def action_unarchive(self):
        """Reopening a lost lead clears lost_note the same way core already
        clears lost_reason_id, so the dashboard doesn't keep counting a
        since-reopened lead under its old lost reason/note.
        lost_reason_category clears itself automatically since it's a
        related field on lost_reason_id."""
        activated = self.filtered(lambda rec: not rec.active)
        res = super().action_unarchive()
        if activated:
            activated.write({'lost_note': False})
        return res

    @api.model
    def get_win_rate(self, domain=None):
        """Won/(won+lost) percentage for the given domain, or False when
        there are no won or lost leads in it ("No data" case) — never
        divides by zero or returns a misleading 0%/100%."""
        domain = (domain or []) + [('won_status', 'in', ('won', 'lost'))]
        groups = self.with_context(active_test=False)._read_group(
            domain, ['won_status'], ['__count'],
        )
        counts = {won_status: count for won_status, count in groups}
        won = counts.get('won', 0)
        lost = counts.get('lost', 0)
        total = won + lost
        if not total:
            return False
        return (won / total) * 100.0

    @api.model
    def _dashboard_bounds(self, date_range):
        """(date_from, date_to, prev_from, prev_to), date_to/prev_to
        exclusive. All None for 'all' - no lower bound, so no
        previous-period comparison is possible either."""
        today = fields.Date.context_today(self)
        if date_range in DATE_RANGE_DAYS:
            days = DATE_RANGE_DAYS[date_range]
            date_to = today + timedelta(days=1)
            date_from = date_to - timedelta(days=days)
            prev_to, prev_from = date_from, date_from - timedelta(days=days)
        elif date_range in DATE_RANGE_CALENDAR:
            granularity = DATE_RANGE_CALENDAR[date_range]
            date_from = date_utils.start_of(today, granularity)
            date_to = date_utils.end_of(today, granularity) + timedelta(days=1)
            prev_from = date_utils.start_of(date_from - timedelta(days=1), granularity)
            prev_to = date_from
        else:
            return None, None, None, None
        return date_from, date_to, prev_from, prev_to

    @api.model
    def get_win_rate_dashboard_filters(self):
        """Teams/salespeople to populate the dashboard's filter dropdowns,
        scoped to whoever actually has leads - no point offering a filter
        that would always return "No data"."""
        leads = self.with_context(active_test=False).search([('type', '=', 'opportunity'), ('team_id', '!=', False)])
        teams = leads.mapped('team_id')
        users = leads.mapped('user_id')
        return {
            'teams': [{'id': t.id, 'name': t.name} for t in teams.sorted('name')],
            'salespeople': [{'id': u.id, 'name': u.name} for u in users.sorted('name')],
        }

    @api.model
    def get_win_rate_dashboard_data(self, date_range='last_30', team_id=None, user_id=None):
        """Aggregated data for the Win Rate Dashboard client action: KPI
        cards (with period-over-period deltas), lost-reason breakdown,
        win rate by salesperson, a stage funnel, and leads by source.
        Every number here comes from read_group - no custom SQL."""
        date_from, date_to, prev_from, prev_to = self._dashboard_bounds(date_range)

        # Scoped to opportunities, matching native CRM's own pipeline/win-rate
        # reporting - raw (not-yet-qualified) leads would otherwise inflate
        # the funnel and source counts before they ever entered the pipeline.
        base_domain = [('type', '=', 'opportunity')]
        if team_id:
            base_domain.append(('team_id', '=', team_id))
        if user_id:
            base_domain.append(('user_id', '=', user_id))

        def period_domain(frm, to):
            domain = list(base_domain)
            if frm:
                domain.append(('create_date', '>=', frm))
            if to:
                domain.append(('create_date', '<', to))
            return domain

        def won_lost_counts(domain):
            groups = self.with_context(active_test=False)._read_group(
                domain + [('won_status', 'in', ('won', 'lost'))],
                ['won_status'], ['__count'],
            )
            counts = {status: count for status, count in groups}
            return counts.get('won', 0), counts.get('lost', 0)

        cur_domain = period_domain(date_from, date_to)
        won, lost = won_lost_counts(cur_domain)
        total = won + lost
        win_rate = (won / total * 100.0) if total else False

        win_rate_delta = won_delta = lost_delta = None
        if date_from:
            prev_won, prev_lost = won_lost_counts(period_domain(prev_from, prev_to))
            prev_total = prev_won + prev_lost
            prev_win_rate = (prev_won / prev_total * 100.0) if prev_total else None
            if prev_win_rate is not None and win_rate is not False:
                win_rate_delta = round(win_rate - prev_win_rate, 1)
            won_delta = _pct_change(won, prev_won)
            lost_delta = _pct_change(lost, prev_lost)

        # Lost-reason breakdown: lost leads only. category is undefined
        # for won/pending leads, so mixing them in would make the
        # breakdown meaningless - same reasoning as the native Loss
        # Reasons pivot/graph in crm_lead_dashboard_views.xml.
        lost_domain = cur_domain + [('active', '=', False), ('won_status', '=', 'lost')]
        reason_groups = self.with_context(active_test=False)._read_group(
            lost_domain, ['lost_reason_category'], ['__count'],
        )
        lost_reasons = sorted((
            {
                'category': category or 'none',
                'label': CATEGORY_LABELS.get(category, 'No Reason'),
                'count': count,
                'pct': round(count / lost * 100.0, 1) if lost else 0.0,
            }
            for category, count in reason_groups
        ), key=lambda r: r['count'], reverse=True)

        # Win rate by salesperson, best first.
        sp_groups = self.with_context(active_test=False)._read_group(
            cur_domain + [('won_status', 'in', ('won', 'lost'))],
            ['user_id', 'won_status'], ['__count'],
        )
        sp_counts = {}
        for user, status, count in sp_groups:
            uid = user.id if user else 0
            entry = sp_counts.setdefault(uid, {'name': user.name if user else 'Unassigned', 'won': 0, 'lost': 0})
            entry[status] = count
        salespeople = sorted((
            {
                'id': uid,
                'name': data['name'],
                'win_rate': round(data['won'] / (data['won'] + data['lost']) * 100.0, 1),
            }
            for uid, data in sp_counts.items() if data['won'] + data['lost']
        ), key=lambda s: s['win_rate'], reverse=True)[:8]

        # Stage funnel: cumulative count of leads that reached at least
        # this stage (by native stage sequence), among all leads in the
        # period regardless of outcome - crm.lead doesn't keep a full
        # stage-history log, so "current stage >= this one" is the
        # standard proxy for "passed through this far". Won/Lost are
        # reported as their own rows from won_status directly, not by
        # stage, since a won lead's stage_id is just whichever won-stage
        # it landed in.
        all_domain = cur_domain
        stages = self.env['crm.stage'].search([('is_won', '=', False)], order='sequence')
        funnel = []
        for stage in stages:
            count = self.with_context(active_test=False).search_count(
                all_domain + [('stage_id.sequence', '>=', stage.sequence)]
            )
            funnel.append({'label': stage.name, 'count': count})
        for i, row in enumerate(funnel):
            nxt = funnel[i + 1]['count'] if i + 1 < len(funnel) else None
            row['dropoff_pct'] = round((row['count'] - nxt) / row['count'] * 100.0, 1) if nxt is not None and row['count'] else None
        funnel.append({'label': 'Won', 'count': won, 'dropoff_pct': None})
        funnel.append({'label': 'Lost', 'count': lost, 'dropoff_pct': None})

        # Leads by source: top 5 + an "Other" bucket, all lead types,
        # any outcome - this is about lead volume, not win/loss.
        source_groups = self.with_context(active_test=False)._read_group(
            all_domain, ['source_id'], ['__count'],
        )
        sources = sorted((
            {'label': source.name if source else 'Direct', 'count': count}
            for source, count in source_groups
        ), key=lambda s: s['count'], reverse=True)
        total_leads = sum(s['count'] for s in sources)
        top_sources, rest = sources[:5], sources[5:]
        if rest:
            top_sources.append({'label': 'Other', 'count': sum(s['count'] for s in rest)})
        for s in top_sources:
            s['pct'] = round(s['count'] / total_leads * 100.0, 1) if total_leads else 0.0

        return {
            'win_rate': win_rate,
            'win_rate_delta': win_rate_delta,
            'won': won,
            'won_delta': won_delta,
            'lost': lost,
            'lost_delta': lost_delta,
            'lost_reasons': lost_reasons,
            'salespeople': salespeople,
            'funnel': funnel,
            'sources': top_sources,
        }
