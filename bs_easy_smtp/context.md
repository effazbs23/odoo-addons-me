# Context: bs_easy_smtp

## Status
Branch + scaffold done. Researching Odoo 19 wizard state-field conventions before writing models.

## Technical name
bs_easy_smtp (final — no naming step needed)

## Odoo version / branch
19.0 — branch: addon_bs_easy_smtp_19.0

## File inventory (what exists, one line each)
- models/bs_easy_smtp_wizard.py — not started
- data/bs_easy_smtp_preset_data.xml — not started
- models/ir_mail_server.py (inherit, error-decode hook) — not started
- views/bs_easy_smtp_wizard_views.xml — not started
- views/ir_mail_server_views.xml (inherit) — not started
- security/ir.model.access.csv — not started
- tests/... — not started

## Key decisions made (not already in the spec)
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
- Waiting on research into repo's existing wizard state-field pattern (in-progress).

## Next step
Read back the wizard-convention research, then implement models/bs_easy_smtp_preset.py +
data file first (per build step 5).
