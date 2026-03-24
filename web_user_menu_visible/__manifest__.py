{
    "name": "Web User Menu Visible",
    "summary": "Always display username in the top bar of Odoo UI",
    "description": """
        This module extends the web user menu to always show the username in the top bar,
        regardless of debug mode. By default, Odoo only shows the username when in debug mode,
        but this module ensures it's always visible.
    """,
    "author": "Brain Station 23",
    "website": "https://brainstation-23.com",
    "category": "Web",
    "version": "19.0.1.0.0",
    "depends": ["web"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "web_user_menu_visible/static/src/xml/user_menu.xml",
        ],
    },
    "license": "LGPL-3",
    "support": "erp23@brainstation-23.com",
    "auto_install": False,
    "installable": True,
}
