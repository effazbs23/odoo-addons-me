# Lot Recall Report

Generate an audit-ready recall report for any lot or serial number in one
click — tracing it forward to every customer, sales order and delivery it
touched, and backward to the vendor purchases and/or manufacturing orders that
fed it.

## Features

- **Forward trace**: every customer, sales order and delivery that received
  stock containing the lot.
- **Backward trace**: the vendor(s), purchase order(s) and/or manufacturing
  order that fed into the lot, plus one level of consumed component lots.
- **Multi-lot batch mode**: select several lots/serials for one consolidated
  report — e.g. an entire production run.
- **Trace direction control**: forward only, backward only, or both.
- **Impact dashboard**: customer / sales order / delivery counts and affected
  quantity forward; vendor / PO / MO counts and quantity backward.
- **Fully-traceable indicator**: flags green when every requested direction
  found movements, amber when one or more came back empty.
- **Print-ready PDF** and **XLSX export** (separate Forward Trace and Backward
  Trace sheets).
- **Searchable recall log** with chatter activity on every report — for
  compliance and audit purposes.

## Installation

1. Copy the `bs_lot_recall_report` directory into your Odoo addons path.
2. Update the apps list (`Apps` → `Update Apps List`).
3. Install **Lot Recall Report**.

Dependencies: `stock`, `sale_stock`, `mrp`, `purchase`, `mail`.

## Configuration

Select the **Recall Report / User** or **Manager** group for the users who
will generate and manage reports (`Settings → Users & Companies → Users →
Access Rights`).

Reports are multi-company aware: users only see reports belonging to their
companies (or to no company).

## Usage

### From a lot/serial record

1. Open a lot/serial number (`Inventory → Products → Lots/Serial Numbers`).
2. Click **Recall Report** (or the **Recall Reports** stat button once reports
   exist) in the top-right button box.

### From the menu

1. Go to **Inventory → Recall Reports**.
2. Click **New**, pick one or more **Lots/Serial Numbers** and the trace
   **Direction** (default: both).
3. Click **Generate Recall Report**.
4. Review the forward/backward dashboard and trace lines.
5. **Export PDF** or **Export XLSX** as needed; use **Recall Log** to open the
   full report history.

Generated reports are readonly; use **Reset to Draft** (via the state bar or
editing) to change lots/direction and regenerate.

## Security

| Group | Access |
|---|---|
| Recall Report / User | Read reports and lines, generate, export. |
| Recall Report / Manager | Full CRUD; implied the User group. |

`lot.recall.report` inherits `mail.thread`, so every generation and change is
logged in the report's chatter.

## Testing

Automated tests are bundled in `tests/`:

```bash
odoo --test-enable -i bs_lot_recall_report -d <db>
```

Coverage includes forward trace via sales deliveries, backward trace via
vendor receipts, and backward trace through manufacturing (component lots),
including regression coverage for Odoo 19's `mrp.production.lot_producing_ids`.

## Changelog

See `CHANGELOG.md`.