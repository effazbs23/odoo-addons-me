import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR_PATTERN = re.compile(r"^#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})$")


class CustomStatusbarStateConfig(models.Model):
    """A single statusbar state (model + field + value) and its color."""

    _name = "custom.statusbar.state.config"
    _description = "Custom Statusbar Color State Configuration"
    _order = "model_name, field_name, sequence"

    module_config_id = fields.Many2one(
        "custom.statusbar.module.config",
        required=True,
        ondelete="cascade",
        index=True,
    )
    model_id = fields.Many2one("ir.model", required=True, ondelete="cascade")
    model_name = fields.Char(related="model_id.model", store=True)
    field_name = fields.Char(required=True)
    state_value = fields.Char(required=True)
    state_label = fields.Char(required=True)
    sequence = fields.Integer(
        help="Position of this state in the field's actual selection order, "
        "so the visual statusbar preview matches the real workflow order.",
    )
    default_color = fields.Char(
        help="Hex color applied to this state's statusbar button when the "
        "record is NOT currently in this state (i.e. it's shown as a past "
        "or upcoming step). Left empty until explicitly set.",
    )
    in_state_color = fields.Char(
        help="Hex color applied to this state's statusbar button when the "
        "record IS currently in this state. Left empty until explicitly set.",
    )
    enabled = fields.Boolean(
        help="Apply the configured color(s) to this specific state.",
    )

    _state_uniq = models.Constraint(
        'unique(module_config_id, model_id, field_name, state_value)',
        "This state is already configured for this module.",
    )

    @api.constrains("default_color", "in_state_color")
    def _check_color_format(self):
        """Reject anything that isn't a valid hex color.

        The color picker widget already enforces this client-side, but
        these fields are plain Char columns underneath - any write that
        bypasses the widget (import, RPC, a future integration) could
        otherwise put arbitrary text into a value that's concatenated
        straight into an inline `style` attribute applied globally to
        every statusbar in the system (see custom_statusbar.js).
        """
        for state in self:
            for field_name in ("default_color", "in_state_color"):
                value = state[field_name]
                if value and not HEX_COLOR_PATTERN.match(value):
                    raise ValidationError(
                        _(
                            "%(field)s must be a valid hex color like #FF0000 or #F00 "
                            "(got %(value)r).",
                            field=state._fields[field_name].string,
                            value=value,
                        )
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._notify_color_update()
        return records

    def write(self, vals):
        result = super().write(vals)
        self._notify_color_update()
        return result

    def _notify_color_update(self):
        """Push a bus notification so open sessions refresh their color cache."""
        self.env["bus.bus"]._sendone(
            "custom_statusbar", "custom_statusbar.colors_updated", {}
        )
