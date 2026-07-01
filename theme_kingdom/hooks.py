# -*- coding: utf-8 -*-


def pre_init_hook(env):
    """Copy legacy offer-line picks to product picks before the old field is removed."""
    _migrate_deals_pricelist_items_to_products(env)


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

    for website in env['website'].search([]):
        env['theme.utils'].with_context(website_id=website.id)._activate_kingdom_footer()

    _ensure_default_product_tabs(env)
    _ensure_homepage_featured_categories(env)


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
    """Default New Arrivals / Best Sellers tabs and header menus on install or upgrade."""
    Tab = env['kingdom.product.tab'].sudo()
    defaults = [
        {
            'name': 'New Arrivals',
            'tab_type': 'new_arrival',
            'show_in_header_menu': True,
            'show_in_product_carousel': True,
            'sequence': 10,
        },
        {
            'name': 'Best Sellers',
            'tab_type': 'best_seller',
            'show_in_header_menu': True,
            'show_in_product_carousel': True,
            'sequence': 20,
        },
    ]
    for vals in defaults:
        existing = Tab.search([('tab_type', '=', vals['tab_type'])], limit=1)
        if not existing:
            Tab.create(vals)
        elif not existing.show_in_header_menu:
            existing.write({'show_in_header_menu': True})
    Tab.search([])._sync_header_menus()

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
