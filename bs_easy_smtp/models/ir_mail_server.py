from odoo import models
from odoo.exceptions import UserError

# keyword -> plain-language explanation, checked in order against the lowercased
# exception message (spec section 7.4)
_ERROR_PATTERNS = [
    (('auth', 'username and password not accepted', 'invalid credentials', 'login'),
     ("Your username or password (or app password) is incorrect. If your provider requires "
      "an app password instead of your normal account password, use that instead.")),
    (('timed out', 'timeout', 'connection refused', 'name or service not known',
      'temporary failure in name resolution', 'network is unreachable'),
     ("We couldn't reach that server. Check the host and port, and make sure your network "
      "or firewall allows outgoing SMTP connections.")),
    (('ssl', 'tls', 'wrong version number', 'certificate'),
     ("The encryption setting doesn't match what this server expects. Try switching between "
      "SSL and STARTTLS.")),
    (('relay', 'access denied', 'not allowed to relay', 'sender address rejected'),
     ("The server rejected sending as this address. Double check the username matches the "
      "account you're authenticating with.")),
]


class IrMailServer(models.Model):
    _inherit = 'ir.mail_server'

    def _bs_easy_smtp_decode_error(self, message):
        """Map a raw SMTP/socket error message to a plain-language explanation.

        Shared by the Easy SMTP Setup wizard's test-send and by the native "Test
        Connection" button below, so the mapping table only lives in one place.
        Falls back to a truncated raw message so nothing is silently swallowed.
        """
        lowered = (message or '').lower()
        for keywords, explanation in _ERROR_PATTERNS:
            if any(keyword in lowered for keyword in keywords):
                return explanation
        return f"Connection test failed: {(message or '').strip()[:300]}"

    def test_smtp_connection(self, autodetect_max_email_size=False):
        try:
            return super().test_smtp_connection(autodetect_max_email_size=autodetect_max_email_size)
        except UserError as exc:
            raise UserError(self._bs_easy_smtp_decode_error(str(exc))) from exc
