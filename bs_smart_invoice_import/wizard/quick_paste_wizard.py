import base64
import binascii
import difflib
import mimetypes
import threading
from datetime import date

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Command

from . import embedding_matcher, llm_client, parser, pdf_utils

try:
    from rapidfuzz import fuzz as _rapidfuzz_fuzz
except ImportError:
    _rapidfuzz_fuzz = None


def _fuzzy_ratio(text_a, text_b):
    """Lexical string similarity in [0, 100], tuned for a short/typo'd
    customer-style query against a longer catalog name.

    Uses ``rapidfuzz``'s ``WRatio`` (a composite of full-string, partial and
    token-based ratios -- handles a query that's just a fragment of the
    product name, e.g. "dawer" vs "Office Drawer Unit", far better than a
    plain ratio) if installed; falls back to ``difflib.SequenceMatcher``
    otherwise -- see ``_match_product_semantic`` for how this is blended
    with the embedding score, and why it's down-weighted there.
    """
    if _rapidfuzz_fuzz is not None:
        return _rapidfuzz_fuzz.WRatio(text_a, text_b)
    return difflib.SequenceMatcher(None, text_a.lower(), text_b.lower()).ratio() * 100


# In-process cache of product-name embeddings, keyed by database name.
# Invalidated automatically when the catalog's (count, max write_date)
# signature changes -- see QuickPasteWizard._get_catalog_embedding_cache.
_CATALOG_EMBEDDING_CACHE = {}
_CATALOG_EMBEDDING_CACHE_LOCK = threading.Lock()

# Product-name candidates are scored on a 0.7/0.3 blend of embedding cosine
# similarity and rapidfuzz WRatio/100. WRatio is deliberately the *minor*
# weight: it's what makes a short fragment like "dawer" (vs "Office Drawer
# Unit") or "ngk sapark plags" (vs "NGK Spark Plug") score high enough to
# match, but being partial/substring-based it CANNOT tell apart names that
# differ only in a trailing word (WRatio ties "Acme Steel Bracket Type A"
# and "...Type B" against either query) -- the embedding score is what
# still separates those correctly, so it needs the larger weight or that
# distinction gets diluted away. A lone top match at/above
# SEMANTIC_MATCH_THRESHOLD, with no rival within SEMANTIC_AMBIGUOUS_GAP of
# it, is treated as a confident 'matched' result. Below
# SEMANTIC_CANDIDATE_THRESHOLD a candidate isn't considered at all. Tuned
# empirically on this blended 0-1 scale against 11 probe cases -- see
# CONTEXT.md for the full case-by-case scores this was tuned against.
#
# SEMANTIC_MATCH_THRESHOLD raised 0.55 -> 0.65 in session 8: a real invoice
# upload against a real (but topically unrelated -- staffing/labor line
# items, no matching products in the catalog) 56-product catalog produced a
# confident false 'matched' at 0.622 ("Staffing - John Smith" ->
# "Memo - Hygene"). 0.65 rejects that false positive as intended, but as a
# deliberate, user-accepted tradeoff it also demotes two previously-tuned
# weak-but-correct fuzzy matches from 'matched' to 'ambiguous':
# "ngk sapark plags" (0.593) and "dawer" (0.596) -- both now require manual
# product selection instead of auto-matching. See CONTEXT.md Session 7/8
# for the full quantitative conflict (the false-positive score sits between
# those two legitimate ones on the same 0-1 scale, so no single global
# threshold can separate this specific case without affecting them).
SEMANTIC_MATCH_THRESHOLD = 0.65
SEMANTIC_CANDIDATE_THRESHOLD = 0.50
SEMANTIC_AMBIGUOUS_GAP = 0.03
SEMANTIC_CATALOG_LIMIT = 5000
SEMANTIC_COSINE_WEIGHT = 0.7
SEMANTIC_FUZZY_WEIGHT = 0.3

# Bounds memory/CPU use when rasterizing an uploaded PDF and the size of the
# base64 payload sent to the LLM -- an invoice is a small document; this is
# generous headroom, not a tight fit.
MAX_INVOICE_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

# Per-user, per-day cap on invoice-extraction calls. Every internal user
# with access to this wizard can trigger a call against the company's
# shared (and billed) LLM API key -- this keeps one user from exhausting
# the quota/budget on their own. Configurable via
# 'bs_smart_invoice_import.llm_daily_limit'; 0 or unset disables the cap.
DEFAULT_LLM_DAILY_LIMIT = 50


