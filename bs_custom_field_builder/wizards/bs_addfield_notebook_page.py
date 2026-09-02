from odoo import fields, models


class BsAddfieldNotebookPage(models.TransientModel):
    """One row per real notebook tab detected on the chosen model's form, plus an
    "End of form" placeholder -- populated fresh by bs.addfield.wizard.action_next_to_field
    each time a model is picked. Exists so "Add to Tab" can be a genuine Many2one dropdown:
    a Many2one's options are fetched live via RPC when the dropdown opens, unlike a
    Selection field's, which Odoo always evaluates against an empty recordset (confirmed
    in odoo/orm/fields_selection.py's _description_selection -- `determine(selection,
    env[self.model_name])`), so a Selection field can never depend on a sibling field like
    target_model_id. See bs_addfield_wizard.py's notebook_page_id docstring.
    """
    _name = 'bs.addfield.notebook.page'
    _description = 'Add-a-Field Wizard: Available Form Tab'
    _rec_name = 'display_label'

    wizard_id = fields.Many2one('bs.addfield.wizard', required=True, ondelete='cascade')
    name = fields.Char(string='Technical Name')  # blank = "end of form"
    display_label = fields.Char(required=True)
