import base64

from odoo import fields, http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal

VESSEL_PLAN_NAMES = ["Vessels", "Cost Centers"]

# Upload hardening: max 10 MB per file and an allow-list of safe extensions.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp",
    ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt",
}


def _analytic_cost_center_domain(company_ids=None):
    domain = [("plan_id.name", "in", VESSEL_PLAN_NAMES)]
    if company_ids:
        domain.append(("company_id", "in", [False, *company_ids]))
    return domain


def _read_validated_upload(file):
    """Return base64 data for an uploaded file after validating extension and
    size, or None if the file is empty/absent. Raises on invalid uploads."""
    from odoo.exceptions import UserError
    import os

    if not file or not file.filename:
        return None
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise UserError("File type '%s' is not allowed." % (ext or file.filename))
    data = file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise UserError("Uploaded file exceeds the 10 MB size limit.")
    return base64.b64encode(data)


class PettyCashPortal(http.Controller):
    @http.route(["/my/cash_requests"], type="http", auth="user", website=True)
    def my_cash_requests(self, **kw):
        """List all cash requests"""
        uid = request.uid
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", uid)], limit=1)
        )

        if not employee:
            return request.render("petty_cash.portal_no_employee", {})

        cash_requests = (
            request.env["petty.cash.request"]
            .sudo()
            .search([("employee_id", "=", employee.id)])
        )

        return request.render(
            "petty_cash.portal_my_cash_requests",
            {
                "cash_requests": cash_requests,
            },
        )

    @http.route(["/cash_request/new"], type="http", auth="user", website=True)
    def cash_request_form(self, **kw):
        """Show form to create new cash request"""
        user = request.env.user
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", user.id)], limit=1)
        )

        if not employee:
            return request.render("petty_cash.portal_no_employee", {})

        company_ids = user.company_ids.ids
        vessel_records = (
            request.env["account.analytic.account"]
            .sudo()
            .search(
                _analytic_cost_center_domain(company_ids),
                limit=1000,
            )
        )
        vessels = [
            {
                "id": v.id,
                "name": v.complete_name or v.name,
                "company_id": v.company_id.id,
            }
            for v in vessel_records
        ]
        context = {
            "companies": user.company_ids,
            "default_company": user.company_id,
            "currencies": request.env["res.currency"].sudo().search([]),
            "vessels": vessels,
            "employee": employee,
            "today": fields.Date.today(),
        }
        return request.render("petty_cash.portal_cash_request_form", context)

    @http.route(
        ["/cash_request/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def cash_request_submit(self, **kw):
        """Create new cash request"""
        uid = request.uid
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", uid)], limit=1)
        )

        if not employee:
            return request.redirect("/my/cash_requests")

        # Collect per-line purpose and amount arrays from POST data
        purposes = request.form.getlist("line_purpose[]")
        amounts = request.form.getlist("line_amount[]")
        files = request.files.getlist("line_attachment[]")

        # Build line_ids commands
        line_ids = []
        for idx, (purpose, amount) in enumerate(zip(purposes, amounts, strict=False)):
            purpose = purpose.strip()
            if not purpose:
                continue
            try:
                amt = float(amount)
            except (ValueError, TypeError):
                amt = 0.0
            if amt < 0:
                amt = 0.0
            line_vals = {"purpose": purpose, "amount": amt}
            if idx < len(files):
                data = _read_validated_upload(files[idx])
                if data is not None:
                    line_vals["attachment"] = data
                    line_vals["attachment_filename"] = files[idx].filename
            line_ids.append((0, 0, line_vals))

        if not line_ids:
            return request.redirect("/cash_request/new")

        user = request.env.user

        # --- Validate client-supplied foreign keys against what this user may use ---
        # Company: must be one the user is actually a member of.
        try:
            company_id = int(kw.get("company_id"))
        except (ValueError, TypeError):
            company_id = user.company_id.id
        if company_id not in user.company_ids.ids:
            company_id = user.company_id.id

        # Currency: must be an active currency.
        currency_id = user.company_id.currency_id.id
        if kw.get("currency_id"):
            try:
                cid = int(kw.get("currency_id"))
            except (ValueError, TypeError):
                cid = False
            if cid and request.env["res.currency"].sudo().browse(cid).exists():
                currency_id = cid

        # Vessel / cost center: must belong to the allowed plan and company.
        vessel_id = False
        if kw.get("vessel_id"):
            try:
                vid = int(kw.get("vessel_id"))
            except (ValueError, TypeError):
                vid = False
            if vid:
                allowed = (
                    request.env["account.analytic.account"]
                    .sudo()
                    .search_count(
                        _analytic_cost_center_domain([company_id]) + [("id", "=", vid)]
                    )
                )
                vessel_id = vid if allowed else False

        vals = {
            "employee_id": employee.id,
            "company_id": company_id,
            "currency_id": currency_id,
            "notes": kw.get("notes", ""),
            "date": kw.get("date") or fields.Date.today(),
            "vessel_id": vessel_id,
            "line_ids": line_ids,
            "request_type": kw.get("request_type")
            if kw.get("request_type") in dict(
                request.env["petty.cash.request"]._fields["request_type"].selection
            )
            else "purchase",
        }

        # Create in the validated company's context; the portal record rule
        # scopes the record to this employee.
        cash_request = (
            request.env["petty.cash.request"]
            .sudo()
            .with_company(company_id)
            .create(vals)
        )

        # Handle single top-level file attachment
        if "attachment" in request.files:
            file_data = _read_validated_upload(request.files.get("attachment"))
            if file_data is not None:
                attachment = (
                    request.env["ir.attachment"]
                    .sudo()
                    .create(
                        {
                            "name": request.files.get("attachment").filename,
                            "datas": file_data,
                            "res_model": "petty.cash.request",
                            "res_id": cash_request.id,
                        }
                    )
                )
                cash_request.sudo().write({"attachment_ids": [(4, attachment.id)]})

        if kw.get("submit_now"):
            cash_request.action_submit()

        return request.redirect("/my/cash_request/%s" % cash_request.id)

    @http.route(
        ["/my/cash_request/<int:request_id>"], type="http", auth="user", website=True
    )
    def my_cash_request_detail(self, request_id, **kw):
        """Show cash request details"""
        cash_request = request.env["petty.cash.request"].sudo().browse(request_id)
        if not cash_request.exists():
            return request.not_found()

        # Check ownership
        uid = request.uid
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", uid)], limit=1)
        )
        if not employee or cash_request.employee_id.id != employee.id:
            return request.not_found()

        return request.render(
            "petty_cash.portal_cash_request_detail",
            {
                "cash_request": cash_request,
            },
        )

    @http.route(
        ["/my/cash_request/<int:request_id>/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def cash_request_submit_action(self, request_id, **kw):
        """Submit cash request for approval"""
        cash_request = request.env["petty.cash.request"].sudo().browse(request_id)
        if not cash_request.exists():
            return request.redirect("/my/cash_requests")

        # Check ownership
        uid = request.uid
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", uid)], limit=1)
        )
        if (
            employee
            and cash_request.employee_id.id == employee.id
            and cash_request.state == "draft"
        ):
            cash_request.action_submit()

        return request.redirect("/my/cash_request/%s" % request_id)

    @http.route(
        ["/my/cash_request/<int:request_id>/cancel"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def cash_request_cancel_action(self, request_id, **kw):
        """Cancel cash request submission"""
        cash_request = request.env["petty.cash.request"].sudo().browse(request_id)
        if not cash_request.exists():
            return request.redirect("/my/cash_requests")

        # Check ownership
        uid = request.uid
        employee = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", uid)], limit=1)
        )
        if (
            employee
            and cash_request.employee_id.id == employee.id
            and cash_request.state == "submitted"
        ):
            cash_request.action_draft()

        return request.redirect("/my/cash_request/%s" % request_id)


class PettyCashCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        """Add cash request counter to portal home"""
        values = super()._prepare_home_portal_values(counters)
        if "cash_request_count" in counters:
            uid = request.uid
            employee = (
                request.env["hr.employee"]
                .sudo()
                .search([("user_id", "=", uid)], limit=1)
            )
            if employee:
                values["cash_request_count"] = (
                    request.env["petty.cash.request"]
                    .sudo()
                    .search_count([("employee_id", "=", employee.id)])
                )
            else:
                values["cash_request_count"] = 0
        return values


class PettyCashPortalJSON(http.Controller):
    """JSON endpoints for AJAX requests"""

    @http.route(["/get_vessels_by_company"], type="jsonrpc", auth="user", website=True)
    def get_vessels_by_company(self, company_id=None, **kw):
        """Returns cost centers filtered by company"""
        company_ids = [int(company_id)] if company_id else None
        vessel_domain = _analytic_cost_center_domain(company_ids)

        vessel_records = (
            request.env["account.analytic.account"]
            .sudo()
            .search(
                vessel_domain,
                limit=500,
            )
        )

        vessels = [
            {
                "id": v.id,
                "name": v.complete_name or v.name,
            }
            for v in vessel_records
        ]

        return {"vessels": vessels}
