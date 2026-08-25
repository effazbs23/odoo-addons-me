# -*- coding: utf-8 -*-
import re

from lxml import etree

from odoo.addons.base.models.ir_ui_view import MOVABLE_BRANDING

_OE_VIEW_REF_RE = re.compile(
    r'\s*data-oe-model=\\?"ir\.ui\.view\\?"\s*'
    r'data-oe-id=\\?"(\d+)\\?"\s*'
    r'data-oe-field=\\?"arch\\?"\s*'
    r'data-oe-xpath=\\?"[^"\\]*\\?"',
    re.IGNORECASE,
)

# Editor-only attrs that must never persist in saved page/snippet arches.
_BAKED_EDITOR_ATTRS = tuple(MOVABLE_BRANDING) + (
    'contenteditable',
    'data-editor-message',
    'data-editor-message-default',
    'data-editor-sub-message',
)
_BAKED_EDITOR_CLASSES = ('o_editable', 'o_dirty')


def _remove_dynamic_product_tabs_feature(env):
    """Drop Dynamic Product Tabs snippet + Website → Product Tabs menu (one-shot cleanup)."""
    ICP = env['ir.config_parameter'].sudo()
    flag = 'theme_kingdom.dynamic_product_tabs_removed'

    # Always drop stale ir.asset rows pointing at removed files (safe to re-run).
    Asset = env['ir.asset'].sudo()
    stale_asset_paths = [
        'theme_kingdom/static/src/css/dynamic_product_tabs.css',
        'theme_kingdom/static/src/interactions/kingdom_dynamic_product_tabs.js',
    ]
    Asset.search([('path', 'in', stale_asset_paths)]).unlink()

    # Clear compiled bundles that embed css_error_message for the missing file.
    Attach = env['ir.attachment'].sudo()
    broken = Attach.search([
        ('name', 'ilike', 'assets_'),
        ('url', 'ilike', '/web/assets/'),
    ])
    # Only unlink CSS attachments so next request recompiles cleanly.
    broken.filtered(lambda a: (a.name or '').endswith('.css') or (a.name or '').endswith('.min.css')).unlink()

    if ICP.get_param(flag):
        return

    View = env['ir.ui.view'].sudo().with_context(active_test=False)
    keys = [
        'theme_kingdom.s_dynamic_product_tabs',
        'theme_kingdom.dynamic_product_tabs_panel',
        'theme_kingdom.dynamic_product_tabs_item',
    ]
    View.search([('key', 'in', keys)]).unlink()
    if 'theme.ir.ui.view' in env:
        env['theme.ir.ui.view'].sudo().with_context(active_test=False).search(
            [('key', 'in', keys)]
        ).unlink()

    pages = View.search([
        ('type', '=', 'qweb'),
        '|',
        ('arch_db', 'ilike', 's_dynamic_product_tabs'),
        ('arch_db', 'ilike', 'data-kingdom-live-snippet="s_dynamic_product_tabs"'),
    ])
    for view in pages:
        arch = view.arch_db
        if not arch:
            continue
        try:
            root = etree.fromstring(arch)
        except etree.XMLSyntaxError:
            continue
        removed = False
        for xpath_expr in (
            '//section[contains(concat(" ", normalize-space(@class), " "), " s_dynamic_product_tabs ")]',
            '//*[@data-kingdom-live-snippet="s_dynamic_product_tabs"]',
            '//*[contains(@data-snippet, "s_dynamic_product_tabs")]',
        ):
            for el in root.xpath(xpath_expr):
                parent = el.getparent()
                if parent is not None:
                    parent.remove(el)
                    removed = True
        if removed:
            view.with_context(no_save_prev=True).write({
                'arch_db': etree.tostring(root, encoding='unicode'),
            })

    ICP.set_param(flag, '1')


