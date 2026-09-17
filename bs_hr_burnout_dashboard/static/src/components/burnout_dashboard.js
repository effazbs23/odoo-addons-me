/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class BsBurnoutDashboard extends Component {
    static template = "bs_hr_burnout_dashboard.BsBurnoutDashboard";

    setup() {
        this.orm = useService("orm");
        this.state = useState({ risks: [], loading: true });
        onWillStart(async () => {
            const employees = await this.orm.searchRead(
                "hr.employee",
                [],
                ["name", "department_id", "bs_burnout_index", "total_overtime", "bs_overdue_task_count"]
            );
            employees.sort((a, b) => b.bs_burnout_index - a.bs_burnout_index);
            this.state.risks = employees;
            this.state.totalOvertime = Math.round(
                employees.reduce((s, e) => s + (e.total_overtime || 0), 0)
            );
            this.state.overdueTasks = employees.reduce((s, e) => s + (e.bs_overdue_task_count || 0), 0);
            this.state.avgScore = employees.length
                ? Math.round(employees.reduce((s, e) => s + e.bs_burnout_index, 0) / employees.length)
                : 0;
            this.state.loading = false;
        });
    }

    departmentName(dept) {
        return dept ? dept[1] : "-";
    }

    riskClass(score) {
        if (score >= 70) return "bg-danger";
        if (score >= 45) return "bg-warning";
        if (score >= 20) return "bg-info";
        return "bg-success";
    }
}
registry.category("actions").add("bs_hr_burnout_dashboard_action", BsBurnoutDashboard);
