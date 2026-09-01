# Context: whatsapp_sms_order_invoice_notifier

## Status
Scaffolding started. Models not yet written.

## Technical name
bs_whatsapp_sms_order_invoice_notifier (placeholder — final name pending odoo-addon-namer step)

## Odoo version / branch
19.0 — branch: addon_bs_whatsapp_sms_order_invoice_notifier_19.0 (branched from origin/19.0)

## File inventory (what exists, one line each)
- models/bs_notify_gateway_config.py — not started
- models/bs_notify_event_template.py — not started
- models/bs_notify_log.py (incl. central _send_notification dispatch) — not started
- models/gateway_adapters/ (one file per provider) — not started
- models/sale_order.py (inherit, so_confirmed hook) — not started
- models/stock_picking.py (inherit, delivery_shipped hook) — not started
- models/account_move.py (inherit, invoice_posted + payment_received hooks) — not started
- data/ir_cron_overdue_check.xml — not started
- views/... — not started
- security/ir.model.access.csv — not started
- tests/... — not started

## Key decisions made (not already in the spec)
- Odoo 19 lifecycle hook points confirmed by reading actual source at /home/bs-00776/odoo19/addons:
  - `sale.order.action_confirm()` at sale/models/sale_order.py:1166 — override, call super(), fire `so_confirmed` for orders in state `sale`.
  - `stock.picking.button_validate()` at stock/models/stock_picking.py:1399 — override, call super(), fire `delivery_shipped` for pickings that reached state `done` AND picking_type_id.code == 'outgoing' (customer deliveries only).
  - `account.move._post(soft=True)` at account/models/account_move.py:5526 — override, call super() to get the actual posted recordset (super only returns moves posted now, not soft-scheduled ones), fire `invoice_posted` for posted moves where move_type in ('out_invoice','out_refund').
  - `payment_received`: no direct "on paid" hook exists in core. `payment_state` is a stored computed field (`_compute_payment_state` at account_move.py:1220). Chosen approach: override `_compute_payment_state`, snapshot `payment_state` per record before calling super(), then after super(), for records where old != 'paid' and new == 'paid', fire `payment_received`. Deliberately NOT firing on `in_payment` (spec says "fully paid" only).
- No wizard needed — manual resend is a plain button/method on bs.notify.log and on source records, not a wizard flow.
- Existing repo module `bs_whatsapp_communication` (unmerged branch `addon_bs_whatsapp_communication_19.0`) is unrelated: it's a manual "click to open WhatsApp Web" wizard per-record, no gateway API, no SMS, no automated triggers, no delivery log. Confirmed no functional/technical overlap — different mechanism entirely. Worth flagging in the naming step so the two aren't confused on the app store.

## Deviations from the spec (if any, and why)
- none yet

## Open questions / blockers
- none currently

## Next step
Write __manifest__.py, security groups, and the three core models (gateway_config, event_template, log) per spec section 6.