def _cleanup_stale_oe_view_refs(env):
    """Remove website editor metadata that points to deleted ir.ui.view records."""
    View = env['ir.ui.view'].sudo()
    candidates = View.search([
        ('type', '=', 'qweb'),
        ('arch_db', 'ilike', 'data-oe-id'),
    ])
    for view in candidates:
        arch = view.arch_db
        if not arch:
            continue
        referenced_ids = {int(view_id) for view_id in re.findall(r'data-oe-id=\\?"(\d+)\\?"', arch)}
        if not referenced_ids:
            continue
        existing_ids = set(View.browse(list(referenced_ids)).exists().ids)
        stale_ids = referenced_ids - existing_ids
        if not stale_ids:
            continue
        new_arch = arch
        for stale_id in stale_ids:
            new_arch = _OE_VIEW_REF_RE.sub(
                lambda match, stale=stale_id: '' if int(match.group(1)) == stale else match.group(0),
                new_arch,
            )
        new_arch = re.sub(r'\s+o_dirty(?=["\s>])', '', new_arch)
        if new_arch != arch:
            view.with_context(no_save_prev=True).write({'arch_db': new_arch})


_KINGDOM_SNIPPET_CLASS_FIXES = (
    ('s_featured_products oe_structure oe_website_sale', 's_featured_products oe_website_sale'),
    ('s_bestsale_products oe_structure oe_website_sale', 's_bestsale_products oe_website_sale'),
    ('s_product_carousel oe_structure oe_website_sale', 's_product_carousel oe_website_sale'),
    ('s_category_dual_carousels oe_structure oe_website_sale', 's_category_dual_carousels oe_website_sale'),
    ('s_hero_slider s_hero_slider_wrapper s_carousel_wrapper p-0 oe_structure', 's_hero_slider s_hero_slider_wrapper s_carousel_wrapper p-0'),
    ('s_category_slider oe_structure', 's_category_slider'),
    ('dealoftheday-wrapper oe_structure oe_website_sale', 'dealoftheday-wrapper oe_website_sale'),
    ('s_promo_banners oe_structure', 's_promo_banners'),
    ('s_promo_banner oe_structure', 's_promo_banner'),
    ('s_blog_news oe_structure', 's_blog_news'),
    ('s_brands oe_structure', 's_brands'),
    ('s_manufacturers oe_structure', 's_brands'),
    ('s_manufacturers', 's_brands'),
    ('s_service_highlights oe_structure', 's_service_highlights'),
)


def _migrate_kingdom_snippet_oe_structure(env):
    """Drop oe_structure from saved Kingdom snippet sections in page views."""
    View = env['ir.ui.view'].sudo()
    views = View.search([
        ('type', '=', 'qweb'),
        ('arch_db', 'ilike', 'data-snippet="theme_kingdom.'),
        ('arch_db', 'ilike', 'oe_structure'),
    ])
    for view in views:
        arch = view.arch_db
        if not arch:
            continue
        new_arch = arch
        for old, new in _KINGDOM_SNIPPET_CLASS_FIXES:
            new_arch = new_arch.replace(old, new)
        if new_arch != arch:
            view.with_context(no_save_prev=True).write({'arch_db': new_arch})


_EDITOR_HINT_PATTERNS = (
    re.compile(
        r'<p class="small text-muted mt-2 mb-0 o_not_editable"[^>]*>\s*'
        r'Preview products shown\. Configure tabs in Website .*?Product Tabs\.\s*</p>',
        re.DOTALL,
    ),
    re.compile(
        r'<div class="alert alert-info mb-0 o_not_editable"[^>]*>.*?Product Tabs.*?</div>',
        re.DOTALL,
    ),
    re.compile(
        r'<div class="swiper-slide[^"]*">\s*<article class="featured-product-card">'
        r'.*?Configure featured products in Website settings.*?</article>\s*</div>',
        re.DOTALL,
    ),
    re.compile(
        r'<div class="swiper-slide[^"]*">\s*<article class="featured-product-card">'
        r'.*?Configure best sale products in Website settings.*?</article>\s*</div>',
        re.DOTALL,
    ),
)


def _strip_saved_snippet_editor_hints(env):
    """Remove editor-only configuration hints baked into saved page HTML."""
    View = env['ir.ui.view'].sudo()
    views = View.search([
        ('type', '=', 'qweb'),
        ('arch_db', 'ilike', 'data-snippet="theme_kingdom.'),
    ])
    for view in views:
        arch = view.arch_db
        if not arch:
            continue
        new_arch = arch
        for pattern in _EDITOR_HINT_PATTERNS:
            new_arch = pattern.sub('', new_arch)
        if new_arch != arch:
            view.with_context(no_save_prev=True).write({'arch_db': new_arch})


