def post_init_hook(env):
    """Defensive backfill for crm.lead rows that pre-date this module.

    `category` on crm.lost.reason is `required=True` with a field-level
    default, so Odoo both backfills every pre-existing row and adds a
    NOT NULL constraint when the column is created - a reason without a
    category cannot exist after install, verified empirically (a raw SQL
    UPDATE ... SET category = NULL is rejected by the DB itself).

    `lost_reason_category` on crm.lead has no such constraint (it's a
    plain related+stored Selection, correctly blank for reasonless
    leads), so this hook re-asserts it for any already-lost lead that
    has a lost_reason_id but whose stored value wasn't computed - e.g.
    a row inserted by a raw SQL/bulk import that bypassed the ORM.
    """
    stale_leads = env['crm.lead'].with_context(active_test=False).search([
        ('lost_reason_id', '!=', False),
        ('lost_reason_category', '=', False),
    ])
    for lead in stale_leads:
        lead.lost_reason_category = lead.lost_reason_id.category
