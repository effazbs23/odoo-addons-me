/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillStart } from "@odoo/owl";

export class MrpBomVariantMatrix extends Component {
    static template = "mrp_variant_bom_manager.VariantMatrix";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            loading: true,
            matrix: null,
            notExact: false,
            selectedLines: {},
            selectedVariants: {},
            previewVariantId: null,
            preview: null,
            copySourceVariantId: null,
            copyTargetVariantId: null,
        });
        onWillStart(async () => {
            await this.loadMatrix();
        });
    }

    get bomId() {
        const value = this.props.record.data[this.props.name];
        if (!value) {
            return false;
        }
        if (Array.isArray(value)) {
            return value[0];
        }
        if (typeof value === "object") {
            return value.id ?? value.resId ?? false;
        }
        return value;
    }

    async loadMatrix() {
        const bomId = this.bomId;
        if (!bomId) {
            this.state.loading = false;
            return;
        }
        this.state.matrix = await this.orm.call("mrp.bom", "get_variant_matrix_data", [bomId]);
        this.state.loading = false;
        if (this.state.matrix.variants.length && !this.state.previewVariantId) {
            this.state.previewVariantId = this.state.matrix.variants[0].id;
            await this.loadPreview();
        }
    }

    isLineSelected(lineId) {
        return !!this.state.selectedLines[lineId];
    }

    isVariantSelected(variantId) {
        return !!this.state.selectedVariants[variantId];
    }

    toggleLineSelect(lineId) {
        if (this.state.selectedLines[lineId]) {
            delete this.state.selectedLines[lineId];
        } else {
            this.state.selectedLines[lineId] = true;
        }
    }

    toggleVariantSelect(variantId) {
        if (this.state.selectedVariants[variantId]) {
            delete this.state.selectedVariants[variantId];
        } else {
            this.state.selectedVariants[variantId] = true;
        }
    }

    async toggleCell(lineId, variantId, currentValue) {
        const result = await this.orm.call(
            "mrp.bom", "set_variant_matrix_cell", [this.bomId, lineId, variantId, !currentValue]
        );
        this.state.matrix = result.matrix;
        this.state.notExact = !result.exact;
        if (this.state.previewVariantId) {
            await this.loadPreview();
        }
    }

    async bulkToggle(applies) {
        const lineIds = Object.keys(this.state.selectedLines).map(Number);
        const variantIds = Object.keys(this.state.selectedVariants).map(Number);
        if (!lineIds.length || !variantIds.length) {
            this.notification.add(
                "Select at least one component and one variant first.", { type: "warning" }
            );
            return;
        }
        const result = await this.orm.call(
            "mrp.bom", "set_variant_matrix_bulk", [this.bomId, lineIds, variantIds, applies]
        );
        this.state.matrix = result.matrix;
        this.state.notExact = !result.exact;
        if (this.state.previewVariantId) {
            await this.loadPreview();
        }
    }

    async onPreviewVariantChange(ev) {
        this.state.previewVariantId = parseInt(ev.target.value, 10);
        await this.loadPreview();
    }

    async loadPreview() {
        if (!this.state.previewVariantId) {
            return;
        }
        this.state.preview = await this.orm.call(
            "mrp.bom", "action_preview_variant", [this.bomId, this.state.previewVariantId]
        );
    }

    onCopySourceChange(ev) {
        this.state.copySourceVariantId = parseInt(ev.target.value, 10) || null;
    }

    onCopyTargetChange(ev) {
        this.state.copyTargetVariantId = parseInt(ev.target.value, 10) || null;
    }

    async copyVariant() {
        if (!this.state.copySourceVariantId || !this.state.copyTargetVariantId) {
            this.notification.add(
                "Pick both a source and a target variant.", { type: "warning" }
            );
            return;
        }
        const result = await this.orm.call(
            "mrp.bom", "action_copy_variant_bom",
            [this.bomId, this.state.copySourceVariantId, this.state.copyTargetVariantId]
        );
        this.state.matrix = result.matrix;
        this.state.notExact = !result.exact;
        this.notification.add("BOM configuration copied to the target variant.", { type: "success" });
    }
}

registry.category("fields").add("mrp_bom_variant_matrix", {
    component: MrpBomVariantMatrix,
    displayName: "Variant-Aware BOM Matrix",
    supportedTypes: ["many2one"],
});
