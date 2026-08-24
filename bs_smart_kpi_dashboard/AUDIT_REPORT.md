# Smart KPI Dashboard (`bs_smart_kpi_dashboard`) — Production / App Store Audit Report

**Auditor role:** Senior Odoo Architect, Security Auditor, Production Release Reviewer
**Module version audited:** 19.0.1.0.0
**Audit method:** Static analysis only (full read of every Python/XML/JS/CSS file, manifest, security rules, data files, and cross-checked every referenced field/XML-ID against a local Odoo 19.0 core checkout). No server was started, nothing was installed or modified.
**Scope:** `/home/bs-00776/odoo_addons/bs_smart_kpi_dashboard`

---

## 1. Executive Summary

Smart KPI Dashboard is a natural-language-to-chart module: a user types a plain-English KPI request, a fully local/deterministic parser (no external AI, no network calls) turns it into a query spec, and the spec is validated against an admin-curated allow-list before it is ever executed against the ORM. The module is unusually disciplined for a paid App Store submission: every client-reachable entry point funnels through a single security gate (`ai.dashboard.allowlist._validate_spec`), record rules correctly separate "read own+shared" from "write/delete own only," `sudo()` is used exclusively on the module's own metadata tables (allow-list, synonym, unmatched-phrase, config parameter) and is **never** used to bypass ACLs on real business data (`sale.order`, `account.move`, `crm.lead`, `stock.move`), and the test suite specifically pins the security boundary (`test_validate_spec.py`) and the "one bad tile can't take down the dashboard" resilience contract.

No Critical or High severity issues were found. However, the audit surfaced a real gap in the domain-validation logic that **violates the module's own documented invariant** ("nothing reaches `formatted_read_group()` without clearing `_validate_spec()`"), a missing input-length guard on the free-text prompt that enables a CPU-cost attack from any authenticated internal user, an inconsistent access surface for portal users, and an unusually heavy hard-dependency footprint (`crm`, `stock` forced on every installation). All are fixable in a small patch; none require an architectural rewrite.

**Verdict: NEEDS MINOR CHANGES.**

---

## 2. Critical Issues

None found.

---

## 3. High Severity Issues

None found.

---

## 4. Medium Severity Issues

### M-1. Domain structural validation does not check operator/leaf balance — uncaught `ValueError` reachable from client-supplied specs

- **Issue:** `AiDashboardAllowlist._validate_spec()` (`models/ai_dashboard_allowlist.py:214-231`) validates each domain *token* independently — a `'&'`/`'|'`/`'!'` string is accepted outright, and each 3-tuple leaf is checked for an allow-listed field name — but it never verifies that the **overall prefix expression is balanced** (i.e., that every `'&'`/`'|'` has the two operands it requires). A spec such as `{'domain': ['&', ('team_id', '=', 1)]}` passes this validator cleanly (the lone `'&'` is a valid token, the lone leaf is a valid, allow-listed leaf), then reaches `Model.formatted_read_group()`, whose domain normalizer (`odoo/orm/domains.py`) raises a plain `ValueError` for a malformed/unbalanced domain — **not** `odoo.exceptions.ValidationError`.
- **Why it matters:** `controllers/main.py` only catches `ValidationError` around every call site (`generate`, `run_manual`, `tile/save`) — `except ValidationError as e:`. A `ValueError` raised deeper in `_run_and_format` / `_to_chart_payload` is not caught anywhere in the module and propagates as an unhandled exception out of the JSON-RPC endpoint.
- **Impact:** Any authenticated internal user (the `run_manual` and `tile/save` routes accept a client-built `spec` wholesale) can trigger a 500-level unhandled-exception response instead of the clean, user-facing `ValidationError` message the rest of the module is carefully designed to produce. This also means a **saved tile** can be created with such a domain (validation at save-time also only catches `ValidationError`) and will then throw the same uncaught exception every time `get_dashboard_tiles()` tries to render it — except that path *is* wrapped in a bare `except Exception` in `ai_dashboard_tile.py`, so the dashboard itself survives; the raw `generate`/`run_manual` calls do not have that safety net.
- **Exploitation scenario:** A logged-in employee (no special privileges needed) sends `POST /bs_smart_kpi_dashboard/run_manual` with `spec.domain = ["&", ["team_id", "=", 1]]`. The request 500s instead of returning a clean "Invalid filter" message; server logs record a full traceback for every such call, which is also a cheap way to spam the error log.
- **Fix:** In `_validate_spec`, walk the domain with a small arity counter (or use `odoo.orm.domains` normalization / `expression.is_leaf` + a running "operands needed" stack) and reject any domain whose logical operators don't balance against the leaf count, *before* accepting it. Alternatively, wrap the `formatted_read_group()` call itself in a `try/except (ValueError, Exception)` at the single call site (`ai_dashboard_tile.py::_run_spec`) and re-raise as `ValidationError`, which keeps the "one gate" design intact for every current and future caller.

