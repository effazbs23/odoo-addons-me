/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { BaseOptionComponent } from "@html_builder/core/utils";
import { FooterTemplateChoice } from "@website/builder/plugins/options/footer_template_option";

/**
 * Theme-tab Header template gallery (always visible in Theme sidebar).
 * Same actions as Style → Header → Template.
 */
export class KingdomThemeHeaderTemplateOption extends BaseOptionComponent {
    static template = "theme_kingdom.ThemeHeaderTemplateOption";
}

/**
 * Theme-tab Footer template gallery (always visible in Theme sidebar).
 * Reuses the same footerTemplates list as Style → Footer → Template.
 */
export class KingdomThemeFooterTemplateOption extends BaseOptionComponent {
    static template = "theme_kingdom.ThemeFooterTemplateOption";
    static dependencies = ["footerOption"];

    setup() {
        super.setup();
        this.footerTemplates = useState(this.dependencies.footerOption.getFooterTemplates());
    }
}

/**
 * Registers Kingdom footer in Style → Footer → Template, and exposes
 * Header / Footer template galleries on the Theme tab sidebar.
 */
class KingdomHeaderFooterTemplatePlugin extends Plugin {
    static id = "kingdomHeaderFooterTemplate";

    resources = {
        footer_templates_providers: [() => this.getKingdomFooterTemplates()],
        theme_options: [
            withSequence(
                25,
                this.getThemeOptionBlock(
                    "kingdom-header-template",
                    _t("Header"),
                    KingdomThemeHeaderTemplateOption
                )
            ),
            withSequence(
                26,
                this.getThemeOptionBlock(
                    "kingdom-footer-template",
                    _t("Footer"),
                    KingdomThemeFooterTemplateOption
                )
            ),
        ],
    };

    getKingdomFooterTemplates() {
        return [
            {
                key: "kingdom",
                Component: FooterTemplateChoice,
                props: {
                    title: _t("Kingdom"),
                    view: "theme_kingdom.template_footer_kingdom",
                    varName: "kingdom",
                    imgSrc: "/theme_kingdom/static/src/img/snippets_options/footer_template_kingdom.svg",
                },
            },
        ];
    }

    getThemeOptionBlock(id, name, OptionClass) {
        const el = this.document.createElement("div");
        el.dataset.name = name;
        this.document.body.appendChild(el);
        OptionClass.selector = "*";
        return {
            id,
            element: el,
            hasOverlayOptions: false,
            headerMiddleButton: false,
            isClonable: false,
            isRemovable: false,
            options: [OptionClass],
            optionsContainerTopButtons: [],
            snippetModel: {},
        };
    }
}

registry
    .category("website-plugins")
    .add(KingdomHeaderFooterTemplatePlugin.id, KingdomHeaderFooterTemplatePlugin);
