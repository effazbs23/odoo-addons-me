# -*- coding: utf-8 -*-

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


def _ensure_default_product_tabs(env):
    """Default New Arrivals / Best Sellers tabs and header menus on install or upgrade."""
    Tab = env['kingdom.product.tab'].sudo()
    defaults = [
        {
            'name': 'New Arrivals',
            'tab_type': 'new_arrival',
            'show_in_header_menu': True,
            'sequence': 10,
        },
        {
            'name': 'Best Sellers',
            'tab_type': 'best_seller',
            'show_in_header_menu': True,
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
