/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { BaseOptionComponent } from "@html_builder/core/utils";
import {
    HEADER_FONT,
} from "@website/builder/plugins/options/header/header_option_plugin";
import { FOOTER_COLORS } from "@website/builder/plugins/options/footer_option_plugin";

/**
 * Top Bar + Header + Navbar text/background colors for Kingdom header.
 * Shown when Style options target header.o_header_kingdom.
 */
export class KingdomHeaderChromeColorsOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomHeaderChromeColorsOption";
    static selector = "#wrapwrap > header.o_header_kingdom";
    static editableOnly = false;
    static groups = ["website.group_website_designer"];
}

/**
 * Footer text/background colors for Kingdom footer (incl. white bg).
 */
export class KingdomFooterChromeColorsOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomFooterChromeColorsOption";
    // Prefer o_footer_kingdom; also match Kingdom `.footer` class if the marker was dropped.
    static selector = "#wrapwrap > footer.o_footer_kingdom, #wrapwrap > footer#bottom.footer";
    static editableOnly = false;
    static groups = ["website.group_website_designer"];
}

class KingdomChromeColorsPlugin extends Plugin {
    static id = "kingdomChromeColors";

    resources = {
        builder_options: [
            // After header font options; before elements.
            withSequence(HEADER_FONT + 1, KingdomHeaderChromeColorsOption),
            // Beside core footer background picker.
            withSequence(FOOTER_COLORS + 1, KingdomFooterChromeColorsOption),
        ],
    };
}

registry.category("website-plugins").add(KingdomChromeColorsPlugin.id, KingdomChromeColorsPlugin);
