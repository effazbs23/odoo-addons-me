# Smart KPI Dashboard

Type a KPI request in plain English, get a live chart — no external AI API, no data leaves your server.

**Smart KPI Dashboard** adds a natural-language prompt bar to Odoo 19. Ask for *"revenue by region this quarter, bar chart"* and the module resolves your words into a safe, allow-listed query on your own data, then renders it as a live Chart.js visualization — all locally, nothing is sent to any third-party AI service.

## Key Features

### Natural Language Parsing
- Type plain English prompts like "revenue by region this quarter, bar chart"
- Typo-tolerant fuzzy matching — misspellings still resolve correctly
- Typeahead suggestions scoped to the current user's permissions
- "Top N" / "lowest performing" sort phrases handled automatically
- Time-range phrases: "this quarter", "YTD", "past week", "last month"

### Dashboard & Saved Tiles
- Pin any KPI result to a personal dashboard as a saved tile
- Live re-fetch on every load — no stale cached data
- Share tiles with users who independently pass access checks
- Kanban board grouped by source model with drag-to-resize
- Chart.js rendering bundled with Odoo — no new frontend dependencies

### Security & Vocabulary
- Single allow-list gate — nothing is queryable by default
- Odoo's own ACLs enforced on top of the allow-list
- Manual vocabulary editing — no code changes, no restart
- Auto-discovery of new models with admin review queue
- Unmatched-phrase telemetry ranked by recurrence

## How It Works

1. **Prompt** — the user types a request in plain English.
2. **Parse** — the local parser (no external AI API) extracts the source model, measure(s), grouping field, time range, chart type and sorting from the phrase, using synonyms and fuzzy matching.
3. **Validate** — every spec is checked against the admin-managed allow-list *and* the requesting user's own record rules / ACLs before anything is queried.
4. **Render** — the query result is returned live and drawn as a bar, pie, trend line or single-value tile.
5. **Pin** — results can be saved as personal dashboard tiles and optionally shared with other users (who must still independently pass all access checks).

## Requirements

- Odoo 19.0 Community or Enterprise
- Depends on: `base`, `web`, `sale`, `account`, `crm`, `stock`

## Installation

1. Copy the `bs_smart_kpi_dashboard` folder into your Odoo addons path.
2. Update the apps list (*Apps → Update Apps List*).
3. Search for **Smart KPI Dashboard** and click **Install**.

## Configuration

Go to *Settings → Smart KPI Dashboard* to manage:

- **Allow-list** — which models/fields are queryable at all. Nothing is queryable until you allow it.
- **Synonyms** — teach the parser your business vocabulary (e.g. map "clients" to `res.partner`) without code changes or restarts.
- **Unmatched phrases** — telemetry of prompts that could not be resolved, ranked by recurrence, so you know exactly what vocabulary to add next.
- **Cron auto-discovery** — new models are proposed for review instead of being silently exposed.

## Security Model

Security is enforced in layers:

1. **Allow-list gate** — only explicitly allowed models/fields can ever be queried.
2. **Odoo ACLs & record rules** — enforced on top of the allow-list for every user, on every load.
3. **Per-user share checks** — shared tiles are re-validated per viewer; sharing never leaks data a viewer cannot otherwise see.

Every tile re-validates its full spec against these layers each time it loads.

## Support

- Website: <https://erp-23.com>
- Email: <erp23@brainstation-23.com>

## License

OPL-1 (Odoo Proprietary License v1.0) — © ERP23 / Brain Station 23.
