from . import models
from . import controllers


def uninstall_hook(env):
    """Remove the fuzzy-match ir.config_parameter created via res.config.
    settings — it isn't tied to a module XML-ID (the config_parameter
    mechanism never generates one), so without this it would silently
    survive an Uninstall.
    """
    env['ir.config_parameter'].sudo().search([
        ('key', '=', 'bs_smart_kpi_dashboard.fuzzy_match_enabled'),
    ]).unlink()
