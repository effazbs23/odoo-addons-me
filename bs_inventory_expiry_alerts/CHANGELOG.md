# Changelog

## 19.0.1.0.0

- Initial release.
- **Deviation from spec**: the spec's suggested dependency `stock_expiry` does not exist
  under that name in Odoo 19 Community; the equivalent core module is `product_expiry`
  (same `expiration_date`/`use_date`/`removal_date`/`alert_date` fields on `stock.lot`).
  Depends on `product_expiry` instead.
