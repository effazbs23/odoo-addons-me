/** @odoo-module **/

import {registry} from "@web/core/registry";
import {_t} from "@web/core/l10n/translation";
import {user} from "@web/core/user";

/**
 * Makes "Custom Statusbar Color" findable from the global command palette
 * (Ctrl+K) regardless of which app is currently open.
 *
 * Gated on base.group_system, matching the menu item's group restriction
 * (see views/menu.xml) - otherwise a regular internal user could reach the
 * admin-only configuration screen through the palette even though it's
 * hidden from their menu.
 */
registry.category("command_provider").add("custom_statusbar", {
    provide: async (env) => {
        const isSystemUser = await user.hasGroup("base.group_system");
        if (!isSystemUser) {
            return [];
        }
        return [
            {
                name: _t("Custom Statusbar Color"),
                category: "default",
                action: () => {
                    env.services.action.doAction("bs_custom_statusbar_color.action_module_config");
                },
            },
        ];
    },
});