### M-2. No length cap on free-text `prompt` — CPU-cost amplification via unconditional fuzzy matching

- **Issue:** `KpiPromptParser._consume_matches()` (`logic/kpi_prompt_parser.py:245-266`) runs `_fuzzy_span()` as a fallback **every time the exact-match regex fails**, for **every** synonym in the vocabulary (~90 seeded rows, more after admin/auto-discovery growth) — regardless of whether the optional `kpi_dashboard_fuzzy_match_enabled` setting is on. `_fuzzy_span` tokenizes the *entire remaining prompt text* and, for multi-word phrases, slides a window across all tokens computing a Levenshtein DP (`_levenshtein`, O(len(a)·len(b))) per word pair. Neither `/bs_smart_kpi_dashboard/generate` nor `/bs_smart_kpi_dashboard/suggest` place any length limit on the `prompt` parameter before it reaches this pipeline.
- **Why it matters:** Levenshtein's cost only degrades gracefully because tests assume "single words, a handful of characters" (per the code's own comment) — that assumption is not enforced anywhere. A single very long token (e.g. one megabyte of non-whitespace characters) forces a full O(n·m) DP against every single-word synonym; a prompt with many words forces the windowing loop to scan proportionally more windows for every multi-word synonym. This runs on **every** call to `/generate`, unconditionally, for any authenticated user (`auth='user'`).
- **Impact:** A malicious or careless authenticated internal (or, per M-3 below, portal) user can send oversized prompts repeatedly to consume worker CPU time, degrading the instance for other users. This is a classic "missing input validation → algorithmic complexity" issue, not a data breach.
- **Fix:** Cap `prompt` (and the `suggest` prompt) to a sane length (e.g. 200–500 characters) at the top of `generate()`/`suggest()`, returning a clean validation error above that length, before any parsing work begins.

### M-3. `auth='user'` admits portal users to an internal productivity feature; the resulting behavior is inconsistent

- **Issue:** All six routes in `controllers/main.py` use `auth='user'`, which in Odoo means "any authenticated res.users record," including **portal** users — not just internal employees. `ir.model.access.csv` only grants `base.group_user` (internal users) read/write access to `ai.dashboard.tile`, and only `base.group_system` to `ai.dashboard.allowlist` / `ai.dashboard.synonym` / `ai.dashboard.unmatched_phrase`. `KpiPromptParser`/`_validate_spec` bypass this via `sudo()` on the module's own metadata tables (by design, and correctly scoped), so a portal user *can* reach `generate()`/`run_manual()` and get a chart back — actual data exposure is still bounded by that portal user's own ACLs/record rules on the target business model (e.g. `sale.order`), so this is not a direct IDOR. But `list_tiles()` / `save_tile()` / `delete_tile()` call `self.search()` / `self.create()` / `self.unlink()` directly on `ai.dashboard.tile`, which portal users have **no** `ir.model.access` grant for — those calls will raise an unhandled `AccessError` for a portal user, an inconsistent (and un-triaged) failure mode.
- **Impact:** (a) A feature evidently intended for internal back-office users ("Smart KPI Dashboard," menu gated to internal users only, no portal templates) is silently reachable by any portal contact who knows/guesses the route URLs, contradicting the module's apparent intent; the effective exposure is bounded only by whatever ACLs that portal user's account happens to hold on `sale.order`/`account.move`/`crm.lead`/`stock.move` — which is precisely the kind of case likely to be missed in manual testing since portal users don't see the menu at all. (b) The tile-management endpoints will hard-fail (uncaught `AccessError`) for that same audience instead of a graceful message, which is a functional bug in its own right.
- **Fix:** Restrict the controller routes to internal users explicitly (e.g. check `request.env.user.has_group('base.group_user')` and return a clean 403/JSON error otherwise, or move to a groups-checked route decorator), and/or add an explicit product decision + test for "what happens when a portal user hits these routes."

