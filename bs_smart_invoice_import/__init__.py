import shutil

from . import wizard
from . import models


def uninstall_hook(env):
    """Remove config parameters set at runtime via ir.config_parameter (not
    owned XML data, so module uninstall wouldn't otherwise clean them up)
    and the local fastembed model cache, if one was ever downloaded.
    """
    ICP = env['ir.config_parameter'].sudo()
    ICP.search([('key', 'like', 'bs_smart_invoice_import.%')]).unlink()

    from .wizard import embedding_matcher
    shutil.rmtree(embedding_matcher._cache_dir(), ignore_errors=True)
