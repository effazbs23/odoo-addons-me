# Context: whatsapp_sms_order_invoice_notifier

## Status
Functionally complete. All code written, tested against a real Odoo 19 DB (17/17 automated tests green), and walked through live in the browser end-to-end (SO confirm -> delivery -> invoice -> payment -> resend), including real outbound HTTP calls to Twilio/Meta-shaped and generic REST endpoints (401s against fake creds proved the non-blocking guarantee for real; httpbin.org proved a real send + resend succeeding). index.html app-store listing finished with 12 real screenshots. Remaining: naming (3 candidates, human picks per guardrail), pricing/tier confirmation (deferred to pricing advisor per spec section 12), then squash-and-PR per bs23-commit-guidelines.

## Technical name
bs_whatsapp_sms_order_invoice_notifier — CONFIRMED by user after odoo-addon-namer research (3 candidates presented; user picked "Whatsapp/SMS Order and Invoice Notifier", which matches the existing manifest name/directory as-is, no rename needed).

## Odoo version / branch
19.0 — branch: addon_bs_whatsapp_sms_order_invoice_notifier_19.0 (branched from origin/19.0)

## File inventory (what exists, one line each)
- models/bs_notify_gateway_config.py — done (1 active gateway per channel/company, provider-channel constraint)
- models/bs_notify_event_template.py — done (global + per-company override)
- models/bs_notify_log.py (incl. central _send_notification dispatch) — done
- models/bs_notify_utils.py — done (E.164 regex + token renderer, shared with res_partner.py)
- models/gateway_adapters/ (meta_cloud_api, twilio, generic_rest) — done
- models/res_partner.py (has_valid_notify_number) — done
- models/sale_order.py (inherit, so_confirmed hook) — done
- models/stock_picking.py (inherit, delivery_shipped hook, outgoing only) — done
- models/account_move.py (invoice_posted + payment_received + overdue cron) — done
- data/ir_cron_overdue_check.xml, data/bs_notify_event_template_data.xml — done
- views/ (gateway config, event template, log, 3x smart-button inherits, menus) — done
- security/ir.model.access.csv — done (group_system for config, group_user read-only for log)
- tests/ (unit: phone/template/never-raises; integration: 5 triggers, guards, resend, no-phone, non-blocking regression) — done, 17/17 green against a real Odoo 19 DB
- static/description/ — icon.png, banner.gif, index.html (odoo-module-index-generator template, sanitizer-checked) + 12 real walkthrough screenshots, all committed.

## Key decisions made (not already in the spec)
- Odoo 19 lifecycle hook points confirmed by reading actual source at /home/bs-00776/odoo19/addons:
  - `sale.order.action_confirm()` at sale/models/sale_order.py:1166 — override, call super(), fire `so_confirmed` for orders in state `sale`.
  - `stock.picking.button_validate()` at stock/models/stock_picking.py:1399 — override, call super(), fire `delivery_shipped` for pickings that reached state `done` AND picking_type_id.code == 'outgoing' (customer deliveries only).
  - `account.move._post(soft=True)` at account/models/account_move.py:5526 — override, call super() to get the actual posted recordset (super only returns moves posted now, not soft-scheduled ones), fire `invoice_posted` for posted moves where move_type in ('out_invoice','out_refund').
  - `payment_received`: no direct "on paid" hook exists in core. `payment_state` is a stored computed field (`_compute_payment_state` at account_move.py:1220). Chosen approach: override `_compute_payment_state`, snapshot `payment_state` per record before calling super(), then after super(), for records where old != 'paid' and new == 'paid', fire `payment_received`. Deliberately NOT firing on `in_payment` (spec says "fully paid" only).
- No wizard needed — manual resend is a plain button/method on bs.notify.log and on source records, not a wizard flow.
- Existing repo module `bs_whatsapp_communication` (unmerged branch `addon_bs_whatsapp_communication_19.0`) is unrelated: it's a manual "click to open WhatsApp Web" wizard per-record, no gateway API, no SMS, no automated triggers, no delivery log. Confirmed no functional/technical overlap — different mechanism entirely. Worth flagging in the naming step so the two aren't confused on the app store.

## Deviations from the spec (if any, and why)
- Spec section 6 says "Uses the customer's mobile number from res.partner" and assumes a separate `mobile` field. Confirmed by an actual failed install (ValueError: Invalid field 'mobile' in 'res.partner') that Odoo 19 merged `mobile` into a single `phone` field on res.partner (checked odoo19/odoo/addons/base/models/res_partner.py -- only `phone = fields.Char()` remains, no `mobile` anywhere in base/sale/account/stock/contacts). All phone reads/validates use `partner.phone` instead. User-facing copy still says "mobile number" since that's still what the field represents functionally.
- `_sql_constraints` is deprecated in Odoo 19 (registry warning: "no longer supported, please define models.Constraint on the model"). bs.notify.event.template's unique constraint uses the new `models.Constraint(...)` class-attribute form instead.
- Manifest depends on `sale_stock` (not plain `stock`): plain `sale`+`stock` never actually wires delivery creation on SO confirm (no sale.order.picking_ids, no procurement) -- confirmed by a real AttributeError during testing. sale_stock is the bridge module and transitively pulls in sale/stock/account anyway.
- res.users.groups_id was renamed to group_ids in this Odoo 19 build (AttributeError caught while writing tests/common.py's group setup for the test user).

## Open questions / blockers
- none currently

## Next step
Naming and pricing are both confirmed (see above): name unchanged, price set to $9.00 / Paid tier. Module is functionally, visually, and commercially complete. Remaining: static analysis / final test pass per step 17, then squash-and-PR per bs23-commit-guidelines (this branch has many small commits by design; squash before opening the PR to development). Test env note: notify_test_db (local) now has an l10n_bd chart of accounts installed manually via `odoo-bin shell` (core had no journal for the company otherwise) -- this was a one-off local test-DB fix, not a module change.
