from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class EinvoiceArchiveCommon(AccountTestInvoicingCommon):
    """Reuses Odoo core's chart-of-accounts/journal/product test fixtures
    (partner_a, product_a, init_invoice(...)) instead of hand-rolling a
    minimal chart -- see odoo/addons/account/tests/common.py.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The test user needs real access to the archive/audit-log/wizard
        # models -- these tests exercise the module's own logic, not its
        # access-control layer.
        cls.env.user.group_ids |= cls.env.ref('bs_einvoice_archive.group_einvoice_archive_admin')
