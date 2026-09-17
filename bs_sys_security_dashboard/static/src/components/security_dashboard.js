/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BsSecurityDashboard extends Component {
    static template = "bs_sys_security_dashboard.BsSecurityDashboard";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ sessions: [], loading: true });

        onWillStart(async () => { await this.loadSessions(); });
    }

    async loadSessions() {
        this.state.loading = true;
        this.state.sessions = await this.orm.searchRead(
            "bs.session.log", [], ["user_id", "session_id", "ip_address", "last_activity"]
        );
        this.state.loading = false;
    }

    async killSession(sessionId) {
        const success = await this.orm.call("bs.session.log", "action_kill_session", [sessionId]);
        if (success) {
            this.notification.add("Session terminated.", { type: "success" });
            await this.loadSessions();
        } else {
            this.notification.add("Could not terminate session.", { type: "danger" });
        }
    }
}
registry.category("actions").add("bs_sys_security_dashboard_action", BsSecurityDashboard);
