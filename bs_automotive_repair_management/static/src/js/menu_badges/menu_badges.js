import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, onWillDestroy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

// Ambient "needs manager attention" indicator, implemented as a systray
// item rather than by patching core web.NavBar.SectionsMenu/web.SectionMenu
// templates: the systray is a documented, stable extension point, whereas
// inheriting those templates via XPath into private internal markup breaks
// the whole backend's asset bundle for every user the moment an Odoo point
// release touches that markup (see audit finding, §3).
const REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 min — this is an ambient count, not a live feed
const REQUIRED_GROUP = "bs_automotive_repair_management.group_shop_manager";

const BADGE_SOURCES = [
    {
        model: "automotive.deletion.request",
        domain: [["state", "=", "pending"]],
        actionXmlId: "bs_automotive_repair_management.action_automotive_deletion_request",
    },
    {
        model: "automotive.warranty.claim",
        domain: [["state", "=", "under_review"]],
        actionXmlId: "bs_automotive_repair_management.action_automotive_warranty_claim",
    },
];

export class AutomotiveRepairSystrayItem extends Component {
    static template = "bs_automotive_repair_management.SystrayItem";
    static props = {};

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({ visible: false, total: 0, counts: [] });

        onWillStart(async () => {
            this.state.visible = await user.hasGroup(REQUIRED_GROUP);
            if (this.state.visible) {
                await this._refresh();
            }
        });

        const intervalId = setInterval(() => {
            if (this.state.visible) {
                this._refresh();
            }
        }, REFRESH_INTERVAL_MS);
        onWillDestroy(() => clearInterval(intervalId));
    }

    async _refresh() {
        const counts = await Promise.all(
            BADGE_SOURCES.map((source) => this.orm.searchCount(source.model, source.domain))
        );
        this.state.counts = counts;
        this.state.total = counts.reduce((sum, count) => sum + count, 0);
    }

    get displayCount() {
        return this.state.total > 99 ? "99+" : String(this.state.total);
    }

    onClick() {
        // Jump to whichever queue actually has something pending, preferring
        // deletion requests since those block a workflow (record deletion)
        // until a manager decides either way.
        const index = this.state.counts.findIndex((count) => count > 0);
        const source = BADGE_SOURCES[index === -1 ? 0 : index];
        this.actionService.doAction(source.actionXmlId);
    }
}

registry.category("systray").add(
    "bs_automotive_repair_management.badge",
    { Component: AutomotiveRepairSystrayItem },
    { sequence: 1 },
);
