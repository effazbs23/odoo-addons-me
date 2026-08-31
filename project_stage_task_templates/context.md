# Context: project_stage_task_templates

## Status
Functionally complete. Models, wizard, views, security, and tests all
written, committed, and verified against a real Odoo 19.0 install (module
installs cleanly + all 17 backend tests pass). Remaining: human naming
decision (3 candidates prepped, not yet picked) and final price confirmation
before shipping.

## Technical name
project_stage_task_templates (placeholder — naming step pending, see spec intro "bs_project_task_templates" as working name)

## Odoo version / branch
19.0 — branch: addon_project_stage_task_templates_19.0 (created from origin/19.0, clean reset)

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

## Deviations from the spec (if any, and why)
- Data model section 6 said one `stage_id` field on the template. Split into `task_stage_id` / `project_stage_id` as above — required because Odoo 19 doesn't have a single shared stage model between project and task. Documented here per guardrail (checked real 19.0 source before deviating, didn't guess).

## Open questions / blockers
- None currently. Waiting on human input for two things (guardrail: must not auto-decide): naming candidate pick, final price.

## Next step
1. Ask user to pick technical name from 3 candidates (prepped: bs_project_task_templates / bs_stage_task_templates / bs_project_stage_checklist), then rename module dir + `_name`-adjacent references (manifest `name` stays human-readable; only the folder/addon technical name changes) and update this file's "Technical name" field.
2. Confirm final price (spec's $35 is a placeholder, not final) — currently 0.00 in manifest.
3. Optional polish not yet done, not spec-required: static analysis (pylint-odoo / flake8) hasn't been run — only py_compile + a live install/test pass so far.