class QuickPasteWizard(models.TransientModel):
    _name = 'quick.paste.wizard'
    _description = "Smart Invoice Import Wizard"

    mode = fields.Selection(
        [('paste', "Paste Text"), ('invoice', "Upload Invoice")],
        default='paste', required=True,
    )
    raw_text = fields.Text(string="Pasted Text")
    invoice_file = fields.Binary(string="Invoice File")
    invoice_filename = fields.Char(string="Invoice Filename")
    order_id = fields.Reference(
        selection=[('sale.order', "Sales Order"), ('purchase.order', "Purchase Order")],
        string="Order",
    )
    state = fields.Selection(
        [('input', "Input"), ('setup_required', "LLM Setup Required"), ('preview', "Preview")],
        default='input',
    )
    preview_line_ids = fields.One2many(
        'quick.paste.wizard.line', 'wizard_id', string="Preview Lines",
    )
    preview_summary = fields.Char(compute='_compute_preview_summary')

    @api.depends('preview_line_ids.status')
    def _compute_preview_summary(self):
        for wizard in self:
            lines = wizard.preview_line_ids
            if not lines:
                wizard.preview_summary = ''
                continue
            matched = len(lines.filtered(lambda l: l.status == 'matched'))
            ambiguous = len(lines.filtered(lambda l: l.status == 'ambiguous'))
            unmatched = len(lines.filtered(lambda l: l.status == 'unmatched'))
            wizard.preview_summary = _(
                "%(total)s row(s) found — %(matched)s matched, %(ambiguous)s ambiguous, %(unmatched)s unmatched",
                total=len(lines), matched=matched, ambiguous=ambiguous, unmatched=unmatched,
            )

    @api.onchange('mode')
    def _onchange_mode(self):
        for wizard in self:
            if wizard.mode == 'invoice' and wizard.state == 'input' and not wizard._get_llm_config():
                wizard.state = 'setup_required'
            elif wizard.mode == 'paste' and wizard.state == 'setup_required':
                wizard.state = 'input'

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        if active_model in ('sale.order', 'purchase.order') and active_id:
            res['order_id'] = f'{active_model},{active_id}'
        if res.get('mode') == 'invoice' and not self._get_llm_config():
            res['state'] = 'setup_required'
        return res

    # ------------------------------------------------------------------
    # LLM configuration
    # ------------------------------------------------------------------
    @api.model
    def _get_llm_config(self):
        """Return {'base_url', 'api_key', 'model', 'prompt'} from Settings,
        or None if the LLM API hasn't been configured yet.

        Only 'base_url' and 'api_key' are required -- 'model' is
        intentionally optional and never defaulted to a hardcoded value:
        not every OpenAI-compatible provider needs (or wants) one hardcoded
        on our side (e.g. some gateways pick it from the API key), and
        forcing a model to be set here would block providers that don't
        need one.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        base_url = get_param('bs_smart_invoice_import.llm_base_url')
        api_key = get_param('bs_smart_invoice_import.llm_api_key')
        if not (base_url and api_key):
            return None
        return {
            'base_url': base_url,
            'api_key': api_key,
            'model': get_param('bs_smart_invoice_import.llm_model') or '',
            'prompt': get_param('bs_smart_invoice_import.llm_prompt') or llm_client.DEFAULT_PROMPT,
        }

    def action_open_llm_settings(self):
        return self.env['ir.actions.act_window']._for_xml_id('base_setup.action_general_configuration')

    @api.model
    def _check_llm_rate_limit(self):
        """Raise UserError if the current user has hit their daily invoice-
        extraction cap. Every internal user with access to this wizard can
        trigger a call billed against the company's shared LLM API key --
        this keeps one user's usage from exhausting the quota/budget for
        everyone else.
        """
        ICP = self.env['ir.config_parameter'].sudo()
        limit = int(ICP.get_param('bs_smart_invoice_import.llm_daily_limit', DEFAULT_LLM_DAILY_LIMIT) or 0)
        if limit <= 0:
            return
        param_key = f'bs_smart_invoice_import.llm_usage.{self.env.uid}.{date.today().isoformat()}'
        count = int(ICP.get_param(param_key, 0) or 0)
        if count >= limit:
            raise UserError(_(
                "You've reached the daily limit of %(limit)s invoice extractions "
                "for today. Ask an administrator to raise "
                "'bs_smart_invoice_import.llm_daily_limit' if you need more.",
                limit=limit,
            ))
        ICP.set_param(param_key, count + 1)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------
    @api.model
    def _parse_text(self, raw_text):
        """Regex/heuristic parser. Returns a list of
        {'raw_line', 'sku', 'name', 'qty'} dicts. See ``wizard/parser.py``.
        """
        return parser.parse_raw_text(raw_text)

    @api.model
    def _parse_order_rows(self, raw_text):
        """Entry point used by :meth:`action_parse`.

        Extension seam: if the regex parser returns too few rows relative to
        the number of non-empty input lines, an AI-based parser could be
        plugged in here as a fallback, e.g.::

            ai_rows = self._ai_parse_text(raw_text)
            if ai_rows:
                rows = ai_rows

        ``_ai_parse_text`` is not implemented yet. As long as it returns the
        same {'raw_line', 'sku', 'name', 'qty'} row shape, no other part of
        the wizard (matching, preview grid, action_confirm) needs to change.
        """
        rows = self._parse_text(raw_text)
        non_empty_lines = [line for line in (raw_text or '').splitlines() if line.strip()]
        if non_empty_lines and len(rows) < len(non_empty_lines) * 0.5:
            # TODO: AI parser fallback seam — not implemented yet.
            pass
        return rows

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------
    @api.model
    def _match_product(self, sku, name):
        """Match a parsed (sku, name) pair to a product.product recordset.

        Returns (product.product recordset, status) where status is one of
        'matched' / 'ambiguous' / 'unmatched'. For 'matched' the recordset
        has exactly one record; for 'ambiguous' it has the candidates; for
        'unmatched' it is empty.
        """
        Product = self.env['product.product']
        sku = (sku or '').strip()
        name = (name or '').strip()

        if sku:
            products = Product.search([
                '|', ('default_code', '=ilike', sku), ('barcode', '=ilike', sku),
            ], limit=11)
            if len(products) == 1:
                return products, 'matched'
            if len(products) > 1:
                return products, 'ambiguous'

        if name:
            semantic = self._match_product_semantic(name)
            if semantic is not None:
                return semantic
            # Fallback when the embedding model isn't available: plain
            # string-fuzzy matching. NOTE: broad scan, capped for
            # performance. Fine for typical catalogs; flagged as a
            # limitation for very large ones.
            candidates = Product.search([('name', '!=', False)], limit=2000)
            names_map = {}
            for product in candidates:
                names_map.setdefault(product.name, product)
            close = difflib.get_close_matches(name, list(names_map.keys()), n=3, cutoff=0.6)
            if len(close) == 1:
                return names_map[close[0]], 'matched'
            if len(close) > 1:
                matched = Product.browse([names_map[c].id for c in close])
                return matched, 'ambiguous'

        return Product.browse(), 'unmatched'

    @api.model
    def _get_catalog_embedding_cache(self):
        """Return (ids, names, embeddings) for all named products visible
        to the current user, cached in-process and invalidated
        automatically when the catalog changes (by (count, max write_date)
        signature). Returns None if the embedding model isn't available.

        Cached per (database, active companies): ``product.product``
        access can be scoped by company/record rules, so a cache keyed on
        the database alone would let one company's/user's product-name
        exposure leak into another's results whenever their (count,
        write_date) signatures happened to coincide. Company scoping is a
        cheap, always-safe partition to key on even where no such rule is
        configured.
        """
        if not embedding_matcher.is_available():
            return None
        Product = self.env['product.product']
        products = Product.search([('name', '!=', False)], limit=SEMANTIC_CATALOG_LIMIT)
        if not products:
            return None
        cache_key = (self.env.cr.dbname, tuple(sorted(self.env.companies.ids)))
        signature = (len(products), max(products.mapped('write_date')))
        with _CATALOG_EMBEDDING_CACHE_LOCK:
            cached = _CATALOG_EMBEDDING_CACHE.get(cache_key)
            if cached and cached['signature'] == signature:
                return cached['ids'], cached['names'], cached['embeddings']
        names = products.mapped('name')
        embeddings = embedding_matcher.embed(names)
        if embeddings is None:
            return None
        entry = {'signature': signature, 'ids': products.ids, 'names': names, 'embeddings': embeddings}
        with _CATALOG_EMBEDDING_CACHE_LOCK:
            _CATALOG_EMBEDDING_CACHE[cache_key] = entry
        return entry['ids'], entry['names'], entry['embeddings']

    @api.model
    def _match_product_semantic(self, name):
        """Semantic + fuzzy hybrid product-name match (see the module-level
        SEMANTIC_* constants for the scoring formula).

        Returns (recordset, status) or None if the embedding model isn't
        available -- callers should fall back to plain string-fuzzy
        matching in that case.
        """
        cache = self._get_catalog_embedding_cache()
        if cache is None:
            return None
        ids, names, embeddings = cache
        query = embedding_matcher.embed([name])
        if not query:
            return None
        query_vec = query[0]
        scored = sorted(
            (
                (
                    SEMANTIC_COSINE_WEIGHT * embedding_matcher.cosine_similarity(query_vec, vec)
                    + SEMANTIC_FUZZY_WEIGHT * (_fuzzy_ratio(name, pname) / 100.0),
                    pid,
                )
                for pid, pname, vec in zip(ids, names, embeddings)
            ),
            reverse=True,
        )
        candidates = [(score, pid) for score, pid in scored[:5] if score >= SEMANTIC_CANDIDATE_THRESHOLD]
        Product = self.env['product.product']
        if not candidates:
            return Product.browse(), 'unmatched'

        top_score, top_id = candidates[0]
        close_rivals = [pid for score, pid in candidates if top_score - score <= SEMANTIC_AMBIGUOUS_GAP]
        if top_score >= SEMANTIC_MATCH_THRESHOLD and len(close_rivals) == 1:
            return Product.browse(top_id), 'matched'
        ambiguous_ids = close_rivals if len(close_rivals) > 1 else [pid for _, pid in candidates]
        return Product.browse(ambiguous_ids), 'ambiguous'

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_parse(self):
        self.ensure_one()
        rows = self._parse_order_rows(self.raw_text)
        self._build_preview_lines(rows)
        return self._reopen_action()

    def action_extract_invoice(self):
        self.ensure_one()
        if not self.invoice_file:
            raise UserError(_("Please upload an invoice file first."))

        config = self._get_llm_config()
        if not config:
            self.state = 'setup_required'
            return self._reopen_action()

        self._check_llm_rate_limit()

        try:
            raw_bytes = base64.b64decode(self.invoice_file, validate=True)
        except (binascii.Error, ValueError):
            raise UserError(_("The uploaded file is not valid -- please re-upload it."))
        if len(raw_bytes) > MAX_INVOICE_FILE_SIZE:
            raise UserError(_(
                "The uploaded invoice is too large (max %(max_mb)s MB). "
                "Try a smaller scan or a lower-resolution export.",
                max_mb=MAX_INVOICE_FILE_SIZE // (1024 * 1024),
            ))
        filename = (self.invoice_filename or '').lower()
        is_pdf = filename.endswith('.pdf') or raw_bytes[:5] == b'%PDF-'

        images_b64 = []
        if is_pdf:
            try:
                pages = pdf_utils.pdf_to_images(raw_bytes)
            except RuntimeError as exc:
                raise UserError(str(exc))
            if not pages:
                raise UserError(_("Could not read any pages from the uploaded PDF."))
            for page_png in pages:
                images_b64.append(('image/png', base64.b64encode(page_png).decode()))
        else:
            mime_type = mimetypes.guess_type(filename)[0] or 'image/png'
            # Binary fields already store base64 -- no need to decode/re-encode.
            image_data = self.invoice_file
            image_b64 = image_data.decode() if isinstance(image_data, bytes) else image_data
            images_b64.append((mime_type, image_b64))

        try:
            rows = llm_client.extract_invoice_lines(
                config['base_url'], config['api_key'], config['model'], config['prompt'], images_b64,
            )
        except llm_client.LLMError as exc:
            raise UserError(_("Invoice extraction failed: %(error)s", error=str(exc)))

        if not rows:
            raise UserError(_(
                "The LLM did not return any line items for this invoice. "
                "Try a clearer scan, or check the configured prompt in Settings."
            ))

        self._build_preview_lines(rows)
        return self._reopen_action()

    def _build_preview_lines(self, rows):
        self.ensure_one()
        line_vals = []
        for row in rows:
            product, status = self._match_product(row['sku'], row['name'])
            best = product[:1]
            line_vals.append(Command.create({
                'raw_line': row['raw_line'],
                'sku': row['sku'],
                'name': row['name'],
                'qty': row['qty'] or 1,
                'product_id': best.id if status == 'matched' else False,
                'uom_id': best.uom_id.id if status == 'matched' else False,
                'status': status,
            }))
        self.write({
            'preview_line_ids': [Command.clear()] + line_vals,
            'state': 'preview',
        })

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        if not order:
            raise UserError(_("No source order found to add lines to."))

        matched_lines = self.preview_line_ids.filtered(lambda l: l.product_id)
        skipped_lines = self.preview_line_ids - matched_lines

        if order._name == 'sale.order':
            order.order_line = [
                Command.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty or 1.0,
                    'product_uom_id': line._order_uom_id().id,
                })
                for line in matched_lines
            ]
        else:  # purchase.order
            order.order_line = [
                Command.create({
                    'product_id': line.product_id.id,
                    'product_qty': line.qty or 1.0,
                    'product_uom_id': line._order_uom_id().id,
                    # TODO: naive default. Real vendor pricing should come
                    # from the vendor's last PO price or a pricelist, not
                    # the generic cost price. Not settled — revisit.
                    'price_unit': line.product_id.standard_price,
                })
                for line in matched_lines
            ]

        if skipped_lines:
            body = Markup('<p>%s</p><ul>') % _(
                "Quick Paste: %(count)s row(s) were skipped because no matching product was found:",
                count=len(skipped_lines),
            )
            for line in skipped_lines:
                body += Markup('<li>%s</li>') % (line.raw_line or '')
            body += Markup('</ul>')
            order.message_post(body=body)

        return {'type': 'ir.actions.act_window_close'}

    def _reopen_action(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }


class QuickPasteWizardLine(models.TransientModel):
    _name = 'quick.paste.wizard.line'
    _description = "Smart Invoice Import Wizard Line"

    wizard_id = fields.Many2one('quick.paste.wizard', required=True, ondelete='cascade')
    raw_line = fields.Char(string="Raw Text")
    sku = fields.Char(string="Parsed SKU")
    name = fields.Char(string="Parsed Description")
    qty = fields.Float(string="Quantity", default=1.0)
    product_id = fields.Many2one('product.product', string="Product")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    status = fields.Selection(
        [('matched', "Matched"), ('ambiguous', "Ambiguous"), ('unmatched', "Unmatched")],
        string="Status", default='unmatched',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.uom_id = line.product_id.uom_id
                line.status = 'matched'
            else:
                line.status = 'unmatched'

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        for line in self:
            if (
                line.product_id and line.uom_id
                and not line.uom_id._has_common_reference(line.product_id.uom_id)
            ):
                line.uom_id = line.product_id.uom_id
                return {'warning': {
                    'title': _("Incompatible unit of measure"),
                    'message': _(
                        "%(uom)s isn't in the same category as %(product)s's unit "
                        "-- reverted to %(default_uom)s.",
                        uom=line.uom_id.name, product=line.product_id.display_name,
                        default_uom=line.product_id.uom_id.name,
                    ),
                }}

    def _order_uom_id(self):
        """UoM to use when creating the order line: the row's own UoM if it
        shares the product's UoM category (a raw write -- e.g. via RPC --
        bypasses the onchange above, so this is checked again here rather
        than trusted at face value), else the product's default.
        """
        self.ensure_one()
        if self.uom_id and self.uom_id._has_common_reference(self.product_id.uom_id):
            return self.uom_id
        return self.product_id.uom_id

    def action_create_product_from_line(self):
        """One-click product creation for an unmatched row: quick-creates a
        product.product from the parsed name (mirrors Odoo's own Many2one
        quick-create -- name only, saved fast, details fleshed out later
        from the product form) and links it back onto this line.
        """
        self.ensure_one()
        label = (self.name or self.raw_line or '').strip()
        if not label:
            raise UserError(_("Nothing to create a product from on this row."))
        Product = self.env['product.product']
        product_id, _name = Product.name_create(label)
        product = Product.browse(product_id)
        if self.sku:
            product.default_code = self.sku
        self.write({
            'product_id': product.id,
            'uom_id': product.uom_id.id,
            'status': 'matched',
        })
