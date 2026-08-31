from . import models


def _post_init_enable_simple_invoicing(env):
    """simple_invoicing_mode defaults to True on the field so it's on for
    any company created after install, but a new field's default is
    backfilled onto *existing* rows via a raw SQL UPDATE (see
    _init_column in odoo/orm/models.py), bypassing write() and therefore
    the group-membership sync on res.company.write(). Call write() once
    here so a fresh install actually enrolls each existing company's
    users into simple_invoicing_group, not just flips the field."""
    env['res.company'].search([]).write({'simple_invoicing_mode': True})
