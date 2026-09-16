/** @odoo-module **/

import { registry } from "@web/core/registry";
import { download } from "@web/core/network/download";
import { getReportUrl } from "@web/webclient/actions/reports/utils";
import { user } from "@web/core/user";

/**
 * Client-side handler for `report_type = 'xlsx'` report actions.
 *
 * The action service only knows qweb-html / qweb-pdf / qweb-text out of the box and
 * logs "unhandled report type" for anything else, so an extra type plugs itself into
 * the handler registry. Returning a truthy value tells the action service the report
 * was taken care of; it then applies `close_on_report_download` and `onClose` itself,
 * which is why neither is handled here.
 */
async function xlsxReportHandler(action, options, env) {
    if (action.report_type !== "xlsx") {
        return false;
    }
    const downloadContext = { ...user.context, ...(action.context || {}) };
    env.services.ui.block();
    try {
        await download({
            url: "/report/download",
            data: {
                data: JSON.stringify([getReportUrl(action, "xlsx"), action.report_type]),
                context: JSON.stringify(downloadContext),
            },
        });
    } finally {
        env.services.ui.unblock();
    }
    return true;
}

registry.category("ir.actions.report handlers").add("xlsx", xlsxReportHandler);
