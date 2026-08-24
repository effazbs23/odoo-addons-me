/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { KpiTile } from "./kpi_tile/kpi_tile";
import { GuidedForm } from "./guided_form/guided_form";

// Kanban grouping metadata, keyed by the tile's spec model. Order here is
// the display order of the columns; anything not listed (or stale tiles
// whose model can't be read) falls into a trailing "Other" bucket.
const GROUP_META = [
    ["sale.order", { label: "Sales", color: "#3b82f6" }],
    ["account.move", { label: "Invoicing", color: "#8b5cf6" }],
    ["crm.lead", { label: "Pipeline", color: "#f59e0b" }],
    ["stock.move", { label: "Inventory", color: "#10b981" }],
];
const OTHER_GROUP = { label: "Other", color: "#6b7280" };

const DEFAULT_TILE_WIDTH = 340;
const DEFAULT_TILE_HEIGHT = 260;
const MIN_TILE_WIDTH = 240;
const MAX_TILE_WIDTH = 680;

export class SmartKpiDashboard extends Component {
    static template = "bs_smart_kpi_dashboard.Dashboard";
    static components = { KpiTile, GuidedForm };

    setup() {
        this.rpc = rpc;
        this.notification = useService("notification");

        this.state = useState({
            prompt: "",
            tiles: [],           // saved tiles, each {id, name, chart_type, chart}
            preview: null,       // an unsaved result from the current prompt
            guidedSpec: null,    // set when confidence is low -> show GuidedForm
            options: [],         // allow-listed models/fields, for the guided form
            loading: false,
            suggestions: [],     // typeahead prompts for the ask bar
            showSuggestions: false,
            highlightIndex: -1,
        });
        this._suggestTimer = null;

        onWillStart(async () => {
            await this._loadTiles();
        });
    }

    // Refetch saved tiles, preserving the on-screen size of any tile the
    // user already resized (a plain re-assign from the server would snap
    // every card back to the default size on each pin/reload).
    async _loadTiles() {
        const fresh = await this.rpc("/bs_smart_kpi_dashboard/tiles");
        const prevById = new Map(this.state.tiles.map((t) => [t.id, t]));
        this.state.tiles = fresh.map((t) => {
            const prev = prevById.get(t.id);
            return {
                ...t,
                width: prev ? prev.width : DEFAULT_TILE_WIDTH,
                height: prev ? prev.height : DEFAULT_TILE_HEIGHT,
            };
        });
    }

    // Saved tiles bucketed into kanban groups by source model, in the
    // fixed GROUP_META order, empty groups omitted.
    get groupedTiles() {
        const byLabel = new Map();
        for (const [, meta] of GROUP_META) {
            byLabel.set(meta.label, { ...meta, tiles: [] });
        }
        byLabel.set(OTHER_GROUP.label, { ...OTHER_GROUP, tiles: [] });

        const metaByModel = new Map(GROUP_META);
        for (const tile of this.state.tiles) {
            const meta = metaByModel.get(tile.model) || OTHER_GROUP;
            byLabel.get(meta.label).tiles.push(tile);
        }
        return [...byLabel.values()].filter((g) => g.tiles.length);
    }

    // Cursor-drag resize, aspect ratio locked to whatever it was when the
    // drag started — only the width is driven by the pointer, height is
    // derived from it so the chart never gets stretched out of proportion.
    onResizeStart(tile, ev) {
        ev.preventDefault();
        ev.stopPropagation();
        const startX = ev.clientX;
        const startWidth = tile.width;
        const ratio = tile.height / tile.width;

        const onMove = (moveEv) => {
            const nextWidth = Math.min(
                MAX_TILE_WIDTH,
                Math.max(MIN_TILE_WIDTH, startWidth + (moveEv.clientX - startX))
            );
            tile.width = nextWidth;
            tile.height = Math.round(nextWidth * ratio);
        };
        const onUp = () => {
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", onUp);
        };
        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", onUp);
    }

