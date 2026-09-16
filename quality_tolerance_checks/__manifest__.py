{
    'name': 'Custom Numeric-Tolerance Quality Checks',
    'version': '17.0.1.0.0',
    'category': 'Manufacturing/Quality',
    'summary': 'Min/max numeric tolerance quality check type with automatic pass/fail.',
    'description': """
Custom Numeric-Tolerance Quality Checks
=========================================
A quality check type supporting min/max numeric tolerance with automatic
pass/fail, common in machining and metal fabrication:

* New "Tolerance Check" quality point type: target value plus a min/max
  tolerance band, defined as a symmetric +/- deviation (absolute or
  percentage) or as a direct min/max range.
* Auto pass/fail: the operator enters a measured value and the check is
  marked pass or fail against the configured tolerance automatically.
* Out-of-tolerance alert: creates a Quality Alert (core Quality's existing
  alert model) pre-filled with the measured vs. target/min/max values
  whenever a measurement fails.
* Measurement History per quality point for statistical-process-control
  style review, plus a native line-graph Control Chart.
* Multi-point tolerance checks are supported the same way core Quality
  supports them: one quality point per measurement point on the part.
""",
    'author': 'ERP23',
    'website': 'https://www.erp-23.com/',
    'license': 'LGPL-3',
    'depends': ['quality'],
    'data': [
        'views/quality_point_views.xml',
        'views/quality_check_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'quality_tolerance_checks/static/src/scss/quality_tolerance_checks.scss',
        ],
    },
    'icon': '/quality_tolerance_checks/static/description/icon.png',
    'images': [
        'static/description/assets/main_screenshot.png',
        'static/description/banner.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
