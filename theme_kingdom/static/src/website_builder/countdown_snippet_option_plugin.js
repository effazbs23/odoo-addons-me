/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";
import { BaseOptionComponent } from "@html_builder/core/utils";

export class KingdomCountdownOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomCountdownOption";
    static selector = ".s_kingdom_countdown, [data-snippet='theme_kingdom.s_countdown']";
}

class KingdomCountdownOptionPlugin extends Plugin {
    static id = "kingdomCountdownOption";
    resources = {
        builder_options: [withSequence(SNIPPET_SPECIFIC, KingdomCountdownOption)],
    };
}

registry
    .category("website-plugins")
    .add(KingdomCountdownOptionPlugin.id, KingdomCountdownOptionPlugin);
