# AMC Management

Annual Maintenance Contracts for Odoo 19, built on Purchase and Accounting only.

## What it does

An AMC is paid once and consumed all year. This module accrues it month by month,
tracks whether each service visit actually happened, and bills the vendor against the
accrual.

1. **Flag the order** — tick *AMC Order* on an RFQ. Line products are restricted to
   services, enforced both by the view domain and by a Python constraint.
2. **Confirm** — one `amc.contract` (Mother AMC) is raised per order line, each cut into
   `Number of Service Periods` child periods. A contract spanning whole months that
   divide evenly by the frequency is cut on the calendar (15 Jan → 14 Feb); anything
   else is split evenly by days with the remainder handed to the earliest periods.
3. **Mark as Signed** — one button on the purchase order. It signs every Mother AMC the
   order carries and generates the monthly provision entries in draft:
   `Dr AMC Expense / Cr AMC Provision`, one debit/credit pair per site, one entry per
   order per month (enforced by a partial unique index). Months already past are folded
   into a single catch-up entry.
4. **Close service periods** — *Mark as Done*, *Partially Serviced* or *Expired*. The
   last two create a standalone draft reversal entry for the non-serviced days; existing
   provision entries are never edited.
5. **Bill the vendor** — the milestone wizard reads the order's payment term to decide
   how many bills the contract splits into and how much each carries, refuses to skip or
   duplicate a milestone, posts the line against the provision account, and copies the
   selected periods' service reports plus the signed contract onto the bill.

## Configuration

| Where | What |
|---|---|
| Product Category | **AMC Provision Account** — credited by provisions, debited by AMC bills |
| Product / Category | **Expense Account** — debited by provisions |
| AMC → Configuration → Settings | Provision journal (defaults to the first miscellaneous journal), expiry reminder days |
| AMC → Configuration → Sites | Buildings/plants, each with a code and an analytic account |

## Models

| Model | Purpose |
|---|---|
| `amc.site` | Place a contract is served at; carries the analytic account |
| `amc.contract` | Mother AMC and its service periods, told apart by `parent_amc_id` |
| `amc.mark.done.wizard` / `amc.partial.service.wizard` / `amc.expire.period.wizard` | Period closure, sharing `amc.service.period.wizard.mixin` |
| `amc.vendor.bill.wizard` | Milestone vendor billing |
| `amc.schedule.report.wizard` | Filters for the XLSX schedule |
| `amc.report.xlsx` | Self-contained XLSX report base (no `report_xlsx` dependency) |

Extended: `purchase.order`, `purchase.order.line`, `account.move`, `account.move.line`,
`product.category`, `res.config.settings`, `ir.actions.report`.

## Notes

- Contract values are taken **net of tax** (`price_subtotal`), because the provisions
  accrue an expense and the milestone bills are raised net as well.
- Provisions book plain debit/credit, which Odoo reads in company currency, so a
  foreign-currency order is converted at the order date.
- Provision and reversal entries are always created in **draft** for accounting review.
- Every `account.move` touch runs as `sudo`: AMC roles drive the workflow but are not
  required to hold accounting access.

## Licence

Odoo Proprietary License v1.0 (OPL-1) — paid module on the Odoo App Store.
