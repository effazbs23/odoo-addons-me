# E-Invoice Retention & Audit Trail (`bs_einvoice_archive`)

An ASP-agnostic records-and-audit layer on top of `account.move`. On invoice
posting it captures an immutable snapshot (PDF/XML references + a SHA-256
checksum), tracks how long that snapshot must legally be retained, logs
access to it, and lets a user produce an audit-ready ZIP export on demand.

## What it is NOT

- Not a PINT AE XML generator.
- Not an ASP / Peppol transmission module.
- Not a place where data ever gets auto-deleted. Disposal is always a
  manual, logged, explicitly-confirmed action (`Administrator` group only).

## Prerequisites

- **Odoo version:** 19.0
- **Dependencies:** `account`, `google_account` (Google Drive backup only works with the latter)
- **Python packages:** `cryptography`, `requests` (declared in `external_dependencies`)

## Core concepts

### Archive lifecycle

Every invoice goes through a deterministic lifecycle:

1. **Active** — the snapshot is current and within its legal retention window.
2. **Eligible for Disposal** — the retention period has expired. A daily cron
   promotes `active` records to this state automatically; it is a flag only
   and never deletes anything.
3. **Disposed** — an E-Invoice Archive Administrator manually confirms
   disposal. The row is never deleted, only marked disposed.

Disposal is a one-way, logged action that can only be performed by the
`Administrator` group.

### Invoice types

The module recognizes seven invoice types, each with its own configurable
retention period:

| Type | Code | Default Retention |
|---|---|---|
| Standard | `standard` | 5 years |
| Simplified | `simplified` | 5 years |
| Self-Billed | `self_billed` | 5 years |
| Credit Note | `credit_note` | 5 years |
| Debit Note | `debit_note` | 5 years |
| Capital Asset | `capital_asset` | 7 years |
| Real Estate | `real_estate` | 15 years |

Credit notes link to the original invoice's archive record
(`original_archive_id`) when one exists. This is best-effort, not enforced
at save time: a standalone credit note (no `reversed_entry_id`) or one
reversing an invoice posted before this module was installed has no
original archive to link to, and posting must still succeed. The daily
health-check cron (`_cron_flag_broken_corrections`) flags any credit/debit
note archive whose `original_archive_id` doesn't resolve, instead of
blocking the post.

### Immutability

Archive records are append-only. The `write()` method rejects any field
change except `state`, `asp_status`, `asp_status_payload`, and the Google
Drive backup bookkeeping fields (`drive_xml_file_id`, `drive_pdf_file_id`,
`drive_backup_status`). Attempting to modify anything else raises a
`UserError`. Archive records can never be deleted — `unlink()` always raises.

### Automatic snapshot on posting

Controlled per company by the **Archive Posted Invoices** toggle under
Settings > E-Invoice Archive (on by default). When enabled and
`action_post()` is called on an `account.move`, the module automatically
creates an archive record if one doesn't already exist. It:

1. Determines the invoice type (credit/debit notes from `move_type`, everything
   else defaults to `standard` — see the `ponytail` heuristic comment in
   `account_move.py`).
2. Looks up the applicable retention policy for the company (or the global
   fallback).
3. Locates existing XML/PDF attachments on the invoice; generates a PDF via
   the `account.account_invoices` report if none exists.
4. Computes a SHA-256 checksum over the binary content of both files.
5. Creates the archive record with a sequential name (`ARCH/YYYY/XXXXX`).

The attachments are owned by `account.move` (not by the archive record), so
they survive module uninstall.

**Once an invoice has an archive record, its `account.move` can never be
deleted again** (`bs.einvoice.archive.move_id` is `ondelete='restrict'`),
even after resetting it to draft — deleting a move that core Odoo would
otherwise allow now raises instead. This is deliberate: an archive record
can never be reassigned to a different invoice, so an FK that allowed the
move to disappear would leave the audit trail dangling.

## Data model

- `bs.einvoice.archive` — append-only snapshot per invoice. `write()` raises
  on any field except `state`/`asp_status`/`asp_status_payload` and Drive
  bookkeeping fields. `unlink()` always raises.
- `bs.einvoice.retention.policy` — company-scoped, editable retention years
  per invoice type. Business logic always reads from here, never from a
  hardcoded number.
- `bs.einvoice.audit.log` — append-only access/action trail. `write()` and
  `unlink()` always raise.