def _strip_baked_editor_branding(env):
    """Remove baked editor branding from saved QWeb arches.

    When ``data-oe-model`` / ``data-oe-id`` / … are stored inside ``#wrap``
    (e.g. after copying a rendered Kingdom snippet), Odoo's
    ``distribute_branding`` moves branding off ``#wrap`` onto those
    descendants. ``#wrap`` then never becomes ``o_editable``, so the Website
    Builder disables every Blocks category
    ("No block of this category can be dropped on this page").
    """
    View = env['ir.ui.view'].sudo()
    views = View.search([
        ('type', '=', 'qweb'),
        '|', '|',
        ('arch_db', 'ilike', 'data-oe-model'),
        ('arch_db', 'ilike', 'data-oe-xpath'),
        ('arch_db', 'ilike', 'contenteditable'),
    ])
    for view in views:
        arch = view.arch_db
        if not arch:
            continue
        try:
            root = etree.fromstring(arch.encode('utf-8') if isinstance(arch, str) else arch)
        except etree.XMLSyntaxError:
            continue
        changed = False
        for el in root.iter(etree.Element):
            for attr in _BAKED_EDITOR_ATTRS:
                if attr in el.attrib:
                    del el.attrib[attr]
                    changed = True
            classes = (el.get('class') or '').split()
            cleaned = [c for c in classes if c not in _BAKED_EDITOR_CLASSES]
            if cleaned != classes:
                if cleaned:
                    el.set('class', ' '.join(cleaned))
                elif 'class' in el.attrib:
                    del el.attrib['class']
                changed = True
        if changed:
            new_arch = etree.tostring(root, encoding='unicode')
            view.with_context(no_save_prev=True).write({'arch_db': new_arch})


def _fix_stale_multi_website_action_contexts(env):
    """Clear legacy multi-website menu contexts left after reverting to global config."""
    xmlids = (
        'theme_kingdom.action_bestsale_products',
        'theme_kingdom.action_kingdom_brand',
        'theme_kingdom.action_kingdom_manufacturer',
        'theme_kingdom.action_kingdom_deals_of_day',
        'theme_kingdom.action_featured_products',
        'theme_kingdom.kingdom_product_tab_action',
        'theme_kingdom.kingdom_dual_carousel_tab_action',
    )
    for xmlid in xmlids:
        action = env.ref(xmlid, raise_if_not_found=False)
        if not action:
            continue
        if 'current_website_id' in str(action.context or ''):
            action.sudo().write({'context': {}})


