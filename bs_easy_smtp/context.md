# Context: bs_easy_smtp

## Status
v1 build complete: module installs cleanly on Odoo 19 and all 6 tests pass (verified via
odoo-bin against a throwaway local DB, since dropped). Static analysis (ruff, appstore
validator) clean. Price left as placeholder per spec -- not yet confirmed with user.

## Technical name
bs_easy_smtp (final — no naming step needed)

## Odoo version / branch
19.0 — branch: addon_bs_easy_smtp_19.0

## File inventory (what exists, one line each)
- models/bs_easy_smtp_preset.py — done (provider/host/port/encryption/credential_note/url)
- data/bs_easy_smtp_preset_data.xml — done, all 8 providers incl. custom (blank host)
- models/bs_easy_smtp_wizard.py — done: state field (provider/credentials), onchange
  autofill, action_test_send (via ir.mail_server._build_email__/send_email in-memory,
  nothing persisted), action_save (create-or-write existing_mail_server_id)
- models/ir_mail_server.py (inherit) — done: _bs_easy_smtp_decode_error() shared decoder
  + test_smtp_connection() override that re-decodes the native button's UserError
- views/bs_easy_smtp_wizard_views.xml — done: form (state-gated groups/footers), act_window,
  menuitem under base.menu_email (group base.group_system, not group_no_one -- meant for
  non-technical admins, not just devs)
- views/ir_mail_server_views.xml — intentionally NOT created, see deviation below
- security/ir.model.access.csv — done (preset: read-only group_system; wizard: full CRUD group_system)
- tests/test_bs_easy_smtp.py — done, 6 tests: preset autofill (all providers), error
  decoder categories (auth/timeout/ssl/relay/fallback), test-send persists nothing,
  save requires successful test, save creates when no server exists, re-run updates
  existing server without duplicating + leaves an unrelated server untouched

## Key decisions made (not already in the spec)
- Repo's own two-step wizard convention confirmed via bs_smart_invoice_import/wizard/quick_paste_wizard.py:
  `state` Selection field, transition methods do `self.write({...})` then return a
  `_reopen_action()` dict (act_window, target=new, res_id=self.id) -- plain truthy return
  would close the target=new dialog. Odoo 19 view syntax uses `invisible="python expr"`
  directly, no `attrs=` dict. Mirrored exactly in bs_easy_smtp_wizard.py / its views.
- Test-send reuses `ir.mail_server._build_email__()` + `.send_email(message, smtp_server=...,
  smtp_port=..., smtp_user=..., smtp_password=..., smtp_encryption=...)` with no
  `mail_server_id` -- confirmed by reading core (base/models/ir_mail_server.py) that this
  path never touches a persisted record; it builds a real message and really sends it,
  which is what spec 4.3 wants (a real test email), unlike core's own `test_smtp_connection`
  which deliberately stops before DATA and never sends anything.
- No separate "advanced/manual edit" toggle field for autofilled host/port/encryption (UX
  flow 8.2 mentions one in prose) -- data model in spec section 6 has no such field, and
  spec 7.2 just says fields "remain editable afterward". Implemented as always-editable,
  simpler, matches the authoritative field table.
- Checked Odoo 19 core (/home/bs-00776/odoo19/odoo/addons/base/models/ir_mail_server.py):
  Odoo 19 core ALREADY ships a native "Test Connection" button (`test_smtp_connection()`)
  on the ir.mail_server form (base/views/ir_mail_server_views.xml:9). This makes spec
  section 4.6 / 7.6 ("Re-test Existing Server" smart button) largely redundant in v19 —
  planning to NOT add a duplicate button, and instead override `test_smtp_connection`
  minimally to route its raised UserError through our shared plain-language decoder, so
  the native button also benefits without a duplicate button/view. Will flag this
  deviation to the user.
- `ir.mail_server._connect__()` already accepts host/port/user/password/encryption/smtp_from
  directly (no persisted record needed) when no `mail_server_id` is passed — this is exactly
  the "in-memory dict" test-send mechanism the spec wants. Wizard test-send will call this
  directly instead of building a custom SMTP client.
- `smtp_encryption` selection in v19 core has 5 values: none/starttls/starttls_strict/ssl/ssl_strict.
  Spec only lists 3 (none/starttls/ssl). Plan: wizard field mirrors the 3 spec values (presets
  only ever set these 3); still valid subset of the real field's selection so no conflict.

## Deviations from the spec (if any, and why)
- Not adding a separate/duplicate "Test Connection" smart button on ir.mail_server — Odoo 19
  core already has one. Will instead hook its error path into the shared decoder. See above.

## Open questions / blockers
- Final price ($19 estimate in spec) not confirmed -- placeholder 0.00 left in manifest
  per build guardrail (stop and ask before confirming final price).

## Next step
Nothing pending for v1 functionality. If asked to continue: confirm price with user,
then optionally add appstore listing assets (icon/screenshots/index.html) as a separate
follow-up commit, matching how bs_simple_invoice did it (functionality first, listing
assets later) -- not part of this build's 15 steps.
