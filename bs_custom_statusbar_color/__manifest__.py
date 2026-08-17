{
    "name": "Custom Statusbar Color",
    "version": "19.0.1.0.0",
    "category": "Technical",
    "summary": "Configurable per-state coloring for statusbar widgets, rule by rule",
    "description": """
Configurable Status Bar Coloring
=================================
- Create a rule: name it and pick the model whose statusbar you want to color
- Its statusbar states are discovered automatically as soon as you pick the
  model, shown as a live preview of the actual statusbar
- Assign two colors per state: one for its default (past/upcoming) look and
  one for when the record is currently in that state, using presets, a hex
  input, or a full RGB color picker
- Toggle coloring on/off per rule and per individual state
- Applies globally to every statusbar widget, no view changes required
- Reachable from the global command palette (Ctrl+K)
    """,
    "author": "ERP23",
    "website": "https://erp-23.com",
    "license": "OPL-1",
    'support': 'erp23@brainstation-23.com',
    "price": 9.99,
    "currency": "USD",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "views/module_config_views.xml",
        "views/state_config_views.xml",
        "views/menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "bs_custom_statusbar_color/static/src/css/custom_statusbar.scss",
            "bs_custom_statusbar_color/static/src/scss/color_picker_field.scss",
            "bs_custom_statusbar_color/static/src/scss/statusbar_state_editor.scss",
            "bs_custom_statusbar_color/static/src/js/statusbar_color_utils.js",
            "bs_custom_statusbar_color/static/src/js/statusbar_color_service.js",
            "bs_custom_statusbar_color/static/src/js/custom_statusbar.js",
            "bs_custom_statusbar_color/static/src/js/statusbar_command_provider.js",
            "bs_custom_statusbar_color/static/src/js/color_picker_field.js",
            "bs_custom_statusbar_color/static/src/js/statusbar_state_editor.js",
            "bs_custom_statusbar_color/static/src/js/statusbar_state_preview.js",
            "bs_custom_statusbar_color/static/src/xml/custom_statusbar.xml",
            "bs_custom_statusbar_color/static/src/xml/color_picker_field.xml",
            "bs_custom_statusbar_color/static/src/xml/statusbar_state_editor.xml",
            "bs_custom_statusbar_color/static/src/xml/statusbar_state_preview.xml",
        ],
    },
    'icon': '/bs_custom_statusbar_color/static/description/icon.png',
    'images': [
        'static/description/banner.gif',
        'static/description/logo.png',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
