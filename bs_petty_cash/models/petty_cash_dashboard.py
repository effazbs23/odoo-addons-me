"""
Petty Cash Dashboard Backend

Provides data computation methods for the interactive dashboard.
All methods are designed to work with filters and return formatted data for OWL frontend.
"""

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class PettyCashDashboard(models.Model):
    _name = "petty.cash.dashboard"
    _description = "Petty Cash Dashboard Data Provider"

    name = fields.Char(default="Petty Cash Dashboard")

    @api.model
    def get_dashboard_data(
        self,
        date_from=None,
        date_to=None,
        request_type=None,
        department_id=None,
        employee_id=None,
        company_id=None,
    ):
        """
        Main RPC method to fetch all dashboard data.

        Args:
            date_from: Start date (YYYY-MM-DD string)
            date_to: End date (YYYY-MM-DD string)
            request_type: Filter by request type (purchase, salary, tour_travel, operational_expenses)
            department_id: Filter by department ID
            employee_id: Filter by employee ID
            company_id: Filter by company ID

        Returns:
            dict: Complete dashboard data including KPIs, charts, activities, alerts
        """
        # Only expose data for companies the current user is actually allowed to
        # see. Never blindly sudo() across the whole database, and never trust a
        # client-supplied company_id that is outside the user's allowed set.
        allowed_company_ids = self.env.companies.ids
        company = False
        if company_id and company_id in allowed_company_ids:
            company = self.env["res.company"].browse(company_id).exists()
        if not company:
            company = self.env.company
        company_id = company.id
        currency_symbol = company.currency_id.symbol or "$"

        # Build common domain for filtering
        domain_advance = self._build_advance_domain(date_from, date_to, employee_id, company_id)
        domain_settlement = self._build_settlement_domain(
            date_from, date_to, employee_id, company_id
        )
        domain_request = self._build_request_domain(
            date_from, date_to, request_type, department_id, employee_id, company_id
        )

        return {
            "kpis": self._compute_kpi_cards(domain_advance, domain_settlement, company_id),
            # ── Four analytics / chart sections ──────────────────────────────
            "advance_type_distribution": self._compute_advance_type_distribution(
                date_from, date_to, request_type, department_id, employee_id, company_id
            ),
            "monthly_trend": self._compute_monthly_trend(date_from, date_to, company_id),
            "top_outstanding_employees": self._compute_top_outstanding_employees(company_id),
            "request_status_funnel": self._compute_request_status_funnel(domain_request),
            # ── Supporting data ───────────────────────────────────────────────
            "recent_activities": self._get_recent_activities(limit=20, company_id=company_id),
            "alerts": self._get_alerts(company_id),
            "currency_symbol": currency_symbol,
            "filters": {
                "date_from": date_from
                or fields.Date.to_string(fields.Date.today() - relativedelta(months=1)),
                "date_to": date_to or fields.Date.to_string(fields.Date.today()),
                "request_type": request_type,
                "department_id": department_id,
                "employee_id": employee_id,
                "company_id": company_id,
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Domain builders
    # ──────────────────────────────────────────────────────────────────────────

    def _build_advance_domain(self, date_from, date_to, employee_id, company_id=None):
        """Build domain for filtering petty.cash.advance records."""
        domain = [("state", "!=", "cancelled")]

        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _build_settlement_domain(self, date_from, date_to, employee_id, company_id=None):
        """Build domain for filtering petty.cash.settlement records."""
        domain = [("state", "!=", "cancelled")]

        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _build_request_domain(
        self, date_from, date_to, request_type, department_id, employee_id, company_id=None
    ):
        """Build domain for filtering petty.cash.request records."""
        domain = []

        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        if request_type:
            domain.append(("request_type", "=", request_type))
        if department_id:
            domain.append(("department_id", "=", department_id))
        if employee_id:
            domain.append(("employee_id", "=", employee_id))
        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    # ──────────────────────────────────────────────────────────────────────────
    # KPI cards
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_kpi_cards(self, domain_advance, domain_settlement, company_id=None):
        """
        Compute all KPI card values.

        Returns:
            dict: KPI values with icons and colors
        """
        Advance = self.env["petty.cash.advance"]
        Settlement = self.env["petty.cash.settlement"]

        # Company-only domain (no date filter) for all-time KPIs
        company_domain = [("company_id", "=", company_id)] if company_id else []

        # Total Advance Issued (paid advances in period)
        paid_advances = Advance.search(
            domain_advance + [("state", "in", ["paid", "partially_settled", "settled"])]
        )
        total_advance_issued = sum(paid_advances.mapped("amount"))

        # Total Settled Amount (posted settlements in period)
        posted_settlements = Settlement.search(
            domain_settlement + [("state", "=", "posted")]
        )
        total_settled = sum(posted_settlements.mapped("total_amount"))

        # Outstanding Advance (all active advances with balance > 0, regardless of date)
        outstanding_advances = Advance.search(
            company_domain + [("state", "in", ["paid", "partially_settled"]), ("balance", ">", 0)]
        )
        outstanding_advance = sum(outstanding_advances.mapped("balance"))

        # Overdue Advances (expected settlement date passed, still has balance)
        today = fields.Date.today()
        overdue_advances = Advance.search(
            company_domain + [
                ("state", "in", ["paid", "partially_settled"]),
                ("balance", ">", 0),
                ("expected_settlement_date", "<", today),
            ]
        )
        overdue_advances_count = len(overdue_advances)

        # Active Advances (currently in paid or partially_settled state)
        active_advances_count = len(
            Advance.search(company_domain + [("state", "in", ["paid", "partially_settled"])])
        )

        # Pending Settlements (in draft or submitted state)
        pending_settlements = Settlement.search(
            company_domain + [("state", "in", ["draft", "submitted"])]
        )
        pending_settlements_count = len(pending_settlements)

        # Approved Advances (approved but payment not yet disbursed)
        approved_advances = Advance.search(
            domain_advance + [("state", "=", "approved")]
        )
        approved_advances_count = len(approved_advances)

        return {
            "total_advance_issued": {
                "value": total_advance_issued,
                "label": "Total Advance Issued",
                "icon": "fa-money",
                "color": "success",
                "currency": True,
            },
            "total_settled": {
                "value": total_settled,
                "label": "Total Settled Amount",
                "icon": "fa-check-circle",
                "color": "warning",
                "currency": True,
            },
            "outstanding_advance": {
                "value": outstanding_advance,
                "label": "Outstanding Advance",
                "icon": "fa-hourglass-half",
                "color": "warning",
                "currency": True,
            },
            "overdue_advances": {
                "value": overdue_advances_count,
                "label": "Overdue Advances",
                "icon": "fa-exclamation-triangle",
                "color": "danger",
                "currency": False,
            },
            "active_advances": {
                "value": active_advances_count,
                "label": "Active Advances",
                "icon": "fa-file-text",
                "color": "info",
                "currency": False,
            },
            "pending_settlements": {
                "value": pending_settlements_count,
                "label": "Pending Settlements",
                "icon": "fa-inbox",
                "color": "warning",
                "currency": False,
            },
            "approved_advances": {
                "value": approved_advances_count,
                "label": "Awaiting Payment",
                "icon": "fa-clock-o",
                "color": "secondary",
                "currency": False,
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics chart 1 — Advance Type Distribution (pie chart)
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_advance_type_distribution(
        self, date_from, date_to, request_type, department_id, employee_id, company_id=None
    ):
        """
        Compute advance distribution by request type for the pie chart.

        Queries petty.cash.request grouped by request_type, then sums the
        linked advance amounts.  Only requests that have a linked advance are
        counted so the pie reflects real money movement rather than just
        request volume.

        Returns:
            list: [
                {
                    "type":       str,   # internal selection key
                    "label":      str,   # human-readable label
                    "amount":     float, # total advance amount for this type
                    "count":      int,   # number of requests of this type
                    "percentage": float, # share of total amount (0-100)
                    "color":      str,   # hex color
                },
                ...
            ]
            Sorted DESC by amount.  Empty list when there is no data.
        """
        # Build domain for requests
        domain = self._build_request_domain(
            date_from, date_to, request_type, department_id, employee_id, company_id
        )
        domain.append(("request_type", "!=", False))

        requests = self.env["petty.cash.request"].search(domain)

        type_colors = {
            "purchase":             "#FFC107",  # yellow
            "salary":               "#4CAF50",  # green
            "tour_travel":          "#2196F3",  # blue
            "operational_expenses": "#F44336",  # red
            "expense":              "#9C27B0",  # purple
            "other":                "#607D8B",  # blue-grey
        }

        type_labels = {
            "purchase":             "Purchase",
            "salary":               "Salary",
            "tour_travel":          "Tour & Travel",
            "operational_expenses": "Operational Exp.",
            "expense":              "Expense",
            "other":                "Other",
        }

        distribution = {}
        total_amount = 0.0

        for request in requests:
            req_type = request.request_type
            if not req_type:
                continue

            advance_amount = request.advance_id.amount if request.advance_id.exists() else 0.0

            if req_type not in distribution:
                distribution[req_type] = {
                    "type":   req_type,
                    "label":  type_labels.get(req_type, req_type.replace("_", " ").title()),
                    "amount": 0.0,
                    "count":  0,
                    "color":  type_colors.get(req_type, "#9E9E9E"),
                }

            distribution[req_type]["amount"] += advance_amount
            distribution[req_type]["count"]  += 1
            total_amount += advance_amount

        result = []
        for data in distribution.values():
            data["percentage"] = (
                round(data["amount"] / total_amount * 100, 1) if total_amount > 0 else 0.0
            )
            result.append(data)

        result.sort(key=lambda x: x["amount"], reverse=True)
        return result

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics chart 2 — Monthly Trend (line + bar combo chart)
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_monthly_trend(self, date_from, date_to, company_id=None):
        """
        Compute monthly advance issuance vs. settlement amounts for the last
        12 calendar months (regardless of the date_from / date_to filter so
        the trend always shows a full year of context).

        Iterates month-by-month and runs two targeted searches per month.
        This avoids loading all records into memory while remaining compatible
        with every Odoo 16/17/18 version (no read_group date-truncation
        quirks).

        Returns:
            list: [
                {
                    "month":            str,   # "YYYY-MM"  e.g. "2025-01"
                    "month_name":       str,   # "Jan"
                    "advances_issued":  float, # total advance amount issued this month
                    "settlements_done": float, # total settlement amount posted this month
                },
                ...
            ]
            Always 12 elements, ordered oldest → newest.
            Returns all-zero entries for months with no activity (so the
            chart x-axis is always fully populated).
        """
        Advance    = self.env["petty.cash.advance"]
        Settlement = self.env["petty.cash.settlement"]

        today      = fields.Date.today()
        # Start from the 1st of the month 11 months ago → gives a 12-month window
        start_date = (today - relativedelta(months=11)).replace(day=1)

        months_data   = []
        current_month = start_date

        for _ in range(12):
            month_start = current_month
            month_end   = (current_month + relativedelta(months=1)) - timedelta(days=1)

            m_start_str = fields.Date.to_string(month_start)
            m_end_str   = fields.Date.to_string(month_end)

            # ── Advances issued (paid/partially_settled/settled) ──────────────
            advance_domain = [
                ("date",  ">=", m_start_str),
                ("date",  "<=", m_end_str),
                ("state", "in", ["paid", "partially_settled", "settled"]),
            ]
            if company_id:
                advance_domain.append(("company_id", "=", company_id))

            advances        = Advance.search(advance_domain)
            advances_amount = sum(advances.mapped("amount"))

            # ── Settlements posted ────────────────────────────────────────────
            settlement_domain = [
                ("date",  ">=", m_start_str),
                ("date",  "<=", m_end_str),
                ("state", "=",  "posted"),
            ]
            if company_id:
                settlement_domain.append(("company_id", "=", company_id))

            settlements        = Settlement.search(settlement_domain)
            settlements_amount = sum(settlements.mapped("total_amount"))

            months_data.append({
                "month":            current_month.strftime("%Y-%m"),
                "month_name":       current_month.strftime("%b %Y"),  # "Jan 2025"
                "advances_issued":  advances_amount,
                "settlements_done": settlements_amount,
            })

            current_month += relativedelta(months=1)

        return months_data

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics chart 3 — Top Outstanding Employees (horizontal bar chart)
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_top_outstanding_employees(self, company_id=None, limit=10):
        """
        Return the top employees ranked descending by total outstanding
        advance balance (sum of `balance` across all their open advances).

        Color coding:
            balance > 100,000  →  red    (high risk)
            balance >  50,000  →  orange (medium risk)
            otherwise          →  blue   (low risk)

        Returns:
            list: [
                {
                    "employee_id":          int,
                    "employee_name":        str,
                    "outstanding_balance":  float,
                    "advance_count":        int,   # number of open advances
                    "color":                str,   # hex color
                },
                ...
            ]
            Sorted DESC by outstanding_balance, max `limit` rows.
            Empty list when there are no outstanding advances.
        """
        domain = [
            ("state",   "in", ["paid", "partially_settled"]),
            ("balance", ">",  0),
        ]
        if company_id:
            domain.append(("company_id", "=", company_id))

        advances = self.env["petty.cash.advance"].search(domain)

        # Group by employee in Python (avoids read_group date-field complications
        # and keeps the logic compatible with non-stored balance fields)
        employee_data = {}
        for adv in advances:
            emp_id = adv.employee_id.id
            if not emp_id:
                continue
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    "employee_id":         emp_id,
                    "employee_name":       adv.employee_id.name,
                    "outstanding_balance": 0.0,
                    "advance_count":       0,
                }
            employee_data[emp_id]["outstanding_balance"] += float(adv.balance)
            employee_data[emp_id]["advance_count"]       += 1

        # Sort descending and cap at limit
        sorted_employees = sorted(
            employee_data.values(),
            key=lambda x: x["outstanding_balance"],
            reverse=True,
        )[:limit]

        # Apply risk-based color
        for item in sorted_employees:
            b = item["outstanding_balance"]
            if b > 100_000:
                item["color"] = "#F44336"   # red   — high risk
            elif b > 50_000:
                item["color"] = "#FF9800"   # orange — medium risk
            else:
                item["color"] = "#2196F3"   # blue  — low risk

        return sorted_employees

    # ──────────────────────────────────────────────────────────────────────────
    # Analytics chart 4 — Request Status Funnel (horizontal bar / funnel chart)
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_request_status_funnel(self, domain_request):
        """
        Compute the request workflow funnel from petty.cash.request records.

        The five stages track a request from creation through full settlement.
        Each stage is a subset of all_requests (stages are not mutually
        exclusive by design — a settled request has passed through all stages).

        Stage definitions:
            requested      — state in ('draft', 'submitted')
            approved       — state == 'approved'
            paid           — linked advance state in ('paid', 'partially_settled', 'settled')
            bills_submitted — at least one linked settlement in 'submitted' state
            settled        — at least one linked settlement in 'posted' state

        Returns:
            list: [
                {
                    "stage":      str,   # internal key
                    "label":      str,   # human-readable
                    "count":      int,
                    "percentage": float, # share of total request count (0-100)
                    "color":      str,   # hex color
                },
                ...
            ]
            Five elements in logical workflow order.
            Empty list when there are no requests matching the domain.
        """
        Request = self.env["petty.cash.request"]

        all_requests = Request.search(domain_request)
        total_count  = len(all_requests)

        if total_count == 0:
            return []

        def _pct(n):
            return round(n / total_count * 100, 1)

        # Stage 1: Requested (draft or submitted, pending approval)
        requested = all_requests.filtered(lambda r: r.state in ("draft", "submitted"))

        # Stage 2: Approved
        approved = all_requests.filtered(lambda r: r.state == "approved")

        # Stage 3: Paid (linked advance disbursed)
        paid = all_requests.filtered(
            lambda r: r.advance_id.exists()
            and r.advance_id.state in ("paid", "partially_settled", "settled")
        )

        requests_with_advances = all_requests.filtered(lambda r: r.advance_id.exists())

        # Stage 4: Bills Submitted (has at least one settlement in 'submitted')
        bills_submitted = requests_with_advances.filtered(
            lambda r: any(s.state == "submitted" for s in r.advance_id.settlement_ids.exists())
        )

        # Stage 5: Fully Settled (has at least one posted settlement)
        settled = requests_with_advances.filtered(
            lambda r: any(s.state == "posted" for s in r.advance_id.settlement_ids.exists())
        )

        return [
            {
                "stage":      "requested",
                "label":      "Requested",
                "count":      len(requested),
                "percentage": _pct(len(requested)),
                "color":      "#9E9E9E",
            },
            {
                "stage":      "approved",
                "label":      "Approved",
                "count":      len(approved),
                "percentage": _pct(len(approved)),
                "color":      "#FFC107",
            },
            {
                "stage":      "paid",
                "label":      "Paid",
                "count":      len(paid),
                "percentage": _pct(len(paid)),
                "color":      "#2196F3",
            },
            {
                "stage":      "bills_submitted",
                "label":      "Bills Submitted",
                "count":      len(bills_submitted),
                "percentage": _pct(len(bills_submitted)),
                "color":      "#FF9800",
            },
            {
                "stage":      "settled",
                "label":      "Settled",
                "count":      len(settled),
                "percentage": _pct(len(settled)),
                "color":      "#4CAF50",
            },
        ]

    # ──────────────────────────────────────────────────────────────────────────
    # Supporting data — recent activities feed
    # ──────────────────────────────────────────────────────────────────────────

    def _get_recent_activities(self, limit=20, company_id=None):
        """
        Get recent activities feed (last 30 days).

        Collects three event types and merges them into a single list sorted
        newest-first:
            - advance   : advances that reached 'paid' state
            - settlement: settlements that were posted
            - overdue   : advances whose expected_settlement_date passed in the
                          last 7 days and still carry a balance

        Returns:
            list: [
                {
                    "type":        str,
                    "icon":        str,   # Font Awesome class e.g. "fa-money"
                    "color":       str,   # hex color
                    "description": str,
                    "employee":    str,
                    "amount":      float,
                    "date":        date,
                    "record_id":   int,
                    "model":       str,
                },
                ...
            ]
            Sorted DESC by date, capped at `limit`.
        """
        activities = []
        today      = fields.Date.today()

        # ── Recent advances (last 30 days, paid/partially_settled/settled) ────
        advance_domain = [
            ("date",  ">=", fields.Date.to_string(today - timedelta(days=30))),
            ("state", "in", ["paid", "partially_settled", "settled"]),
        ]
        if company_id:
            advance_domain.append(("company_id", "=", company_id))

        for adv in self.env["petty.cash.advance"].search(
            advance_domain, order="date desc", limit=10
        ):
            activities.append({
                "type":        "advance",
                "icon":        "fa-money",
                "color":       "#4CAF50",
                "description": f"New Advance: {adv.employee_id.name}",
                "employee":    adv.employee_id.name,
                "amount":      adv.amount,
                "date":        adv.date,
                "record_id":   adv.id,
                "model":       "petty.cash.advance",
            })

        # ── Recent settlements (last 30 days, posted) ─────────────────────────
        settlement_domain = [
            ("date",  ">=", fields.Date.to_string(today - timedelta(days=30))),
            ("state", "=",  "posted"),
        ]
        if company_id:
            settlement_domain.append(("company_id", "=", company_id))

        for settle in self.env["petty.cash.settlement"].search(
            settlement_domain, order="date desc", limit=10
        ):
            activities.append({
                "type":        "settlement",
                "icon":        "fa-check-circle",
                "color":       "#2196F3",
                "description": f"Settlement Done: {settle.employee_id.name}",
                "employee":    settle.employee_id.name,
                "amount":      settle.total_amount,
                "date":        settle.date,
                "record_id":   settle.id,
                "model":       "petty.cash.settlement",
            })

        # ── Overdue alerts (overdue within the last 7 days) ───────────────────
        overdue_domain = [
            ("state",                    "in", ["paid", "partially_settled"]),
            ("balance",                  ">",  0),
            ("expected_settlement_date", "<",  today),
            ("expected_settlement_date", ">=", fields.Date.to_string(today - timedelta(days=7))),
        ]
        if company_id:
            overdue_domain.append(("company_id", "=", company_id))

        for overdue in self.env["petty.cash.advance"].search(
            overdue_domain, order="expected_settlement_date desc", limit=5
        ):
            days_overdue = (today - overdue.expected_settlement_date).days
            activities.append({
                "type":        "overdue",
                "icon":        "fa-exclamation-triangle",
                "color":       "#F44336",
                "description": f"Overdue Alert: {overdue.employee_id.name} - {days_overdue} days",
                "employee":    overdue.employee_id.name,
                "amount":      overdue.balance,
                "date":        overdue.expected_settlement_date,
                "record_id":   overdue.id,
                "model":       "petty.cash.advance",
            })

        # Merge and cap
        activities.sort(key=lambda x: x["date"], reverse=True)
        return activities[:limit]

    # ──────────────────────────────────────────────────────────────────────────
    # Supporting data — alert counts
    # ──────────────────────────────────────────────────────────────────────────

    def _get_alerts(self, company_id=None):
        """
        Return alert counts displayed in the Alerts notification box.

        Returns:
            dict: {
                "overdue_advances_count": int,  # advances past expected_settlement_date
                "missing_bills_count":    int,  # paid > 30 days ago with no settlement at all
            }
        """
        today  = fields.Date.today()
        Advance = self.env["petty.cash.advance"]

        # Overdue advances
        overdue_domain = [
            ("state",                    "in", ["paid", "partially_settled"]),
            ("balance",                  ">",  0),
            ("expected_settlement_date", "<",  today),
        ]
        if company_id:
            overdue_domain.append(("company_id", "=", company_id))

        # Missing bills (paid more than 30 days ago with no settlement record)
        cutoff_date = today - timedelta(days=30)
        missing_bills_domain = [
            ("state",           "in", ["paid", "partially_settled"]),
            ("date",            "<=", fields.Date.to_string(cutoff_date)),
            ("balance",         ">",  0),
            ("settlement_ids",  "=",  False),
        ]
        if company_id:
            missing_bills_domain.append(("company_id", "=", company_id))

        return {
            "overdue_advances_count": Advance.search_count(overdue_domain),
            "missing_bills_count":    Advance.search_count(missing_bills_domain),
        }
