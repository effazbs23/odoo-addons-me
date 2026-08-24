from odoo import api, fields, models

from . import llm_client


class QuickPasteLLMPromptWizard(models.TransientModel):
    _name = 'quick.paste.llm.prompt.wizard'
    _description = "Edit Invoice Extraction Prompt"

    prompt = fields.Text(string="Extraction Prompt", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'prompt' in fields_list and not res.get('prompt'):
            res['prompt'] = self.env['ir.config_parameter'].sudo().get_param(
                'bs_smart_invoice_import.llm_prompt') or llm_client.DEFAULT_PROMPT
        return res

    def action_save(self):
        self.ensure_one()
        self.env['ir.config_parameter'].sudo().set_param(
            'bs_smart_invoice_import.llm_prompt', self.prompt or llm_client.DEFAULT_PROMPT,
        )
        return {'type': 'ir.actions.act_window_close'}