    onPromptKeydown(ev) {
        const hasSuggestions = this.state.showSuggestions && this.state.suggestions.length;
        if (ev.key === "ArrowDown" && hasSuggestions) {
            ev.preventDefault();
            this.state.highlightIndex = (this.state.highlightIndex + 1) % this.state.suggestions.length;
        } else if (ev.key === "ArrowUp" && hasSuggestions) {
            ev.preventDefault();
            this.state.highlightIndex =
                (this.state.highlightIndex - 1 + this.state.suggestions.length) % this.state.suggestions.length;
        } else if (ev.key === "Escape") {
            this.state.showSuggestions = false;
        } else if (ev.key === "Enter") {
            if (hasSuggestions && this.state.highlightIndex >= 0) {
                ev.preventDefault();
                this.onSuggestionClick(this.state.suggestions[this.state.highlightIndex]);
            } else {
                this.onSubmitPrompt();
            }
        }
    }

    // Debounced typeahead: fetch fresh suggestions a moment after the user
    // stops typing, from vocabulary-derived example prompts server-side
    // (KpiPromptParser.suggest) — never guessed client-side.
    onPromptInput() {
        this.state.highlightIndex = -1;
        this.state.showSuggestions = true;
        clearTimeout(this._suggestTimer);
        this._suggestTimer = setTimeout(() => this._fetchSuggestions(), 150);
    }

    onPromptFocus() {
        this.state.showSuggestions = true;
        this._fetchSuggestions();
    }

    // Suggestion buttons use pointerdown+preventDefault (see template) so
    // this blur never races a click on one of them — it only fires for a
    // genuine click/tab away from the ask bar.
    onPromptBlur() {
        this.state.showSuggestions = false;
    }

    async _fetchSuggestions() {
        const prompt = this.state.prompt;
        const result = await this.rpc("/bs_smart_kpi_dashboard/suggest", { prompt });
        // Drop stale responses if the user kept typing while this was in flight.
        if (prompt === this.state.prompt) {
            this.state.suggestions = result || [];
        }
    }

    onSuggestionClick(text) {
        this.state.prompt = text;
        this.state.suggestions = [];
        this.state.showSuggestions = false;
        this.state.highlightIndex = -1;
    }

    async onSubmitPrompt() {
        if (!this.state.prompt.trim()) return;
        this.state.loading = true;
        this.state.guidedSpec = null;
        this.state.showSuggestions = false;
        try {
            const result = await this.rpc("/bs_smart_kpi_dashboard/generate", {
                prompt: this.state.prompt,
            });
            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else if (result.needs_manual_input) {
                // Don't guess — hand the best-effort partial spec to the
                // guided form so the user finishes it in a few clicks.
                this.state.options = result.options;
                this.state.guidedSpec = result.partial_spec;
            } else {
                this.state.preview = {
                    // Derived from the spec's actual fields, never the raw
                    // prompt — a typo or vague phrasing in what was typed
                    // should never end up as the tile's heading.
                    name: result.title,
                    description: result.description,
                    prompt: this.state.prompt,
                    chart_type: result.spec.chart_type,
                    chart: result.chart,
                    spec: result.spec,
                    source: result.source,
                };
            }
        } finally {
            this.state.loading = false;
        }
    }

    async onGuidedFormSubmit(spec) {
        this.state.loading = true;
        try {
            const result = await this.rpc("/bs_smart_kpi_dashboard/run_manual", { spec });
            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
                return;
            }
            this.state.preview = {
                name: result.title || "Custom KPI",
                description: result.description,
                prompt: this.state.prompt,
                chart_type: spec.chart_type,
                chart: result.chart,
                spec: result.spec,
                source: result.source,
            };
            this.state.guidedSpec = null;
        } finally {
            this.state.loading = false;
        }
    }

    async onPinPreview() {
        const p = this.state.preview;
        if (!p) return;
        const res = await this.rpc("/bs_smart_kpi_dashboard/tile/save", {
            name: p.name,
            prompt: p.prompt,
            spec: p.spec,
            chart_type: p.chart_type,
            shared: false,
        });
        if (res.error) {
            this.notification.add(res.error, { type: "danger" });
            return;
        }
        await this._loadTiles();
        this.state.preview = null;
        this.state.prompt = "";
    }

    async onDeleteTile(tileId) {
        await this.rpc("/bs_smart_kpi_dashboard/tile/delete", { tile_id: tileId });
        this.state.tiles = this.state.tiles.filter((t) => t.id !== tileId);
    }
}

registry.category("actions").add("bs_smart_kpi_dashboard.dashboard", SmartKpiDashboard);
