/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";
import { BaseOptionComponent } from "@html_builder/core/utils";
import { BuilderAction } from "@html_builder/core/builder_action";

const KINGDOM_SNIPPET_ACTIONS = {
    "theme_kingdom.s_featured_products": "theme_kingdom.action_featured_products",
    "theme_kingdom.s_bestsale_products": "theme_kingdom.action_bestsale_products",
    "theme_kingdom.s_deal_of_the_day": "theme_kingdom.action_kingdom_deals_of_day",
    "theme_kingdom.s_manufacturers": "theme_kingdom.action_kingdom_manufacturer",
    "theme_kingdom.s_product_carousel": "theme_kingdom.kingdom_product_tab_action",
    "theme_kingdom.s_category_dual_carousels": "theme_kingdom.kingdom_product_tab_action",
};

export class KingdomSnippetOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomSnippetOption";
    static selector = "section[data-snippet^='theme_kingdom.']";
    static groups = ["website.group_website_designer"];

    get configAction() {
        const snippetKey = this.env.getEditingElement()?.dataset?.snippet;
        return snippetKey ? KINGDOM_SNIPPET_ACTIONS[snippetKey] : null;
    }
}

export class OpenKingdomSnippetConfigAction extends BuilderAction {
    static id = "openKingdomSnippetConfig";

    apply({ editingElement, params }) {
        const actionXmlId = params?.actionXmlId;
        if (!actionXmlId) {
            return;
        }
        window.open(`/web#action=${actionXmlId}`, "_blank");
    }
}

class KingdomSnippetOptionPlugin extends Plugin {
    static id = "kingdomSnippetOption";
    resources = {
        builder_options: [withSequence(SNIPPET_SPECIFIC, KingdomSnippetOption)],
        builder_actions: {
            OpenKingdomSnippetConfigAction,
        },
    };
}

registry
    .category("website-plugins")
    .add(KingdomSnippetOptionPlugin.id, KingdomSnippetOptionPlugin);
