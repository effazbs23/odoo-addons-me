# Inventory Valuation Details

**Version:** 19.0.2.0.0
**Category:** Inventory/Inventory
**License:** LGPL-3
**Author:** ERP23
**Website:** https://www.erp-23.com

## Overview

The **Inventory Valuation Details** module restores per-move inventory valuation transparency in Odoo 19. It provides detailed valuation information directly on stock operations, which Odoo 19 removed (SVL - Stock Valuation Layers).

This module brings full visibility into how inventory is valued across all stock movements, including the expected accounting entries for each operation.

## Features

### 💰 Valuation Smart Buttons
- **Stock Transfers (Picking):** Smart button showing total stock value for each operation
  - Receipt orders (Stock > Purchase Receipt)
  - Delivery orders (Stock > Sales Delivery)
  - Customer/Vendor returns
  - Drop-ship orders
  - Internal transfers

### 📄 Journal Entry Integration
- Direct link to corresponding accounting entries
- Shows expected DR/CR accounts even when no per-move entry is created
- Uses Odoo 19's actual accounts:
  - Stock Valuation
  - Stock Variation
  - Expense/COGS
  - Work in Progress (WIP)

### 🏭 Manufacturing Operations
- **Manufacturing Orders:** Smart button for production valuation
- Component consumption valuation
- Finished goods production valuation
- Scrap orders valuation smart button

### 📊 Detailed Breakdown Per Product
- Quantity moved
- Unit cost (based on configured cost method)
- Total value
- Cost method identification

### 🎯 Cost Method Support
Correctly distinguishes between:
- **Perpetual vs Periodic** valuation
- **FIFO** (First In First Out)
- **AVCO** (Average Cost)
- **Standard** Cost

### ✅ Intelligent Filtering
- Automatically skips Services (no valuation)
- Excludes untracked Consumables
- Covers only inventory items

### 📋 Supported Operations
- Purchase receipts
- Sales deliveries
- Customer/Vendor returns
- Drop-ship operations
- Scrap orders
- Unbuild orders
- Landed cost adjustments
- MRP components & finished goods

### 📈 Global Reporting
**Inventory → Reporting → Stock Valuations**
- Filter by:
  - Product
  - Product category
  - Cost method
  - Valuation method
  - Date
- Group by any dimension for analysis

## Installation

### Requirements
- Odoo 19.0
- `stock_account` module (standard)
- `mrp_account` module (standard)

### Setup
1. Clone or download the module to your Odoo `addons` directory
2. Update the module list in your Odoo instance
3. Install the module from the Apps menu
4. Grant appropriate permissions to users (see Security section)

## Module Structure

```
bs_inventory_valuation_details/
├── __manifest__.py           # Module manifest and metadata
├── __init__.py               # Python package initialization
├── models/
│   ├── stock_move.py         # Valuation calculations for stock moves
│   ├── stock_picking.py      # Smart buttons and aggregation for transfers
│   ├── stock_scrap.py        # Scrap order valuation
│   ├── mrp_production.py     # Manufacturing order valuation
│   └── res_company.py        # Company-level configurations
├── views/
│   ├── stock_move_valuation_views.xml      # Move-level valuation view
│   ├── stock_picking_views.xml             # Transfer smart buttons
│   ├── stock_scrap_views.xml               # Scrap smart buttons
│   └── mrp_production_views.xml            # Manufacturing smart buttons
├── security/
│   └── ir.model.access.csv   # User access controls
└── static/
    └── (Resources for UI/styling)
```

## Usage

### Viewing Valuation on Stock Transfers

1. Navigate to **Inventory > Operations > Transfers**
2. Open any receipt, delivery, or return order
3. Click the **Valuation** smart button to see:
   - Per-product breakdown
   - Unit costs
   - Total values
   - Cost method used

### Viewing Related Journal Entry

1. On a Stock Transfer detail, click the **Journal Entry** smart button
2. View the complete accounting entry
3. See expected accounts even if entry wasn't automatically created

### Checking Manufacturing Valuations

1. Go to **Manufacturing > Manufacturing Orders**
2. Open a production order
3. Click **Valuation** to see component costs and finished goods value

### Analyzing Scrap Operations

1. Navigate to **Inventory > Operations > Scraps**
2. Open a scrap order
3. Click **Scrap Valuation** to see disposal value

### Global Valuation Report

1. Go to **Inventory > Reporting > Stock Valuations**
2. Use filters to analyze:
   - Valuations by product
   - Valuations by cost method
   - Time-based valuations
3. Group data as needed for analysis

## Configuration

### User Permissions
Access is controlled via `ir.model.access.csv`. Users need:
- **Read** access to view valuations
- **Write/Create** access (admin) to modify configurations

### Cost Method Selection
- Cost method is defined at the **Product** level
- Affects valuation calculations across all operations
- Supports: Standard, FIFO, AVCO

## Security & Access Control

The module includes model-level security in `security/ir.model.access.csv`:
- Define groups that can access valuation details
- Control visibility of cost information
- Standard Odoo security model applies

## Technical Details

### Valuation Calculation
- Based on product's cost method
- Uses actual quantities and costs from stock moves
- Accounts for:
  - Unit cost at time of movement
  - Quantity transferred
  - Applicable surcharges (landed costs)

### Journal Entry Prediction
- Calculates expected accounts based on:
  - Operation type (receipt, delivery, scrap, etc.)
  - Product type (inventory item, service, etc.)
  - Valuation method (perpetual/periodic)
  - Cost method (FIFO, AVCO, Standard)

### Performance
- Lazy loading of valuation details
- Aggregated smart buttons (no inline calculation)
- Optimized for large inventories

## Troubleshooting

### Valuation Shows as 0
- Verify product has a cost method assigned
- Check if product is marked as "Inventory Tracked"
- Ensure unit cost is properly configured

### Journal Entry Button Missing
- Verify `stock_account` module is installed
- Check user permissions for accounting models
- Confirm operation type is supported

### Cost Method Mismatch
- Verify product's cost method hasn't changed after operations
- Check historical cost records for retroactive changes

## API & Customization

### Key Models
- **stock.move** - Individual movement valuations
- **stock.picking** - Transfer-level aggregation
- **stock.scrap** - Scrap operation valuations
- **mrp.production** - Manufacturing valuations

### Extending the Module
The module is designed to be extended:
- Override calculation methods for custom logic
- Add new smart buttons via view inheritance
- Extend models for additional fields

## Support & Contributions

For issues, feature requests, or contributions:
- **Author:** ERP23
- **Website:** https://www.erp-23.com

## License

This module is licensed under the **LGPL-3** license.

---

**Last Updated:** 2026-05-13

