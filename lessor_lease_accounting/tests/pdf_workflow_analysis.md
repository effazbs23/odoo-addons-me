# VOLT PDF Workflow Analysis - Invoices and Journal Entries

## PDF Workflow: From Down-Payment to Monthly Interest Income

### Phase A: Down Payment (A1-A3)
| Step | Document Type | Description | Debit | Credit |
|------|--------------|-------------|-------|--------|
| A1 | **Invoice** | Down Payment Invoice | AR (113101) | HP Receivable (113104) |
| A1.2 | Tax Line | VAT on Down Payment | Undue VAT (215102) | (included in invoice) |
| A2 | **Journal Entry** | VAT Reclass on DP | Undue VAT (215102) | Output VAT (215101) |
| A3 | Payment | Down Payment Payment | Cash (110001) | AR (113101) |

### Phase C: Initial Recognition (C1-C3)
| Step | Document Type | Description | Debit | Credit |
|------|--------------|-------------|-------|--------|
| C1 | **Journal Entry** | Initial Recognition - Receivable | HP Receivable (113104) | Lease Sales (410101) |
| C2 | **Journal Entry** | Initial Recognition - Deferred Interest | Deferred Interest (216103) | (part of C1 entry) |
| C3 | **Journal Entry** | Initial Recognition - Undue VAT | Undue VAT (215102) | (part of C1 entry) |

### Phase D: Asset Recognition (D1)
| Step | Document Type | Description | Debit | Credit |
|------|--------------|-------------|-------|--------|
| D1 | **Journal Entry** | Asset Derecognition | COGS (500103) | Asset for Sale (114104) |

### Phase E: Monthly Accounting (E1-E4)
| Step | Document Type | Description | Debit | Credit |
|------|--------------|-------------|-------|--------|
| E1 | **Invoice** | Monthly Installment Invoice | AR (113101) | HP Receivable (113104) |
| E1.2 | Tax Line | VAT on Installment | Undue VAT (215102) | (included in invoice) |
| E2 | **Journal Entry** | VAT Reclass Monthly | Undue VAT (215102) | Output VAT (215101) |
| E3 | **Journal Entry** | Interest Recognition | Deferred Interest (216103) | Interest Income (410102) |
| E4 | Payment | Monthly Payment | Cash (110001) | AR (113101) |

---

## Summary: From Down-Payment to Monthly Interest Income

### Total Documents Created:

#### Invoices (2):
1. **A1**: Down Payment Invoice
2. **E1**: Monthly Installment Invoice

#### Journal Entries (4):
1. **A2**: VAT Reclass on Down Payment
2. **C**: Initial Recognition (1 combined entry with 3 lines)
3. **D**: Asset Recognition
4. **E2**: VAT Reclass Monthly
5. **E3**: Interest Recognition

### Grand Total: 7 Documents
- **2 Invoices**
- **5 Journal Entries**

---

## Current Code Implementation Analysis

### Current Workflow (from `lessor_lease_contract.py`):

| PDF Step | Current Method | Status |
|----------|---------------|--------|
| A1: Down Payment Invoice | `action_create_down_payment_invoice()` | ✅ Implemented |
| A2: VAT Reclass DP | ❌ **NOT IMPLEMENTED** | ❌ Missing |
| A3: Down Payment Payment | Odoo's Register Payment | ✅ Native Odoo |
| C: Initial Recognition | `action_post_initial_recognition()` | ✅ Implemented |
| D: Asset Recognition | Included in C (Gross Method) | ✅ Implemented |
| E1: Monthly Invoice | `_create_installment_invoice()` | ✅ Implemented |
| E2: VAT Reclass Monthly | `_create_vat_recognition_entry()` | ✅ Implemented |
| E3: Interest Recognition | `_create_interest_recognition_entry()` | ✅ Implemented |
| E4: Monthly Payment | Odoo's Register Payment | ✅ Native Odoo |

---

## Gap Analysis

### Missing in Current Code:
1. **A2: VAT Reclass on Down Payment** - The down payment invoice VAT reclassification is missing

### Differences:
1. **PDF shows A2 as separate step** after down payment invoice
2. **Current code only creates VAT reclass for monthly invoices** (E2), not for down payment (A2)

---

## Test Cases Required

### TC001: Down Payment Invoice Creation
- Verify down payment invoice is created
- Verify it debits AR (113101)
- Verify it credits HP Receivable (113104)
- Verify VAT line credits Undue VAT (215102)

### TC002: VAT Reclass on Down Payment
- **MISSING FEATURE**: Need to implement A2 VAT reclass
- Verify JE: Dr Undue VAT (215102) / Cr Output VAT (215101)

### TC003: Initial Recognition (Gross Method)
- Verify HP Receivable is debited (gross amount)
- Verify Lease Sales is credited (principal only)
- Verify Deferred Interest is credited (total interest)
- Verify Undue VAT is credited (total VAT)

### TC004: Asset Recognition
- Verify COGS is debited (cost_price)
- Verify Asset for Sale is credited (cost_price)

### TC005: Monthly Installment Invoice
- Verify invoice debits AR (113101)
- Verify invoice credits HP Receivable (113104) - NOT Lease Sales
- Verify VAT line credits Undue VAT (215102)

### TC006: Monthly VAT Reclass
- Verify JE: Dr Undue VAT (215102) / Cr Output VAT (215101)

### TC007: Monthly Interest Recognition
- Verify JE: Dr Deferred Interest (216103) / Cr Interest Income (410102)

### TC008: Verify Lease Sales NOT Credited Monthly
- **CRITICAL**: Verify monthly invoices do NOT credit Lease Sales
- Verify only initial recognition credits Lease Sales

