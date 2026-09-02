import re
import unicodedata

from lxml import etree
from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Small, explicit blocklist: internal metadata/self models a field should never be added
# to. Kept deliberately short per spec section 7.1 -- broad "ir.*" exclusion would also
# hide legitimate business models many integrations extend (e.g. ir.attachment, ir.cron).
MODEL_BLOCKLIST = [
    'ir.model', 'ir.model.fields', 'ir.model.fields.selection', 'ir.model.data',
    'ir.model.constraint', 'ir.model.relation', 'ir.ui.view', 'ir.ui.menu',
    'ir.actions.server', 'ir.actions.act_window', 'base.automation',
    'ir.module.module', 'bs.addfield.registry', 'bs.addfield.wizard',
    'bs.addfield.remove.wizard',
]

FIELD_TYPES_AUTOMATABLE = ('char', 'integer', 'float', 'date', 'datetime', 'boolean', 'selection')


class BsAddfieldWizard(models.TransientModel):
    _name = 'bs.addfield.wizard'
    _description = 'Add a Field Wizard'

    state = fields.Selection([
        ('model', 'Pick Model'),
        ('field', 'Define Field'),
        ('preview', 'Preview'),
        ('done', 'Done'),
    ], default='model', required=True)

    # Step 1
    target_model_id = fields.Many2one(
        'ir.model', string='Model',
        domain=[('abstract', '=', False), ('transient', '=', False),
                ('model', 'not in', MODEL_BLOCKLIST)])

    # Step 2
    field_type = fields.Selection([
        ('char', 'Text'),
        ('integer', 'Number (Whole)'),
        ('float', 'Number (Decimal)'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('boolean', 'Yes/No'),
        ('selection', 'Selection'),
        ('many2one', 'Many2one'),
    ], default='char')
    field_label = fields.Char(string='Field Label')
    field_required = fields.Boolean(string='Required')
    selection_options = fields.Text(
        string='Selection Options', help='One option per line.')
    relation_model_id = fields.Many2one(
        'ir.model', string='Related Model',
        domain=[('abstract', '=', False), ('transient', '=', False),
                ('model', 'not in', MODEL_BLOCKLIST)])
    label_warning = fields.Char(readonly=True)

    # Optional automation
    add_automation = fields.Boolean(string='Notify someone when this changes')
    automation_trigger_value = fields.Char(string='When the field is set to')
    automation_notify_user_id = fields.Many2one('res.users', string='Notify')
    automation_message = fields.Text(string='Message')

    # Preview (computed on transition to 'preview')
    placement_group = fields.Char(readonly=True)
    placement_note = fields.Char(readonly=True)

    # Result
    result_registry_id = fields.Many2one('bs.addfield.registry', readonly=True)

    # ---------------------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------------------
    def _reopen_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add a Field'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_next_to_field(self):
        self.ensure_one()
        if not self.target_model_id:
            raise UserError(_('Choose a model first.'))
        self.state = 'field'
        return self._reopen_action()

    def action_back_to_model(self):
        self.state = 'model'
        return self._reopen_action()

    def action_back_to_field(self):
        self.state = 'field'
        return self._reopen_action()

    def action_next_to_preview(self):
        self.ensure_one()
        self._validate_field_definition()
        target_model = self.target_model_id.model
        group_name, _expr, _position, is_fallback = self._detect_placement(target_model)
        self.placement_group = group_name or ''
        self.placement_note = (
            _('No named group was detected on this model\'s form -- the field will be '
              'appended to the end of the form.')
            if is_fallback else
            _('Will be added to the "%s" group.', group_name)
        )
        self.state = 'preview'
        return self._reopen_action()

    def action_confirm(self):
        self.ensure_one()
        self._validate_field_definition()
        target_model = self.target_model_id.model
        with self.env.cr.savepoint():
            field_name = self._generate_field_name(target_model)
            field = self._create_field(target_model, field_name)
            _group_name, expr, position, _is_fallback = self._detect_placement(target_model)
            view = self._create_view(target_model, field_name, expr, position)
            automation = self.env['base.automation']
            if self.add_automation:
                automation = self._create_automation(target_model, field_name)
            registry = self.env['bs.addfield.registry'].create({
                'target_model_id': self.target_model_id.id,
                'field_id': field.id,
                'view_id': view.id,
                'automation_id': automation.id if automation else False,
            })
        self.result_registry_id = registry.id
        self.state = 'done'
        return self._reopen_action()

    def action_view_target_model(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.target_model_id.name,
            'res_model': self.target_model_id.model,
            'view_mode': 'list,form',
        }

    # ---------------------------------------------------------------------
    # Validation (spec section 9 edge cases)
    # ---------------------------------------------------------------------
    def _validate_field_definition(self):
        self.ensure_one()
        if not self.target_model_id:
            raise UserError(_('Choose a model first.'))
        if not self.field_label or not self.field_label.strip():
            raise UserError(_('Enter a field label.'))
        target_model = self.target_model_id.model
        # Edge case: label collides with an existing field's label (warn, don't block).
        self._check_label_collision(target_model)
        # Edge case: duplicate selection options.
        if self.field_type == 'selection':
            self._parse_selection_options()
        # Edge case: many2one target the current users can't read.
        if self.field_type == 'many2one':
            self._check_relation_accessible()
        if self.add_automation:
            if self.field_type not in FIELD_TYPES_AUTOMATABLE:
                raise UserError(_('Automation notifications are not supported for this field type.'))
            if not self.automation_notify_user_id:
                raise UserError(_('Choose who should be notified.'))
            # Edge case: automation trigger value type mismatch.
            self._validate_automation_trigger_value()

    def _check_label_collision(self, target_model):
        existing = self.env['ir.model.fields'].search([
            ('model', '=', target_model),
            ('field_description', '=ilike', self.field_label.strip()),
        ], limit=1)
        self.label_warning = (
            _('A field labeled "%(label)s" (%(name)s) already exists on this model.',
              label=existing.field_description, name=existing.name)
            if existing else False
        )

    def _parse_selection_options(self):
        lines = [line.strip() for line in (self.selection_options or '').split('\n') if line.strip()]
        if not lines:
            raise UserError(_('Enter at least one selection option, one per line.'))
        seen = set()
        for line in lines:
            key = line.lower()
            if key in seen:
                raise UserError(_('Duplicate selection option: "%s". Each option must be unique.', line))
            seen.add(key)
        return lines

    def _check_relation_accessible(self):
        if not self.relation_model_id:
            raise UserError(_('Choose a target model for the Many2one field.'))
        accessible = self.env['ir.model.access'].sudo().search_count([
            ('model_id', '=', self.relation_model_id.id), ('perm_read', '=', True),
        ], limit=1)
        if not accessible:
            raise UserError(_(
                'Users don\'t have read access to "%s". Add an access rule for this model '
                'before linking a field to it.', self.relation_model_id.name))

    def _validate_automation_trigger_value(self):
        value = (self.automation_trigger_value or '').strip()
        if not value:
            raise UserError(_('Enter the value that should trigger the notification.'))
        ftype = self.field_type
        if ftype == 'boolean':
            if value.lower() not in ('true', 'false'):
                raise UserError(_('For a Yes/No field, the trigger value must be "true" or "false".'))
        elif ftype == 'integer':
            try:
                int(value)
            except ValueError:
                raise UserError(_('For a Number (Whole) field, the trigger value must be a whole number.'))
        elif ftype == 'float':
            try:
                float(value)
            except ValueError:
                raise UserError(_('For a Number (Decimal) field, the trigger value must be numeric.'))
        elif ftype == 'date':
            try:
                if not fields.Date.to_date(value):
                    raise ValueError()
            except ValueError:
                raise UserError(_('For a Date field, the trigger value must be a valid date (YYYY-MM-DD).'))
        elif ftype == 'datetime':
            try:
                if not fields.Datetime.to_datetime(value):
                    raise ValueError()
            except ValueError:
                raise UserError(_(
                    'For a Datetime field, the trigger value must be a valid datetime '
                    '(YYYY-MM-DD HH:MM:SS).'))
        elif ftype == 'selection':
            options = self._parse_selection_options()
            if value.lower() not in [o.lower() for o in options]:
                raise UserError(_('The trigger value must match one of the selection options.'))

    # ---------------------------------------------------------------------
    # Creation helpers
    # ---------------------------------------------------------------------
    @api.model
    def _slugify(self, text):
        text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()
        return text or 'field'

    def _generate_field_name(self, target_model):
        base = ('x_studio_' + self._slugify(self.field_label))[:54]
        name = base
        IrModelFields = self.env['ir.model.fields']
        i = 1
        while IrModelFields.search_count([('model', '=', target_model), ('name', '=', name)], limit=1):
            i += 1
            name = f'{base}_{i}'
        return name

    def _build_selection_slugs(self, options):
        """Deterministic label -> unique value-key pairs, in given order."""
        seen = set()
        result = []
        for i, opt in enumerate(options):
            base = self._slugify(opt) or f'option_{i}'
            slug = base
            n = 1
            while slug in seen:
                n += 1
                slug = f'{base}_{n}'
            seen.add(slug)
            result.append((slug, opt))
        return result

    def _create_field(self, target_model, field_name):
        vals = {
            'name': field_name,
            'model_id': self.target_model_id.id,
            'field_description': self.field_label.strip(),
            'ttype': self.field_type,
            'required': self.field_required,
        }
        if self.field_type == 'many2one':
            vals['relation'] = self.relation_model_id.model
        if self.field_type == 'selection':
            pairs = self._build_selection_slugs(self._parse_selection_options())
            vals['selection_ids'] = [
                (0, 0, {'value': slug, 'name': label, 'sequence': i})
                for i, (slug, label) in enumerate(pairs)
            ]
        return self.env['ir.model.fields'].create(vals)

    def _detect_placement(self, target_model):
        """Return (group_name_or_False, xpath_expr, position, is_fallback)."""
        arch = self.env[target_model].get_view(view_type='form')['arch']
        return self._detect_placement_from_arch(arch)

    @api.model
    def _detect_placement_from_arch(self, arch):
        """Pure arch-parsing half of placement detection, kept separate so it can be
        unit-tested without a live model/view. Returns
        (group_name_or_False, xpath_expr, position, is_fallback)."""
        tree = etree.fromstring(arch.encode('utf-8') if isinstance(arch, str) else arch)
        groups = tree.xpath('//group[@name]')
        if groups:
            name = groups[0].get('name')
            return name, f"//group[@name='{name}']", 'inside', False
        if tree.xpath('//sheet'):
            return False, '//sheet', 'inside', True
        return False, '//form', 'inside', True

    def _get_base_form_view(self, target_model):
        View = self.env['ir.ui.view'].sudo()
        view = View.search([
            ('model', '=', target_model), ('type', '=', 'form'), ('inherit_id', '=', False),
        ], limit=1)
        if not view:
            view = View.search([
                ('model', '=', target_model), ('type', '=', 'form'), ('mode', '=', 'primary'),
            ], order='priority', limit=1)
        if not view:
            raise UserError(_('No form view was found for this model, so a field cannot be placed on it.'))
        return view

    def _create_view(self, target_model, field_name, expr, position):
        base_view = self._get_base_form_view(target_model)
        arch = f'<xpath expr="{expr}" position="{position}"><field name="{field_name}"/></xpath>'
        return self.env['ir.ui.view'].create({
            'name': f'{target_model}.addfield.{field_name}',
            'model': target_model,
            'inherit_id': base_view.id,
            'mode': 'extension',
            'arch': arch,
        })

    def _create_automation(self, target_model, field_name):
        template = self.env['mail.template'].create({
            'name': _('Add-a-Field Notify: %s', self.field_label),
            'model_id': self.target_model_id.id,
            'subject': _('%s was updated', self.field_label),
            'body_html': f'<p>{self.automation_message or ""}</p>',
            'partner_to': str(self.automation_notify_user_id.partner_id.id),
            'auto_delete': True,
        })
        value = self.automation_trigger_value.strip()
        if self.field_type == 'boolean':
            py_value = value.lower() == 'true'
        elif self.field_type == 'integer':
            py_value = int(value)
        elif self.field_type == 'float':
            py_value = float(value)
        elif self.field_type == 'selection':
            pairs = self._build_selection_slugs(self._parse_selection_options())
            py_value = next(slug for slug, label in pairs if label.lower() == value.lower())
        else:
            py_value = value

        automation = self.env['base.automation'].create({
            'name': _('Add-a-Field: notify on %s', self.field_label),
            'model_id': self.target_model_id.id,
            'trigger': 'on_create_or_write',
            'action_server_ids': [(0, 0, {
                'name': _('Notify %s', self.automation_notify_user_id.name),
                'model_id': self.target_model_id.id,
                'usage': 'base_automation',
                'state': 'mail_post',
                'mail_post_method': 'email',
                'template_id': template.id,
            })],
        })
        # Written after create rather than inside the create() vals: filter_domain is a
        # stored compute field whose compute can override create-time values for triggers
        # it manages -- an explicit write() afterwards is unambiguous. See context.md.
        automation.write({'filter_domain': repr([(field_name, '=', py_value)])})
        return automation