### M-4. Hard dependency on `crm` and `stock` inflates every installation's footprint

- **Issue:** `__manifest__.py` lists `'depends': ['base', 'web', 'sale', 'account', 'crm', 'stock']`. All four business apps are **mandatory** — not optional/soft dependencies — purely because `data/allowlist_data.xml` seeds one allow-list entry per app.
- **Why it matters:** A customer who only wants a Sales or Invoicing KPI dashboard is forced to install the full CRM and Inventory apps (with their own menus, security groups, demo data, and upgrade surface) just to install this one productivity add-on. This materially increases the blast radius of every future Odoo upgrade for that customer (four large first-party apps' migrations now gate this module's installability, instead of one), and is an unusual ask for a $29 "Productivity" utility.
- **Fix:** Split the four seed allow-list records into four separate, optional data files gated by `'sale'`/`'account'`/`'crm'`/`'stock'` each being *soft* dependencies (Odoo doesn't support truly optional depends without a bridge module, so the common pattern is one thin bridge module per integration, e.g. `bs_smart_kpi_dashboard_crm`, `bs_smart_kpi_dashboard_stock`), or clearly document/justify the decision if bundling all four is intentional for this SKU.

---

## 5. Low Severity Issues

### L-1. Oversized/non-standard icon asset
`static/description/icon.png` is 1024×1024. Odoo App Store convention favors a small square icon (historically ~128×128); an oversized asset isn't broken but is inconsistent with typical listings and increases download size for no benefit.
- **Fix:** Provide a properly-sized icon (or confirm current OdooSA App Store spec accepts high-res icons before submission).

### L-2. `ir.config_parameter` not cleaned up on uninstall
`bs_smart_kpi_dashboard.fuzzy_match_enabled` is created via `res.config.settings`' `config_parameter` mechanism, which is **not** tied to a module XML-ID, so it survives `Uninstall` (a generic Odoo pattern, not unique to this module, but worth noting for a "zero trace on uninstall" bar).
- **Fix:** Optional `uninstall_hook` that deletes the parameter, if a completely clean uninstall is a requirement for this SKU.

### L-3. Unbounded domain clause count
`_validate_spec` validates every domain clause's *shape* but places no cap on the **number** of clauses (unlike `groupby`, capped at `_MAX_GROUPBY = 3`, and `limit`, capped at `_MAX_QUERY_LIMIT = 1000`). A client-built spec (`run_manual`/`tile/save`) could submit a domain with thousands of syntactically valid, allow-listed clauses.
- **Fix:** Add a `_MAX_DOMAIN_CLAUSES` cap alongside the existing groupby/limit caps, consistent with the module's own stated "cost cap" design philosophy.

### L-4. Log verbosity on tile render failures
`get_dashboard_tiles()`'s catch-all `except Exception:` logs `_logger.exception(...)` including the tile id — acceptable for an admin-facing log, but combined with L-3/M-1 could produce log spam if a bad spec is submitted repeatedly. Not user-facing; informational only.

---

## 6. Upgrade Risks

- **First release (19.0.1.0.0):** there is no prior version to upgrade *from*, so no in-place migration risk exists yet for this module itself.
- **XML-ID field references verified correct:** every `ref('...')` in `data/allowlist_data.xml` (e.g. `sale.field_sale_order__date_order`, `account.field_account_move__invoice_date`, `crm.field_crm_lead__expected_revenue`, `stock.field_stock_move__product_qty`, etc.) was cross-checked against the local Odoo 19.0 core source and all exist with the expected type — **install will not fail** on a broken field reference today.
- **Forward-upgrade exposure (Odoo 20+):** because those XML-IDs are hard external references into `sale`/`account`/`crm`/`stock`, any future Odoo core rename/removal of those specific fields would break this module's data loading at the *next* fresh install on that future version (not on an already-installed database, since the records are `noupdate="1"`). This is normal for Odoo add-ons that integrate this deeply, but is worth tracking against future Odoo core changelogs before porting.
- **`noupdate="1"` discipline is correct throughout** (`allowlist_data.xml`, `synonym_data.xml`, `ir_cron_data.xml`, `ai_dashboard_security.xml`): admin edits to the allow-list/vocabulary survive upgrades, and the module's own comments correctly instruct "ship new seeds as new XML IDs" for future versions — this is the right pattern and, if followed, keeps future upgrades low-risk.
- **`models.Constraint` declarative API (`_active_model_uniq`)** verified to be valid, current Odoo 19 API (confirmed against `odoo/orm/table_objects.py`), not a deprecated or invalid construct.
- **No stored computed fields, no field removals/renames, no removed models** — nothing in this release requires a migration script, and none is shipped (correctly, since none is needed for a v1.0.0 release).

---

## 7. Security Risks

Summarized from Section 4/5 (full detail there): **M-1** (uncaught `ValueError` bypassing the intended single validation gate), **M-2** (unbounded prompt length enabling CPU-cost requests), **M-3** (portal users reachable by routes seemingly meant for internal staff only, plus an inconsistent `AccessError` failure mode for the tile-management endpoints). No SQL injection, no `eval`/`exec`, no raw `cr.execute`, no unsafe `sudo()` inheritance onto business data, no CSRF gap (all mutating routes are `type='jsonrpc'`, which is protected by the same-origin/preflight behavior modern browsers enforce on non-simple JSON requests), no XSS surface found (OWL templates use `t-esc` throughout for user-influenced text — chart labels, tile names, error messages — never `t-raw`), no public/unauthenticated routes, no multi-company field on the module's own models but none of the underlying business models' multi-company record rules are bypassed (queries run as `env.user`, never `sudo()`, so multi-company record rules apply exactly as they would to that user anywhere else in Odoo).

---

## 8. Blast Radius Analysis

- **New models added** (`ai.dashboard.allowlist`, `.synonym`, `.tile`, `.unmatched_phrase`): purely additive, no existing model is modified, no existing view is inherited/patched, no existing field is touched. Uninstalling this module removes only these four new tables and their data — **zero risk to any other installed module**.
- **`res.config.settings` inheritance:** one new Boolean field + one new settings block, additive only, no existing settings field touched.
- **Read-only consumption of `sale.order` / `account.move` / `crm.lead` / `stock.move`:** the module never writes to, nor inherits views/models of, these four business models — it only *reads* via `formatted_read_group()` under the calling user's own ACLs. This is the safest possible integration pattern for a reporting add-on and means **no other module or workflow depending on those four models can be broken by installing/uninstalling this one**.
- **Cron job:** one new `ir.cron` (`ir_cron_discover_new_models`), scoped to this module's own model; failure or removal has no effect outside this module.
- **Dependency risk is the main blast-radius concern** (see M-4): by depending hard on `crm`+`stock`, this module's *installability* is coupled to the health of those two apps' own upgrade paths on a given database, even for customers who never wanted CRM/Inventory functionality.
- **Frontend assets:** all additive under `bs_smart_kpi_dashboard/static/src/**`, scoped by the `bs_smart_kpi_dashboard.*` template/component/CSS-class namespace observed throughout — no evidence of overriding or monkey-patching any core `web` component. The manifest's `('include', 'web.chartjs_lib')` asset directive is the correct, supported way to reuse Odoo's bundled Chart.js rather than shipping a duplicate copy.

---

## 9. App Store Publication Blockers

**No hard blockers identified.** Manifest completeness check:

| Field | Status |
|---|---|
| `name`, `summary`, `category` | Present |
| `version` (`19.0.1.0.0`) | Correctly formatted for the target series |
| `license` (`OPL-1`) | Present, appropriate for a paid listing |
| `price` / `currency` | Present |
| `icon` | Present (see L-1: oversized, not invalid) |
| `images` | Present (banner) |
| `author`, `website`, `support` | Present |
| `depends` | Present (see M-4: unnecessarily broad) |
| `data` | Present, correctly ordered (security → data → views → menus) |
| `assets` | Present, correctly scoped to `web.assets_backend` |
| `installable` / `application` | `True` / `True` |
| `static/description/index.html` | Present, complete, well-formed marketing page |
| `README.md` | Present, thorough, accurate to the code |
| Screenshots | 13 numbered screenshots present under `static/description/assets/` |

Recommend fixing **M-1 through M-4** before submission — none are store-listing blockers per se, but M-1/M-2 are exactly the class of defect a store reviewer or a customer's security team would flag, and M-4 affects the honesty of the listing's stated footprint.

---

## 10. Performance Issues

- **M-2** (unbounded prompt → Levenshtein cost) is the primary performance finding.
- **L-3** (unbounded domain clause count) is a secondary, lower-likelihood cost-amplification vector on the `run_manual`/`tile/save` paths.
- **Query cost is otherwise well-bounded by design:** `_MAX_GROUPBY = 3` and `_MAX_QUERY_LIMIT = 1000` are exactly the right kind of guard for an aggregation endpoint exposed to end-user-composed queries, and the code's own comments show this was a deliberate design decision, not an oversight.
- **`get_dashboard_tiles()` re-validates and re-executes every visible tile's query on every dashboard load** (by design, documented as "never cached to disk"). For a user with many pinned/shared tiles this means N live aggregation queries per page load; acceptable for a KPI dashboard's expected tile count, but worth a documented soft limit (e.g. warn or cap the number of shared/pinned tiles) if this becomes a customer-reported slowness complaint at scale.

---

## 11. Recommended Improvements

1. Fix **M-1**: balance-check domain operators in `_validate_spec`, or wrap `formatted_read_group()` and normalize all exceptions to `ValidationError` at the one call site.
2. Fix **M-2**: cap prompt length on `generate`/`suggest`.
3. Fix **M-3**: gate all six routes to internal users only (or make the portal-accessibility decision explicit and add tests + a graceful error path for the tile-management endpoints).
4. Reconsider **M-4**'s dependency footprint, or document/justify it explicitly in the listing description.
5. Add a `_MAX_DOMAIN_CLAUSES` cap (L-3) for defense-in-depth consistency with the existing groupby/limit caps.
6. Resize the App Store icon (L-1) to the conventional dimension.
7. Consider a small `uninstall_hook` to remove the orphaned config parameter (L-2) if a fully clean uninstall matters for this SKU.

---

## 12. Production Readiness Score (/100)

**80/100** — No Critical/High defects; four Medium-severity gaps (one of which — M-1 — directly contradicts the module's own stated security invariant and is trivial to fix) keep this from a higher score. The overall engineering discipline (single validation gate, layered ACL enforcement, defensive `sudo()` usage, resilience-by-design for saved tiles, and an actual regression test suite pinning the security boundary) is well above the baseline expected of most third-party Odoo apps.

## 13. Odoo App Store Readiness Score (/100)

**83/100** — Manifest, description page, README, and screenshots are all complete and professional; no listing-blocking omissions. Deducted for the oversized icon (L-1) and the unusually broad hard-dependency footprint (M-4), which a store reviewer is likely to question.

## 14. Upgrade Safety Score (/100)

**88/100** — First release with no migration debt; `noupdate="1"` discipline and "ship new seeds as new XML IDs" guidance are correctly applied and will keep *future* upgrades low-risk if followed. All referenced core XML-IDs verified to exist in Odoo 19.0. Minor deduction for the forward-looking fragility of hard-coding four business apps' field XML-IDs directly (normal for this integration depth, but a maintenance item for future Odoo series ports).

## 15. Security Score (/100)

**82/100** — Strong layered design (allow-list → real ACL check → record rules, on every load, never bypassed via `sudo()` for business data) with no Critical/High findings. Deducted for M-1 (uncaught-exception path around the validation gate), M-2 (missing input-length hardening enabling a CPU-cost vector), and M-3 (unintended-looking portal reachability with an inconsistent failure mode).

---

## 16. Final Verdict

# **NEEDS MINOR CHANGES**

Rationale: zero Critical or High severity findings; the module demonstrates genuinely disciplined security engineering (single validated gate, no unsafe `sudo()`, real regression tests for the security boundary, correct multi-company/record-rule pass-through). However, four concrete Medium-severity defects were verified by static analysis — most notably M-1, which allows an uncaught exception to bypass the module's own documented "single security/validation gate" invariant — and should be fixed before this module is approved for unrestricted production rollout or Odoo App Store submission.

---

## 17. Fixes Applied

All Medium and Low severity findings below were addressed directly in this codebase (no server start/install performed; verified by static re-read of the changed files and a standalone re-derivation of the new domain-balance algorithm against the report's exploit case and the existing `test_validate_spec.py` cases). `__manifest__.py`'s `version` field was left untouched at `19.0.1.0.0` per instruction.

- **M-1 (uncaught `ValueError` via unbalanced domain operators):** `models/ai_dashboard_allowlist.py::_validate_spec()` now walks the domain in reverse with an operand-arity counter (leaves push one operand, `'!'` consumes/replaces one, `'&'`/`'|'` consume two and replace them with one) and raises `ValidationError` for any domain whose logical operators don't balance against its leaf count — *before* the spec can reach `formatted_read_group()`. The report's exact exploit (`['&', ('team_id', '=', 1)]`) is now rejected at the gate.
- **M-2 (unbounded prompt length / CPU-cost amplification):** `controllers/main.py` adds a `_MAX_PROMPT_LENGTH = 300` cap, enforced in both `generate()` and `suggest()` before any parsing/fuzzy-matching work begins.
- **M-3 (portal users reachable; inconsistent failure mode):** all six routes in `controllers/main.py` (`generate`, `suggest`, `run_manual`, `tiles`, `tile/save`, `tile/delete`) now call a shared `_check_internal_user()` guard first, raising a clean `AccessError` for any non-`base.group_user` caller (portal included) — the same failure mode across every route instead of three working via `sudo()`'d metadata reads and three crashing with an unhandled `AccessError` deep in the ORM.
- **M-4 (hard `crm`/`stock` dependency footprint):** since the fix would require new top-level bridge addon modules outside `bs_smart_kpi_dashboard` (out of scope per instructions), this was resolved via the report's documented alternative: the dependency is now explicitly justified in both `__manifest__.py` (comment above `depends`) and `README.md`'s "Requirements" section, explaining why all four business apps are bundled and how to deactivate unused allow-list entries.
- **L-1 (oversized icon):** `static/description/icon.png` resized from 1024×1024 to the conventional 128×128.
- **L-2 (orphaned config parameter on uninstall):** added `uninstall_hook` (defined in `__init__.py`, wired in `__manifest__.py`) that deletes the `bs_smart_kpi_dashboard.fuzzy_match_enabled` `ir.config_parameter` on module uninstall.
- **L-3 (unbounded domain clause count):** added `_MAX_DOMAIN_CLAUSES = 50` to `ai.dashboard.allowlist`, enforced in `_validate_spec()` alongside the existing groupby/limit caps.
- **L-4 (log verbosity on tile render failures):** no code change — the report itself classifies this as informational-only/non-user-facing, with no corrective action recommended.
