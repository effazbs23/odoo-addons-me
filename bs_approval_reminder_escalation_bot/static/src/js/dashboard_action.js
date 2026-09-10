/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Mirror of the module's _bs_pending_domain() / _bs_get_primary_approver
// display signals, per approval type. The authoritative business-day math
// and approver resolution stay server-side in the cron; this client action
// only reads the same pending sets and shows a calendar-day approximation.
const TYPE_META = {
    purchase_order: {
        label: "Purchase Orders",
        icon: "fa-shopping-cart",
        color: "#00A0DB",
        model: "purchase.order",
        domain: [["state", "=", "to approve"]],
        fields: ["name", "create_date", "create_uid", "user_id"],
    },
    expense_report: {
        label: "Expense Reports",
        icon: "fa-file-text-o",
        color: "#8E59FD",
        model: "hr.expense",
        domain: [["state", "=", "submitted"]],
        fields: ["name", "create_date", "create_uid", "employee_id", "manager_id"],
    },
    time_off: {
        label: "Time Off",
        icon: "fa-plane",
        color: "#FBAF33",
        model: "hr.leave",
        domain: [["state", "in", ["confirm", "validate1"]]],
        fields: ["name", "create_date", "create_uid", "employee_id"],
    },
};

const MS_PER_DAY = 24 * 60 * 60 * 1000;

export class BsApprovalReminderDashboard extends Component {
    static template = "bs_approval_reminder_escalation_bot.Dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            cards: [],
            rows: [],
            selected: null,
            openMenu: null,
        });
        onWillStart(() => this._load());
    }

    async _load() {
        this.state.loading = true;
        try {
            const configs = await this.orm.call(
                "bs.approval.reminder.config",
                "search_read",
                [[["active", "=", true]], ["approval_type", "reminder_threshold_days", "escalation_threshold_days"]]
            );
            const thresholdByType = {};
            for (const cfg of configs) {
                thresholdByType[cfg.approval_type] = cfg;
            }
            const cards = [];
            const rows = [];
            for (const [key, meta] of Object.entries(TYPE_META)) {
                const records = await this.orm.call(meta.model, "search_read", [
                    meta.domain,
                    meta.fields,
                    [["create_date", "desc"]],
                ]);
                const card = {
                    key,
                    label: meta.label,
                    icon: meta.icon,
                    color: meta.color,
                    count: records.length,
                    reminderOverdue: 0,
                    escalationDue: 0,
                };
                const cfg = thresholdByType[key] || {
                    reminder_threshold_days: 3,
                    escalation_threshold_days: 7,
                };
                for (const rec of records) {
                    const status = this._status(rec, cfg);
                    if (status === "reminder_due") {
                        card.reminderOverdue += 1;
                    }
                    if (status === "escalation_due") {
                        card.reminderOverdue += 1;
                        card.escalationDue += 1;
                    }
                    rows.push({
                        uid: meta.model + ":" + rec.id,
                        id: rec.id,
                        model: meta.model,
                        typeKey: key,
                        typeLabel: meta.label,
                        icon: meta.icon,
                        color: meta.color,
                        reference: rec.name,
                        requestedBy: this._requestedBy(meta, rec),
                        approver: this._approver(meta, rec),
                        pendingDays: this._daysPending(rec),
                        status,
                    });
                }
                cards.push(card);
            }
            this.state.cards = cards;
            this.state.rows = rows;
        } catch (error) {
            this.notification.add(
                "Failed to load the approvals dashboard: " + error.message,
                { type: "danger" }
            );
        } finally {
            this.state.loading = false;
        }
    }

    // Calendar-day approximation (the server uses the company's business
    // calendar); only used for this dashboard's display columns.
    _daysPending(rec) {
        if (!rec.create_date) {
            return 0;
        }
        const since = new Date(String(rec.create_date).replace(" ", "T") + "Z");
        return Math.max(0, Math.floor((Date.now() - since.getTime()) / MS_PER_DAY));
    }

    _status(rec, cfg) {
        const days = this._daysPending(rec);
        if (days >= Number(cfg.escalation_threshold_days || 7)) {
            return "escalation_due";
        }
        if (days >= Number(cfg.reminder_threshold_days || 3)) {
            return "reminder_due";
        }
        return "pending";
    }

    _displayName(value) {
        return value && value[1] ? String(value[1]) : "—";
    }

    _requestedBy(meta, rec) {
        if (meta.key === "expense_report" || meta.key === "time_off") {
            if (rec.employee_id) {
                return this._displayName(rec.employee_id);
            }
        }
        return this._displayName(rec.create_uid);
    }

    _approver(meta, rec) {
        if (meta.key === "purchase_order") {
            return this._displayName(rec.user_id);
        }
        if (meta.key === "expense_report") {
            return this._displayName(rec.manager_id);
        }
        return "—";
    }

    selectCard(key) {
        this.state.selected = this.state.selected === key ? null : key;
    }

    toggleMenu(row) {
        this.state.openMenu = this.state.openMenu === row ? null : row;
    }

    get visibleRows() {
        if (!this.state.selected) {
            return this.state.rows;
        }
        return this.state.rows.filter((row) => row.typeKey === this.state.selected);
    }

    viewRecord(row) {
        this.state.openMenu = null;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: row.model,
            res_id: row.id,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
        });
    }

    snoozeRecord(row) {
        this.state.openMenu = null;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "bs.approval.reminder.snooze.wizard",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: {
                active_id: row.id,
                active_ids: [row.id],
                active_model: row.model,
            },
        });
    }
}

registry.category("actions").add(
    "bs_approval_reminder_escalation_bot.dashboard",
    BsApprovalReminderDashboard
);