def _table_exists(cr, name):
    cr.execute(
        """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = %s
        )
        """,
        (name,),
    )
    return bool(cr.fetchone()[0])


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def _rename_manufacturer_to_brand(cr):
    """Rename kingdom.manufacturer → kingdom.brand (table, fields, xmlids)."""
    if _table_exists(cr, 'kingdom_manufacturer') and not _table_exists(cr, 'kingdom_brand'):
        cr.execute('ALTER TABLE kingdom_manufacturer RENAME TO kingdom_brand')
    if _table_exists(cr, 'kingdom_brand'):
        cr.execute(
            'ALTER INDEX IF EXISTS kingdom_manufacturer_pkey RENAME TO kingdom_brand_pkey'
        )

    if _column_exists(cr, 'product_template', 'kingdom_manufacturer_id') and not _column_exists(
        cr, 'product_template', 'kingdom_brand_id'
    ):
        cr.execute(
            'ALTER TABLE product_template '
            'RENAME COLUMN kingdom_manufacturer_id TO kingdom_brand_id'
        )
        cr.execute(
            'ALTER INDEX IF EXISTS product_template_kingdom_manufacturer_id_index '
            'RENAME TO product_template_kingdom_brand_id_index'
        )

    cr.execute(
        """
        UPDATE ir_model
           SET model = 'kingdom.brand'
         WHERE model = 'kingdom.manufacturer'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_fields
           SET model = 'kingdom.brand'
         WHERE model = 'kingdom.manufacturer'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_fields
           SET relation = 'kingdom.brand'
         WHERE relation = 'kingdom.manufacturer'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_fields
           SET name = 'kingdom_brand_id'
         WHERE model = 'product.template'
           AND name = 'kingdom_manufacturer_id'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_fields
           SET relation_field = 'kingdom_brand_id'
         WHERE relation_field = 'kingdom_manufacturer_id'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_data
           SET name = 'model_kingdom_brand'
         WHERE module = 'theme_kingdom'
           AND name = 'model_kingdom_manufacturer'
           AND model = 'ir.model'
        """
    )
    cr.execute(
        """
        UPDATE ir_attachment
           SET res_model = 'kingdom.brand'
         WHERE res_model = 'kingdom.manufacturer'
        """
    )

    xmlid_renames = [
        ('view_kingdom_manufacturer_list', 'view_kingdom_brand_list'),
        ('view_kingdom_manufacturer_form', 'view_kingdom_brand_form'),
        ('action_kingdom_manufacturer', 'action_kingdom_brand'),
        ('menu_kingdom_manufacturer', 'menu_kingdom_brand'),
        ('s_manufacturers', 's_brands'),
        ('product_template_form_view_manufacturer', 'product_template_form_view_brand'),
        ('product_template_tree_view_manufacturer', 'product_template_tree_view_brand'),
        ('access_kingdom_manufacturer', 'access_kingdom_brand'),
        ('access_kingdom_manufacturer_public', 'access_kingdom_brand_public'),
        ('access_kingdom_manufacturer_portal', 'access_kingdom_brand_portal'),
    ]
    for old, new in xmlid_renames:
        cr.execute(
            """
            SELECT id FROM ir_model_data
             WHERE module = 'theme_kingdom' AND name = %s
            """,
            (new,),
        )
        if cr.fetchone():
            cr.execute(
                """
                DELETE FROM ir_model_data
                 WHERE module = 'theme_kingdom' AND name = %s
                """,
                (old,),
            )
        else:
            cr.execute(
                """
                UPDATE ir_model_data
                   SET name = %s
                 WHERE module = 'theme_kingdom' AND name = %s
                """,
                (new, old),
            )

    # Best-effort QWeb arch rewrite (translated arch_db may be jsonb).
    try:
        with cr.savepoint():
            cr.execute(
                """
                UPDATE ir_ui_view
                   SET arch_db = replace(
                        replace(
                            replace(arch_db::text, 'kingdom.manufacturer', 'kingdom.brand'),
                            's_manufacturers', 's_brands'
                        ),
                        'kingdom_manufacturer_id', 'kingdom_brand_id'
                   )::jsonb
                 WHERE arch_db::text LIKE '%manufacturer%'
                """
            )
    except Exception:
        # Non-jsonb DBs / partial installs — theme reload will refresh arches.
        pass

    if _table_exists(cr, 'theme_ir_ui_view'):
        try:
            with cr.savepoint():
                cr.execute(
                    """
                    UPDATE theme_ir_ui_view
                       SET arch = replace(
                            replace(
                                replace(arch::text, 'kingdom.manufacturer', 'kingdom.brand'),
                                's_manufacturers', 's_brands'
                            ),
                            'kingdom_manufacturer_id', 'kingdom_brand_id'
                       )::jsonb
                     WHERE arch::text LIKE '%manufacturer%'
                    """
                )
        except Exception:
            try:
                with cr.savepoint():
                    cr.execute(
                        """
                        UPDATE theme_ir_ui_view
                           SET arch = replace(
                                replace(
                                    replace(arch, 'kingdom.manufacturer', 'kingdom.brand'),
                                    's_manufacturers', 's_brands'
                                ),
                                'kingdom_manufacturer_id', 'kingdom_brand_id'
                           )
                         WHERE arch LIKE '%manufacturer%'
                        """
                    )
            except Exception:
                pass


