/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC_END } from "@html_builder/utils/option_sequence";
import { BaseOptionComponent } from "@html_builder/core/utils";
import { BuilderAction } from "@html_builder/core/builder_action";

export class ProductTabSnippetOption extends BaseOptionComponent {
    static template = "theme_kingdom.ProductTabSnippetOption";
    static selector =
        "section.s_product_carousel[data-snippet], section.s_category_dual_carousels[data-snippet]";
}

export class OpenProductTabsAction extends BuilderAction {
    static id = "openProductTabs";

    apply({ editingElement }) {
        const section = editingElement?.closest?.("[data-snippet]") || editingElement;
        const snippet = section?.dataset?.snippet || "";
        const action =
            snippet.includes("s_category_dual_carousels")
                ? "theme_kingdom.kingdom_dual_carousel_tab_action"
                : "theme_kingdom.kingdom_product_tab_action";
        window.open(`/web#action=${action}`, "_blank");
    }
}

class ProductTabSnippetOptionPlugin extends Plugin {
    static id = "productTabSnippetOption";
    resources = {
        builder_options: [withSequence(SNIPPET_SPECIFIC_END, ProductTabSnippetOption)],
        builder_actions: {
            OpenProductTabsAction,
        },
    };
}

registry
    .category("website-plugins")
    .add(ProductTabSnippetOptionPlugin.id, ProductTabSnippetOptionPlugin);
