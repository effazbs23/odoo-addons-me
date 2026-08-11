/** @odoo-module **/

import {registry} from "@web/core/registry";

/**
 * Caches the model/field/state -> {defaultColor, inStateColor} mapping
 * from custom.statusbar.state.config so that the patched StatusBarField
 * can look up colors synchronously while rendering, without an RPC per
 * field. The cache is rebuilt on load and whenever a bus notification
 * signals that colors were changed by any user.
 */
export const statusbarColorService = {
    dependencies: ["orm", "bus_service"],

    async start(env, {orm, bus_service}) {
        let defaultColorMap = {};
        let inStateColorMap = {};

        const buildKey = (model, field, value) => `${model}:${field}:${value}`;

        async function load() {
            const modules = await orm.searchRead(
                "custom.statusbar.module.config",
                [["enabled", "=", true]],
                ["id"]
            );
            if (!modules.length) {
                defaultColorMap = {};
                inStateColorMap = {};
                return;
            }
            const states = await orm.searchRead(
                "custom.statusbar.state.config",
                [
                    ["enabled", "=", true],
                    ["module_config_id", "in", modules.map((module) => module.id)],
                ],
                ["model_name", "field_name", "state_value", "default_color", "in_state_color"]
            );
            const nextDefaultColorMap = {};
            const nextInStateColorMap = {};
            for (const state of states) {
                const key = buildKey(state.model_name, state.field_name, state.state_value);
                if (state.default_color) {
                    nextDefaultColorMap[key] = state.default_color;
                }
                if (state.in_state_color) {
                    nextInStateColorMap[key] = state.in_state_color;
                }
            }
            defaultColorMap = nextDefaultColorMap;
            inStateColorMap = nextInStateColorMap;
        }

        await load();

        bus_service.subscribe("custom_statusbar.colors_updated", load);
        bus_service.addChannel("custom_statusbar");

        return {
            getDefaultColor(model, field, value) {
                return defaultColorMap[buildKey(model, field, value)] || null;
            },
            getInStateColor(model, field, value) {
                return inStateColorMap[buildKey(model, field, value)] || null;
            },
            refresh: load,
        };
    },
};

registry.category("services").add("statusbar_color", statusbarColorService);