def _migrate_promo_banners_to_img(env):
    """Convert twin promo cards from CSS background-image to <img> (Replace in Builder)."""
    ICP = env['ir.config_parameter'].sudo()
    flag = 'theme_kingdom.promo_banners_img_migrated_v2'
    if ICP.get_param(flag):
        return

    bg_url_re = re.compile(
        r"""background-image:\s*url\(\s*['"]?([^'")]+)['"]?\s*\)\s*;?""",
        re.IGNORECASE,
    )
    View = env['ir.ui.view'].sudo()
    views = View.search([
        ('type', '=', 'qweb'),
        ('arch_db', 'ilike', 'promo-banner-blocks__card'),
        ('arch_db', 'ilike', 'background-image'),
    ])
    for view in views:
        arch = view.arch_db
        if not arch:
            continue
        try:
            root = etree.fromstring(arch)
        except etree.XMLSyntaxError:
            continue
        changed = False
        for card in root.xpath(
            '//*[contains(concat(" ", normalize-space(@class), " "), " promo-banner-blocks__card ")]'
        ):
            if card.xpath('.//img[contains(@class, "promo-banner-blocks__img")]'):
                continue
            style = card.get('style') or ''
            match = bg_url_re.search(style)
            if not match:
                continue
            src = match.group(1)
            new_style = bg_url_re.sub('', style).strip().strip(';').strip()
            if new_style:
                card.set('style', new_style)
            elif 'style' in card.attrib:
                del card.attrib['style']
            for child in list(card):
                card.remove(child)
            img = etree.SubElement(card, 'img')
            img.set('src', src)
            img.set('alt', card.get('aria-label') or '')
            img.set('width', '1320')
            img.set('height', '423')
            img.set('loading', 'lazy')
            img.set('class', 'img img-fluid w-100 promo-banner-blocks__img')
            img.set('data-name', 'Promo Banner Image')
            changed = True
        if changed:
            view.with_context(no_save_prev=True).write({
                'arch_db': etree.tostring(root, encoding='unicode'),
            })

    ICP.set_param(flag, '1')


def pre_init_hook(env):
    """Prepare schema and migrate legacy data before module models load."""
    _rename_manufacturer_to_brand(env.cr)
    _ensure_website_menu_kingdom_tab_column(env)
    _migrate_deals_pricelist_items_to_products(env)
    _fix_stale_multi_website_action_contexts(env)


def _ensure_website_menu_kingdom_tab_column(env):
    """Add website_menu.kingdom_product_tab_id when missing (broken/partial installs)."""
    cr = env.cr
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'website_menu'
        )
    """)
    if not cr.fetchone()[0]:
        return
    cr.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'website_menu'
          AND column_name = 'kingdom_product_tab_id'
    """)
    if cr.fetchone():
        return
    cr.execute("""
        ALTER TABLE website_menu
        ADD COLUMN kingdom_product_tab_id int4
    """)
    cr.execute("""
        CREATE INDEX IF NOT EXISTS website_menu_kingdom_product_tab_id_index
        ON website_menu (kingdom_product_tab_id)
    """)


def post_init_hook(env):
    """Ensure public users can read eCommerce categories on the website."""
    category_model = env['ir.model']._get('product.public.category')
    if category_model:
        access_model = env['ir.model.access'].sudo()
        for group_xmlid in ('base.group_public', 'base.group_portal'):
            group = env.ref(group_xmlid, raise_if_not_found=False)
            if not group:
                continue
            exists = access_model.search([
                ('model_id', '=', category_model.id),
                ('group_id', '=', group.id),
                ('perm_read', '=', True),
            ], limit=1)
            if not exists:
                access_model.create({
                    'name': 'product.public.category website read',
                    'model_id': category_model.id,
                    'group_id': group.id,
                    'perm_read': True,
                })

    # Mark Kingdom theme templates inactive by default (gallery opt-in).
    # Do not force-disable applied chrome — that raced with theme post_copy.
    env['theme.utils']._migrate_header_footer_opt_in()
    env['theme.utils']._ensure_header_respects_no_header()

    env['kingdom.product.tab'].ensure_default_tabs()
    _ensure_dual_carousel_tabs(env)
    _migrate_deals_of_day_pricelist_items(env)
    _ensure_homepage_featured_categories(env)
    env['theme.utils']._ensure_kingdom_shop_layout()
    _migrate_kingdom_snippet_oe_structure(env)
    _strip_saved_snippet_editor_hints(env)
    _strip_baked_editor_branding(env)
    _migrate_promo_banners_to_img(env)
    _remove_dynamic_product_tabs_feature(env)
    _cleanup_stale_oe_view_refs(env)

    # Theme may have been applied during this install; re-enable Kingdom chrome last.
    env['theme.utils']._sync_kingdom_chrome_on_themed_websites()


def _ensure_homepage_featured_categories(env):
    """Flag root eCommerce categories for the Featured Categories snippet."""
    Category = env['product.public.category'].sudo()
    if Category.search_count([
        ('parent_id', '=', False),
        ('show_in_homepage', '=', True),
    ]):
        return
    roots = Category.search(
        [('parent_id', '=', False)],
        order='sequence, id',
        limit=8,
    )
    if roots:
        roots.write({'show_in_homepage': True})


