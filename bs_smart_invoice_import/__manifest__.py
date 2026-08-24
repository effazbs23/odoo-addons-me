{
    'name': "Smart Invoice Import",
    'summary': "Paste a raw text table of SKUs/quantities and generate order lines in one shot.",
    'description': """
Smart Invoice Import
========================
Paste a raw block of text (email, PDF export, spreadsheet copy-paste) listing
SKUs and quantities above the order line table on a Sale Order or Purchase
Order, parse it, review the matched products in a preview grid, and generate
the order lines in one shot.

The "Upload Invoice" (AI extraction) mode requires your own OpenAI-compatible
LLM API account (OpenAI, Groq, Azure OpenAI, a self-hosted server, ...),
configured under Settings. Usage of that API is billed by its provider,
separately from this module -- the plain "Paste Text" mode needs no such
account and incurs no external cost.

Optional Python packages (installed automatically if present, otherwise the
module falls back to plain string matching): `rapidfuzz` (better fuzzy
product-name matching), `fastembed` (semantic/typo-tolerant product-name
matching), `pymupdf` (PDF invoice upload support).
""",
    'version': '19.0.1.0.0',
    'category': 'Sales/Purchase',
    'author': 'ERP23',
    'website': 'https://erp-23.com',
    'support': 'erp23@brainstation-23.com',
    'license': 'OPL-1',
    'price': 9.99,
    'currency': 'USD',
    'application': False,
    'icon': '/bs_smart_invoice_import/static/description/icon.png',
    'images': ['static/description/banner.gif'],
    'depends': ['sale', 'purchase', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/quick_paste_wizard_views.xml',
        'wizard/llm_prompt_wizard_views.xml',
        'views/sale_order_views.xml',
        'views/purchase_order_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'bs_smart_invoice_import/static/src/loading_bar/loading_bar.js',
            'bs_smart_invoice_import/static/src/loading_bar/loading_bar.xml',
        ],
    },
    'uninstall_hook': 'uninstall_hook',
}