- `bs.einvoice.archive.export.wizard` — filters archives and produces a ZIP
  (attachments + `manifest.json` + `audit_log.csv`). Supports English and
  Arabic manifest labels. Can also be launched from a multi-select on the
  archive list view.
- `bs.einvoice.drive.config` — one-per-company Google Drive connection record.
- `bs.einvoice.drive.upload.queue` — asynchronous upload queue processed by
  a cron; handles retry with exponential backoff.

## Security

### Groups

| Group | Access |
|---|---|
| **Auditor** | Read-only on archives, audit logs, retention policies, and the export wizard. No configuration or disposal rights. |
| **Administrator** | Full CRUD on archives and retention policies, manages the Google Drive connection, and is the only role that can approve disposal or retry failed Drive backups. |

### Multi-company isolation

Global `ir.rule` records enforce that every model in the module
(`bs.einvoice.archive`, `bs.einvoice.retention.policy`,
`bs.einvoice.drive.config`) is scoped to the user's allowed companies. A
user in Company A can never see Company B's archive records.

### Access control (ACL)

Auditors have read-only access to archives, logs, and policies. Admins have
full CRUD on archives and policies. Both roles have full access to the
export wizard. Drive config and upload queue are restricted to Admins.

## Daily cron

`ir.cron` "E-Invoice Archive: Daily Health Check" runs once a day and:

- Flags posted invoices with no archive (creates a `mail.activity` and
  emails a summary to Administrators).
- Flags archives with a broken/missing attachment (same notification path).
- Promotes expired records to `eligible_for_disposal` (a flag only, never a
  delete).
- Flags credit/debit notes whose `original_archive_id` doesn't resolve
  (the linked archive is missing or has been disposed).
- Reports any failed Google Drive backups or Drive connection errors in
  the same summary email.

## Export for audit

The Export for Audit wizard lets users filter archives by date range, partner,
or TRN, then download a ZIP containing:

- Per-archive subdirectories with the XML and PDF files.
- `manifest.json` — machine-readable index with invoice number, TRN,
  archive date, retention expiry, checksum, and ASP status. Labels are
  language-aware (English or Arabic).
- `audit_log.csv` — every logged action across all exported archives.

Each export action is recorded in the audit trail.

## Optional: Google Drive offsite backup

If a company connects a Google Drive account (Settings for the OAuth client
id/secret, then E-Invoice Archive > Configuration > Google Drive Backup to
connect that company), every new archive's XML/PDF is additionally queued
for upload to Drive, processed by its own 5-minute cron
(`bs.einvoice.drive.upload.queue`) — never synchronously with invoice
posting. This is purely additive: the local `ir.attachment`-on-`account.move`
storage is unchanged, and with no account connected, archives are simply
created with `drive_backup_status='not_applicable'`.

- Requests only the `drive.file` OAuth scope (files this app creates, not
  the whole Drive).
- The refresh token is encrypted at rest (Fernet, key derived from Odoo's
  own `database.secret`) and only visible to the `Administrator` group.
- Uploaded files are organized under a root `E-Invoice Archive` folder with
  year-based subfolders (e.g. `E-Invoice Archive/2026/INV00001.pdf`).
- A failed upload retries up to 5 times with exponential backoff (2, 4, 8,
  16, 32 minutes); after that it's marked `failed`, logged to the audit
  trail, and raises an activity for the `Administrator` group. A "Retry
  Backup" button on the archive form re-queues it.
- Secrets are never logged or persisted in plain text — all error messages
  and stored payloads are redacted before persistence.
- Uninstalling revokes the stored OAuth grant with Google as a courtesy
  (so it stops showing up under the client's connected apps) but never
  touches a single file already uploaded to their Drive — same principle
  as the local attachment strategy above.

## Uninstall protection (read this before uninstalling)

The module ships an `uninstall_hook` that **blocks uninstall** if any
`bs.einvoice.archive` record is still `state != 'disposed'` and its
`retention_expiry_date` is in the future. If it blocks you:

- The invoice PDFs/XMLs themselves are safe either way — they're stored as
  `ir.attachment` records owned by `account.move`, a model this module
  doesn't own, specifically so they survive this module being removed.
- What you lose on uninstall is the archive index, the audit trail, and the
  export tooling built on top of those files.
- There is no override flag. Either wait out the retention period or dispose
  of the outstanding records (as an Administrator) first.

If the uninstall proceeds (all records are disposed or expired), the module
also revokes any active Google Drive OAuth tokens with Google as a courtesy
step. This never blocks uninstall — failures are silently ignored.