def _ensure_default_product_tabs(env):
    """Default tabs + dual-carousel seed (used by legacy callers / migrations)."""
    env['kingdom.product.tab'].ensure_default_tabs()
    _ensure_dual_carousel_tabs(env)
    _migrate_deals_of_day_pricelist_items(env)


def _ensure_dual_carousel_tabs(env):
    """Seed up to two category columns for the dual carousel snippet."""
    Tab = env['kingdom.product.tab'].sudo()
    active_dual = Tab.search_count([
        ('active', '=', True),
        ('show_in_homepage', '=', True),
    ])
    if active_dual >= 2:
        return

    categories = env['product.public.category'].sudo().search(
        [('parent_id', '=', False)],
        order='sequence, id',
        limit=2,
    )
    for index, category in enumerate(categories):
        if Tab.search_count([
            ('active', '=', True),
            ('show_in_homepage', '=', True),
        ]) >= 2:
            break
        existing = Tab.search([
            ('category_id', '=', category.id),
            ('show_in_homepage', '=', True),
        ], limit=1)
        if existing:
            if not existing.active:
                existing.write({'active': True})
            continue
        Tab.create({
            'name': category.name,
            'tab_type': 'category',
            'category_id': category.id,
            'show_in_homepage': True,
            'sequence': 30 + index * 10,
            'feature_label': category.name,
            'feature_url': Tab._get_category_shop_url(category),
            'product_limit': 16,
        })


def _migrate_deals_pricelist_items_to_products(env):
    """Move kingdom_deals_of_day_pricelist_item_rel rows to product_tmpl_ids."""
    cr = env.cr
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'kingdom_deals_of_day_pricelist_item_rel'
        )
    """)
    if not cr.fetchone()[0]:
        return

    cr.execute("""
        CREATE TABLE IF NOT EXISTS kingdom_deals_of_day_product_rel (
            deal_id INTEGER NOT NULL,
            product_tmpl_id INTEGER NOT NULL,
            PRIMARY KEY (deal_id, product_tmpl_id)
        )
    """)
    cr.execute("""
        INSERT INTO kingdom_deals_of_day_product_rel (deal_id, product_tmpl_id)
        SELECT DISTINCT rel.deal_id, tmpl.id
        FROM kingdom_deals_of_day_pricelist_item_rel rel
        JOIN product_pricelist_item item ON item.id = rel.item_id
        LEFT JOIN product_product variant ON variant.id = item.product_id
        JOIN product_template tmpl ON tmpl.id = COALESCE(item.product_tmpl_id, variant.product_tmpl_id)
        WHERE COALESCE(item.product_tmpl_id, variant.product_tmpl_id) IS NOT NULL
        ON CONFLICT DO NOTHING
    """)
    cr.execute("""
        INSERT INTO kingdom_deals_of_day_product_rel (deal_id, product_tmpl_id)
        SELECT DISTINCT rel.deal_id, pt.id
        FROM kingdom_deals_of_day_pricelist_item_rel rel
        JOIN product_pricelist_item item ON item.id = rel.item_id
        JOIN product_category pc ON pc.id = item.categ_id
        JOIN product_template pt ON pt.sale_ok AND pt.is_published
        JOIN product_category ptc ON ptc.id = pt.categ_id
        WHERE item.applied_on = '2_product_category'
          AND (ptc.id = pc.id OR ptc.parent_path LIKE '%%/' || pc.id::text || '/%%')
        ON CONFLICT DO NOTHING
    """)


def _migrate_deals_of_day_pricelist_items(env):
    """Move legacy deal lines / product_source values to the many2many offer lines."""
    cr = env.cr
    cr.execute("""
        UPDATE kingdom_deals_of_day
        SET product_source = 'selected'
        WHERE product_source = 'lines'
    """)
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'kingdom_deals_of_day_line'
        )
    """)
    if not cr.fetchone()[0]:
        return
    cr.execute("""
        SELECT deal_id, pricelist_item_id
        FROM kingdom_deals_of_day_line
        WHERE pricelist_item_id IS NOT NULL
    """)
    for deal_id, item_id in cr.fetchall():
        cr.execute("""
            INSERT INTO kingdom_deals_of_day_pricelist_item_rel (deal_id, item_id)
            SELECT %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM kingdom_deals_of_day_pricelist_item_rel
                WHERE deal_id = %s AND item_id = %s
            )
        """, (deal_id, item_id, deal_id, item_id))
