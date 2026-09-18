# Landed Cost Auto-Allocator

Automatically splits freight, duty and customs charges across a purchase
order's receipt lines by weight, volume, or value — in one click.

Built directly on top of core `stock_landed_costs`. This module automates the
split calculation that Odoo already lets you enter manually; it does not
replace the landed-cost accounting flow itself.

## Features

- **One-click Auto-Allocate** button on a Landed Cost: suggests an allocation
  method per cost line from reusable rule templates, runs a pre-flight
  data-quality check, then lets core compute the actual split.
- **Reuses core's `split_method`** (Equal, By Quantity, By Current Cost, By
  Weight, By Volume) on landed cost lines — no parallel allocation field, no
  reimplemented split math.
- **Rule templates** ("always allocate DHL freight by weight") matched by
  vendor and/or cost-type product, with a documented priority order.
- **Mixed allocation on the same record**: freight by weight, duty by value,
  customs by quantity — each cost line keeps its own method.
- **Allocation Preview**: weight/volume/value columns alongside the valuation
  adjustment lines, so the split can be sanity-checked before posting.
- **Allocation audit trail**: a human-readable formula breakdown stored per
  adjustment line for finance review.
- **Data-quality guardrail**: blocks allocation when a `By Weight`/`By Volume`
  split would be run against products with no weight/volume set, listing the
  offending products.

## Installation

1. Copy the `bs_landed_cost_auto_allocator` directory into your Odoo addons path.
2. Update the apps list (`Apps` → `Update Apps List`).
3. Install **Landed Cost Auto-Allocator**.

Dependencies: `stock_landed_costs`, `purchase`.

## Configuration

### Allocation rules

Before using Auto-Allocate, define your reusable rules under:

`Inventory → Configuration → Landed Cost Allocation Rules`

Each rule maps a scope to an allocation method:

| Field | Purpose |
|---|---|
| **Vendor** | Restrict the rule to a specific vendor; leave empty to match any vendor. |
| **Cost Type** | Restrict to a specific cost-type product (the service product used on the cost line, e.g. *Freight*, *Duty*, *Customs*); leave empty to match any. |
| **Allocation Method** | The `split_method` written onto the matching cost line. |
| **Sequence** | Tie-breaker when several rules could match (lower runs first). |

**Rule matching priority** (highest first):

1. Exact vendor + cost-type match.
2. Cost-type-only rule (no vendor set on the rule).
3. Vendor-only rule (no cost type set on the rule).

Within a tier, ties are broken by `sequence` ascending, then `id`.

## Usage

1. Open an existing Landed Cost in *Draft* state (`Inventory → Operations →
   Landed Costs`, or from a receipt's *Vendor Bills* tab).
2. Add your cost lines (Freight, Duty, Customs, …) and amounts as usual.
3. Click **Auto-Allocate**. The module will:
   - apply the best-matching allocation rule's method to each cost line that
     has a matching rule (a line with no match keeps whatever method it
     already has);
   - run the weight/volume data-quality pre-flight check, blocking with a
     clear error if any product is missing data a `By Weight`/`By Volume`
     line needs;
   - compute the split using core's own `compute_landed_cost()`;
   - populate an **Allocation Breakdown** formula per valuation adjustment
     line.
4. Review the **Allocation Preview** (weight/volume/value columns) and the
   **Audit Trail**; click **Details** (info icon) on any adjustment line to
   read the full formula behind its allocation.
5. Validate and post the landed cost exactly as before.

> **Note**: re-running Auto-Allocate re-applies matching rules and overwrites
> the cost lines' methods. For a one-off manual override, either don't re-run
> Auto-Allocate for that record or narrow the rule so it no longer matches.

## Security

| Group | Access |
|---|---|
| `stock.group_stock_user` (Inventory User) | Read-only on allocation rules. |
| `stock.group_stock_manager` (Inventory Manager) | Full read/write/create/delete on allocation rules and Auto-Allocate. |

## Testing

Automated tests are bundled in `tests/`:

```bash
odoo --test-enable -i bs_landed_cost_auto_allocator -d <db>
```

Coverage includes rule-matching priority order, the data-quality check (raises
for missing weight, passes with complete data), mixed allocation with
independently-correct per-line amounts, and populated allocation breakdowns.

## Changelog

See `CHANGELOG.md`.