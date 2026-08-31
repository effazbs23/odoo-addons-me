# Context: bs_project_task_templates

## Status
Done. Models, wizard, views, security, and tests all written, committed,
and verified two ways: (1) all 17 backend tests pass against a real
Odoo 19.0 install, (2) the full workflow was walked live in Chrome
(template setup, auto-creation + badge + chatter, confirm-mode queue +
wizard, bulk stage change, refire-policy idempotency, smart button,
per-project toggle) — found and fixed 2 UI bugs invisible to the unit
tests (see decisions log). Technical name and price both confirmed by
the user. 5 demo GIFs + a user manual produced from that session.

## Technical name
bs_project_task_templates (confirmed by user 2026-08-31, picked over
bs_stage_task_templates / bs_project_stage_checklist)

## Odoo version / branch
19.0 — branch: addon_bs_project_task_templates_19.0 (created from origin/19.0, clean reset)

## File inventory (what exists, one line each)
- models/project_stage_task_template.py — done: fields, constraints, automation entry point (`_process_stage_change`), assignee/deadline/placeholder resolution
- models/project_stage_task_template_log.py — done: audit + pending-confirmation queue (Reference field + `state`)
- models/project_task_type.py (inherit) — done: `stage_task_template_count` + smart button
- models/project_project.py (inherit) — done: two trigger-toggle Booleans + `write()` override
- models/project_task.py (inherit) — done: `generated_from_template_id` + `write()` override
- wizards/project_stage_template_confirm_wizard.py — done: wizard + line TransientModels
- views/project_stage_task_template_views.xml — done: list/form for templates + pending-confirmations list/action
- views/project_task_type_views.xml, project_project_views.xml, project_task_views.xml, project_menus.xml — done
- wizards/project_stage_template_confirm_wizard_views.xml — done
- security/ir.model.access.csv — done (manager full CRUD on templates/log, project_user read-only on templates, read+confirm on log/wizard)
- tests/test_stage_task_templates.py — done: 17 tests covering all 6 spec-10 scenarios, passing against real Odoo 19

## Key decisions made (not already in the spec)
- **Spec gap found via source check (odoo19/addons/project)**: `project.project.stage_id` points to model `project.project.stage`, while `project.task.stage_id` points to `project.task.type` — these are TWO DIFFERENT stage models in real Odoo 19, not one shared `project.task.type` as spec section 6 implies. Fix: template model gets two nullable Many2one fields — `task_stage_id` (→ project.task.type, used when trigger_level='task') and `project_stage_id` (→ project.project.stage, used when trigger_level='project') — only the relevant one is shown/required per trigger_level in the view.
- `project.task.priority` Selection is `[('0','Low'),('1','Medium'),('2','High'),('3','Urgent')]` — template's `priority` field mirrors this exactly (same string values) so it can be passed straight through to created tasks.
- `project.task` assignee field is `user_ids` (Many2many, multi-assignee since Odoo 17+), not a single `user_id`. `same_as_source` assignee rule copies `user_ids` from the source task. For project-level triggers, `same_as_source` has no natural source assignee (project.project has no assignee field, only `user_id`=Project Manager which is already its own rule) — falls back to unassigned + logged warning, same code path as the "no assignee" edge case in spec section 9.
- Per-project trigger scope toggle (spec 4.2) implemented as two Boolean fields on `project.project`: `stage_template_trigger_project` and `stage_template_trigger_task`, both default True. These gate whether templates fire at all for that project; `trigger_level` on the template itself determines which event type it's defined for.
- Smart button (spec section 6) added only to `project.task.type` per spec text, not duplicated onto `project.project.stage` — discoverability for project-level templates is via the main config list view instead, to avoid unrequested extra UI.
- Confirm-mode wizard is a persistent queue (`project.stage.task.template.log` rows with `state='pending'`), reviewed on demand from a "Pending Template Confirmations" list — not a modal popped straight out of `write()`. Odoo's kanban drag-and-drop stage change goes through a plain `write()` RPC whose return value the client doesn't use to open dialogs, so a synchronous popup isn't reliable there.
- res.users field is `group_ids` in Odoo 19, not `groups_id` — caught by running tests against real 19.0 source, not guessed.
- Two UI bugs only visible when actually rendering the views (unit tests don't catch these — they call the ORM directly): (1) the "Auto-generated" badge on the task form truncated to "Auto-ge…" because it shared a flex row with the (intentionally text-truncate'd) title without its own `flex-shrink:0` — fixed by adding `flex-shrink-0`. (2) the confirm wizard's line list never rendered `log_id`, so the web client silently dropped it from the save payload and "Confirm" failed with a required-field error — fixed by adding `log_id` as `column_invisible="1"` so it's part of the fields spec sent on save.
- A leftover empty `static/description/index.html` (from an unrelated App-Store-listing pipeline that had generated icon.png/banner.gif/main_screenshot.png but not yet the description page) crashed the whole module registry on install (`lxml.etree.ParserError: Document is empty` — Odoo treats a present-but-unparseable index.html as the module's long description and errors on `_check()`). Deleted the empty file; the three image assets are left in place for the index-generator step.

## Deviations from the spec (if any, and why)
- Data model section 6 said one `stage_id` field on the template. Split into `task_stage_id` / `project_stage_id` as above — required because Odoo 19 doesn't have a single shared stage model between project and task. Documented here per guardrail (checked real 19.0 source before deviating, didn't guess).

## Open questions / blockers
- None. User confirmed 2026-08-31: keep `price: 0.00` (free/internal for now, no pricing-advisor tool was available in this environment to re-derive the spec's $35 estimate).

## Next step
None outstanding for the module itself. Optional/not spec-required if
picked up later: static analysis (pylint-odoo/flake8) hasn't been run —
only py_compile + a live install/test pass + a full manual UI walkthrough
against real Odoo 19 so far. Separately, the module's App Store
`static/description/index.html` listing page still needs to be generated
(assets are in place: icon.png, banner.gif, main_screenshot.png) via the
`odoo-module-index-generator` skill — handed off to a separate agent.
