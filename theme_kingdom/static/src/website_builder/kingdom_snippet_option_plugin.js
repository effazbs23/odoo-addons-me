/** @odoo-module **/

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { _t } from "@web/core/l10n/translation";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";
import { BaseOptionComponent } from "@html_builder/core/utils";
import { BuilderAction } from "@html_builder/core/builder_action";

const KINGDOM_SNIPPET_SELECTOR = "section[data-snippet^='theme_kingdom.']";

const KINGDOM_SNIPPET_ACTIONS = {
    "theme_kingdom.s_featured_products": "theme_kingdom.action_featured_products",
    "theme_kingdom.s_bestsale_products": "theme_kingdom.action_bestsale_products",
    "theme_kingdom.s_deal_of_the_day": "theme_kingdom.action_kingdom_deals_of_day",
    "theme_kingdom.s_manufacturers": "theme_kingdom.action_kingdom_manufacturer",
    "theme_kingdom.s_product_carousel": "theme_kingdom.kingdom_product_tab_action",
    "theme_kingdom.s_category_dual_carousels": "theme_kingdom.kingdom_product_tab_action",
};

function getKingdomSnippetSection(editingElement) {
    return editingElement?.closest?.(KINGDOM_SNIPPET_SELECTOR) || null;
}

function getHomepageWrap(editable, nextTargetEl) {
    return (
        nextTargetEl?.closest?.("#wrap.oe_structure, .oe_structure[data-oe-id]") ||
        editable.querySelector("#wrap.oe_structure[data-oe-id], #wrap.oe_structure")
    );
}

export class KingdomSnippetOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomSnippetOption";
    static selector = KINGDOM_SNIPPET_SELECTOR;

    get configAction() {
        const snippetKey = this.env.getEditingElement()?.dataset?.snippet;
        return snippetKey ? KINGDOM_SNIPPET_ACTIONS[snippetKey] : null;
    }
}

export class KingdomCarouselSlideOption extends BaseOptionComponent {
    static template = "theme_kingdom.KingdomCarouselSlideOption";
    static selector = `${KINGDOM_SNIPPET_SELECTOR} .carousel-item`;
}

export class OpenKingdomSnippetConfigAction extends BuilderAction {
    static id = "openKingdomSnippetConfig";

    apply({ params }) {
        const actionXmlId = params?.actionXmlId;
        if (!actionXmlId) {
            return;
        }
        window.open(`/web#action=${actionXmlId}`, "_blank");
    }
}

export class RemoveKingdomSnippetBlockAction extends BuilderAction {
    static id = "removeKingdomSnippetBlock";
    static dependencies = ["remove"];

    apply({ editingElement }) {
        const section =
            editingElement?.matches?.(KINGDOM_SNIPPET_SELECTOR)
                ? editingElement
                : getKingdomSnippetSection(editingElement);
        if (section) {
            this.dependencies.remove.removeElement(section);
        }
    }
}

const VIEW_BRANDING_ATTRS = [
    "data-oe-model",
    "data-oe-id",
    "data-oe-field",
    "data-oe-xpath",
    "data-oe-source-id",
];

class KingdomSnippetOptionPlugin extends Plugin {
    static id = "kingdomSnippetOption";
    static dependencies = ["builderOptions", "remove"];
    resources = {
        builder_options: [
            withSequence(SNIPPET_SPECIFIC, KingdomSnippetOption),
            withSequence(SNIPPET_SPECIFIC, KingdomCarouselSlideOption),
        ],
        builder_actions: {
            OpenKingdomSnippetConfigAction,
            RemoveKingdomSnippetBlockAction,
        },
        get_overlay_buttons: withSequence(10, {
            getButtons: (target) => this.getKingdomCarouselOverlayButtons(target),
        }),
        on_removed_handlers: this.onRemovedKingdomSnippet.bind(this),
        // Keep #wrap editable: never persist ir.ui.view branding inside page arches.
        clean_for_save_handlers: this.cleanViewBrandingForSave.bind(this),
    };

    cleanViewBrandingForSave({ root }) {
        if (!root) {
            return;
        }
        // Keep branding on the savable root (#wrap); strip it from descendants.
        root.querySelectorAll('[data-oe-model="ir.ui.view"]').forEach((el) => {
            if (el === root) {
                return;
            }
            for (const attr of VIEW_BRANDING_ATTRS) {
                el.removeAttribute(attr);
            }
        });
    }

    /**
     * Hero/carousel snippets select the active .carousel-item for the floating
     * toolbar (it is resizable). Odoo marks slides unremovable, so the trash
     * icon is omitted unless we add it for the parent Kingdom section.
     */
    getKingdomCarouselOverlayButtons(target) {
        if (!target.classList.contains("carousel-item")) {
            return [];
        }
        const section = target.closest(KINGDOM_SNIPPET_SELECTOR);
        if (!section) {
            return [];
        }
        return [
            {
                class: "oe_snippet_remove bg-danger fa fa-trash",
                title: _t("Remove this block"),
                handler: () => this.dependencies.remove.removeElement(section),
            },
        ];
    }

    onRemovedKingdomSnippet({ removedEl, nextTargetEl }) {
        if (!removedEl.matches?.(KINGDOM_SNIPPET_SELECTOR)) {
            return;
        }
        // Clear overlay after DOM removal (before history refresh) to avoid
        // MovePlugin reading parentNode.children on a detached section.
        this.dependencies.builderOptions.deactivateContainers();
        const wrapEl = getHomepageWrap(this.editable, nextTargetEl);
        if (wrapEl) {
            wrapEl.classList.add("o_dirty");
        }
    }
}

registry
    .category("website-plugins")
    .add(KingdomSnippetOptionPlugin.id, KingdomSnippetOptionPlugin);
