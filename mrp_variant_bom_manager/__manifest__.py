{
    'name': 'Variant-Aware BOM Manager',
    'version': '19.0.1.0.0',
    'category': 'Manufacturing/Manufacturing',
    'summary': 'Visual matrix for configuring which BOM lines apply to '
               'which product variants.',
    'description': """
Variant-Aware BOM Manager
==========================
Configure variant-specific Bills of Materials visually instead of manually
keying attribute-value filters on each BOM line:

* Matrix view: BOM lines as rows, product variants as columns, toggle
  applicability per cell.
* Bulk apply/remove across several lines and variants at once.
* Live preview of the exact resolved BOM for any single variant.
* Copy an existing variant's BOM configuration as the starting point for
  a new, similar variant.
* Warns about variants left with zero applicable BOM lines.

Works directly on the existing `bom_product_template_attribute_value_ids`
field of `mrp.bom.line` — no parallel data model.
""",
    'author': 'ERP23',
    'website': 'https://www.erp-23.com/',
    'license': 'LGPL-3',
    'depends': ['mrp', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/mrp_bom_variant_matrix_wizard_views.xml',
        'views/mrp_bom_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mrp_variant_bom_manager/static/src/js/mrp_bom_variant_matrix.js',
            'mrp_variant_bom_manager/static/src/xml/mrp_bom_variant_matrix.xml',
            'mrp_variant_bom_manager/static/src/scss/mrp_bom_variant_matrix.scss',
        ],
    },
    'icon': '/mrp_variant_bom_manager/static/description/icon.png',
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
