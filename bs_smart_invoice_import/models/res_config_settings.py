from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Only base_url + api_key are required to consider the LLM "configured"
    # (see QuickPasteWizard._get_llm_config) -- these are the two things
    # every OpenAI-compatible provider needs. 'model' is deliberately
    # optional: some gateways route by API key/base URL alone and don't
    # want a model name, so it's never required or defaulted here.
    quick_paste_llm_base_url = fields.Char(
        string="LLM API Base URL",
        config_parameter='bs_smart_invoice_import.llm_base_url',
        help="OpenAI-compatible API base URL, e.g. https://api.openai.com/v1 "
             "-- also works with OpenAI-compatible gateways/self-hosted "
             "servers (Groq, OpenRouter, Azure OpenAI, Ollama, vLLM, ...).",
    )
    quick_paste_llm_api_key = fields.Char(
        string="LLM API Key",
        config_parameter='bs_smart_invoice_import.llm_api_key',
        help="Sent as a Bearer token.",
    )
    quick_paste_llm_model = fields.Char(
        string="LLM Model (optional)",
        config_parameter='bs_smart_invoice_import.llm_model',
        help="Model name as expected by the API, e.g. gpt-4o-mini or "
             "llama-3.2-11b-vision-preview. Leave empty if your endpoint "
             "doesn't need one -- it's only included in the request when set.",
    )
    quick_paste_llm_daily_limit = fields.Integer(
        string="Max Invoice Extractions per User/Day",
        config_parameter='bs_smart_invoice_import.llm_daily_limit',
        default=50,
        help="Every internal user with access to Smart Invoice Import can "
             "trigger a call against this shared, billed LLM API key -- "
             "caps how many invoice extractions one user can run per day. "
             "Set to 0 to disable the limit.",
    )
