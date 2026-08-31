# Context: project_stage_task_templates

## Status
Starting build. Branch created, module skeleton created. Writing models next.

## Technical name
project_stage_task_templates (placeholder — naming step pending, see spec intro "bs_project_task_templates" as working name)

## Odoo version / branch
19.0 — branch: addon_project_stage_task_templates_19.0 (created from origin/19.0, clean reset)

## File inventory (what exists, one line each)
- models/project_stage_task_template.py — not started
- models/project_stage_task_template_log.py — not started
- models/project_task_type.py (inherit) — not started
- models/project_project_stage.py (inherit) — not started
- models/project_project.py (inherit) — not started
- models/project_task.py (inherit) — not started
- wizards/project_stage_template_confirm_wizard.py — not started
- views/... — not started
- security/ir.model.access.csv — not started
- tests/... — not started

## Key decisions made (not already in the spec)
- **Spec gap found via source check (odoo19/addons/project)**: `project.project.stage_id` points to model `project.project.stage`, while `project.task.stage_id` points to `project.task.type` — these are TWO DIFFERENT stage models in real Odoo 19, not one shared `project.task.type` as spec section 6 implies. Fix: template model gets two nullable Many2one fields — `task_stage_id` (→ project.task.type, used when trigger_level='task') and `project_stage_id` (→ project.project.stage, used when trigger_level='project') — only the relevant one is shown/required per trigger_level in the view.
- `project.task.priority` Selection is `[('0','Low'),('1','Medium'),('2','High'),('3','Urgent')]` — template's `priority` field mirrors this exactly (same string values) so it can be passed straight through to created tasks.
- `project.task` assignee field is `user_ids` (Many2many, multi-assignee since Odoo 17+), not a single `user_id`. `same_as_source` assignee rule copies `user_ids` from the source task. For project-level triggers, `same_as_source` has no natural source assignee (project.project has no assignee field, only `user_id`=Project Manager which is already its own rule) — falls back to unassigned + logged warning, same code path as the "no assignee" edge case in spec section 9.
- Per-project trigger scope toggle (spec 4.2) implemented as two Boolean fields on `project.project`: `stage_template_trigger_project` and `stage_template_trigger_task`, both default True. These gate whether templates fire at all for that project; `trigger_level` on the template itself determines which event type it's defined for.
- Smart button (spec section 6) added only to `project.task.type` per spec text, not duplicated onto `project.project.stage` — discoverability for project-level templates is via the main config list view instead, to avoid unrequested extra UI.

## Deviations from the spec (if any, and why)
- Data model section 6 said one `stage_id` field on the template. Split into `task_stage_id` / `project_stage_id` as above — required because Odoo 19 doesn't have a single shared stage model between project and task. Documented here per guardrail (checked real 19.0 source before deviating, didn't guess).

## Open questions / blockers
- None currently.

## Next step
Write models/project_stage_task_template.py and models/project_stage_task_template_log.py.
