# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import math


class TestLessorLeaseContract(TransactionCase):
    """Test cases for Lessor Lease Contract model calculations"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test partner (lessee)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Lessee Company',
            'customer_rank': 1,
        })

        # Ensure company has a country (required for tax in 19.0)
        company = cls.env.company
        if not company.account_fiscal_country_id and not company.country_id:
            country = cls.env.ref('base.us', raise_if_not_found=False) or cls.env['res.country'].search([], limit=1)
            company.write({'country_id': country.id})
        fiscal_country_id = company.account_fiscal_country_id.id or company.country_id.id

        tax_group = cls.env['account.tax.group'].search([], limit=1)
        if not tax_group:
            tax_group = cls.env['account.tax.group'].create({'name': 'VAT'})
        
        # Create VAT tax 7%
        cls.vat_tax_7 = cls.env['account.tax'].create({
            'name': 'VAT 7%',
            'type_tax_use': 'sale',
            'amount': 7.0,
            'amount_type': 'percent',
            'country_id': fiscal_country_id,
            'tax_group_id': tax_group.id,
        })
        
        # Create VAT tax 15% (for additional tests)
        cls.vat_tax_15 = cls.env['account.tax'].create({
            'name': 'VAT 15%',
            'type_tax_use': 'sale',
            'amount': 15.0,
            'amount_type': 'percent',
            'country_id': fiscal_country_id,
            'tax_group_id': tax_group.id,
        })

    def test_01_basic_field_calculations(self):
        """Test basic field calculations with user's data"""
        
        # Create contract with user's manual inputs
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Equipment',
            'cost_price': 89430.00,  # Manual
            'total_gross_amount': 160000.00,  # Manual
            'down_payment_percent': 10.00,  # Manual
            'annual_interest_rate': 15.00,  # Manual
            'term_months': 48,  # Manual
            'start_date': '2025-01-01',
            'vat_rate_id': self.vat_tax_7.id,
            'accounting_method': 'gross',
        })
        
        # Test VAT Rate extraction
        self.assertAlmostEqual(
            contract.vat_rate_id.amount, 
            7.00, 
            places=2,
            msg="VAT Rate should be 7.00%"
        )
        
        # Test Total Net Amount = Total Gross Amount / 1.07
        expected_total_net = 160000.00 / 1.07
        self.assertAlmostEqual(
            contract.total_net_amount,
            expected_total_net,
            places=2,
            msg=f"Total Net Amount should be {expected_total_net:.2f}"
        )
        self.assertAlmostEqual(
            contract.total_net_amount,
            149532.71,
            places=2,
            msg="Total Net Amount should be 149,532.71"
        )
        
        # Test Total VAT = Total Gross Amount - Total Net Amount
        expected_vat = 160000.00 - contract.total_net_amount
        self.assertAlmostEqual(
            contract.total_vat,
            expected_vat,
            places=2,
            msg=f"Total VAT should be {expected_vat:.2f}"
        )
        self.assertAlmostEqual(
            contract.total_vat,
            10467.29,
            places=2,
            msg="Total VAT should be 10,467.29"
        )
        
        # Test Down Payment = Down Payment Rate × Total Gross Amount
        expected_down_payment = 160000.00 * 0.10
        self.assertAlmostEqual(
            contract.down_payment_amount,
            expected_down_payment,
            places=2,
            msg=f"Down Payment should be {expected_down_payment:.2f}"
        )
        self.assertAlmostEqual(
            contract.down_payment_amount,
            16000.00,
            places=2,
            msg="Down Payment should be 16,000.00"
        )

        
        # Test Margin = 1 - (Cost Price / Total Net Amount)
        expected_margin_percent = (1 - (89430.00 / contract.total_net_amount)) * 100
        self.assertAlmostEqual(
            contract.margin_percent,
            expected_margin_percent,
            places=2,
            msg=f"Margin % should be {expected_margin_percent:.2f}%"
        )
        self.assertAlmostEqual(
            contract.margin_percent,
            40.19,
            places=2,
            msg="Margin % should be 40.19%"
        )
        
        # Test Margin Amount
        expected_margin_amount = contract.total_net_amount - 89430.00
        self.assertAlmostEqual(
            contract.margin,
            expected_margin_amount,
            places=2,
            msg=f"Margin amount should be {expected_margin_amount:.2f}"
        )

    def test_02_gross_asset_value_calculation(self):
        """
        Test Gross Asset Value calculation (Thai market method)
        
        Thai market standard: GAV = Total Gross Amount - Down Payment (GROSS - GROSS)
        This includes VAT in the financed amount.
        """
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        # Thai market method: GAV = Total Gross - Down Payment
        expected_gav = contract.total_gross_amount - contract.down_payment_amount
        self.assertAlmostEqual(
            contract.gross_asset_value_financed,
            expected_gav,
            places=2,
            msg=f"GAV should be {expected_gav:.2f} (GROSS - GROSS)"
        )
        
        # Should be 144,000.00 (Thai market standard)
        self.assertAlmostEqual(
            contract.gross_asset_value_financed,
            144000.00,
            places=2,
            msg="GAV should be 144,000.00 (using GROSS values)"
        )

    def test_03_monthly_interest_rate_calculation(self):
        """Test Monthly Interest Rate = (1 + Annual)^(1/12) - 1"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        # Monthly = (1 + Annual)^(1/12) - 1
        expected_monthly_rate = (1 + 0.15) ** (1/12) - 1
        self.assertAlmostEqual(
            contract.monthly_interest_rate,
            expected_monthly_rate,
            places=6,
            msg=f"Monthly interest rate should be {expected_monthly_rate:.6f}"
        )
        
        # Should be approximately 0.011715 (1.171%)
        self.assertAlmostEqual(
            contract.monthly_interest_rate,
            0.011715,
            places=5,
            msg="Monthly interest rate should be 0.011715 (1.171%)"
        )
        
        # Test percentage conversion
        monthly_rate_percent = contract.monthly_interest_rate * 100
        self.assertAlmostEqual(
            monthly_rate_percent,
            1.171,
            places=3,
            msg="Monthly interest rate should be 1.171%"
        )

    def test_04_monthly_installment_pmt_calculation(self):
        """Test Monthly Installment = ROUNDUP(-PMT(monthly_rate, months, GAV), 0)"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        # Manual PMT calculation
        pv = contract.gross_asset_value_financed
        r = contract.monthly_interest_rate
        n = contract.term_months
        
        pmt = pv * (r * (1 + r)**n) / ((1 + r)**n - 1)
        expected_installment = math.ceil(pmt)  # ROUNDUP to whole number
        
        self.assertAlmostEqual(
            contract.monthly_installment,
            expected_installment,
            places=2,
            msg=f"Monthly installment should be {expected_installment:.2f}"
        )
        
        # With Thai GAV (144,000), installment should be 3,940.00
        self.assertAlmostEqual(
            contract.monthly_installment,
            3940.00,
            places=2,
            msg="Monthly installment should be 3,940.00"
        )

    def test_05_outstanding_balance_calculation(self):
        """Test Outstanding Balance = Monthly Installments × Months"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        expected_ob = contract.monthly_installment * contract.term_months
        self.assertAlmostEqual(
            contract.outstanding_balance,
            expected_ob,
            places=2,
            msg=f"Outstanding Balance should be {expected_ob:.2f}"
        )
        
        # With installment of 3,940, OB should be 189,120
        self.assertAlmostEqual(
            contract.outstanding_balance,
            189120.00,
            places=2,
            msg="Outstanding Balance should be 189,120.00"
        )

    def test_06_schedule_generation(self):
        """Test schedule generation creates correct number of lines"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        # Confirm contract to generate schedule
        contract.action_confirm()
        
        # Check schedule lines created
        self.assertEqual(
            len(contract.schedule_line_ids),
            48,
            msg="Should create 48 schedule lines"
        )
        
        # Check first line
        first_line = contract.schedule_line_ids[0]
        self.assertEqual(first_line.month, 1, msg="First line should be month 1")
        # Opening NPV is now PV of payment stream, not GAV
        # Just check it's positive
        self.assertGreater(
            first_line.opening_npv,
            0.0,
            msg="First line opening NPV should be positive"
        )
        
        # Check last line closes at zero
        last_line = contract.schedule_line_ids[-1]
        self.assertEqual(last_line.month, 48, msg="Last line should be month 48")
        self.assertAlmostEqual(
            last_line.closing_npv,
            0.00,
            places=2,
            msg="Last line closing NPV should be 0.00"
        )

    def test_07_schedule_totals(self):
        """Test schedule totals match expected values"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        contract.action_confirm()
        
        # Calculate totals
        total_principal = sum(line.principal for line in contract.schedule_line_ids)
        total_interest = sum(line.interest for line in contract.schedule_line_ids)
        total_net_payments = sum(line.net_payment for line in contract.schedule_line_ids)
        total_gross_payments = sum(line.gross_payment for line in contract.schedule_line_ids)
        total_vat = sum(line.vat for line in contract.schedule_line_ids)
        
        # Total principal should equal opening NPV (PV of payment stream)
        first_line = contract.schedule_line_ids.sorted('month')[0]
        self.assertAlmostEqual(
            total_principal,
            first_line.opening_npv,
            places=1,
            msg="Total principal should equal Opening NPV"
        )
        
        # Total GROSS payments should equal outstanding balance
        self.assertAlmostEqual(
            total_gross_payments,
            contract.outstanding_balance,
            places=2,
            msg="Total gross payments should equal Outstanding Balance"
        )
        
        # Total gross = Total net + Total VAT
        self.assertAlmostEqual(
            total_gross_payments,
            total_net_payments + total_vat,
            places=2,
            msg="Total gross should equal Total net + Total VAT"
        )
        
        # Total interest + Total principal should equal Total net payments (within rounding tolerance)
        self.assertAlmostEqual(
            total_interest + total_principal,
            total_net_payments,
            delta=1.0,  # Reduced delta for better precision
            msg="Interest + Principal should equal Total Net Payments"
        )

    def test_08_schedule_vat_calculations(self):
        """Test VAT calculations in schedule lines"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'accounting_method': 'gross',
            'vat_rate_id': self.vat_tax_7.id,
        })
        
        contract.action_confirm()
        
        # Check VAT calculation for each line
        for line in contract.schedule_line_ids:
            expected_vat = line.net_payment * 0.07
            self.assertAlmostEqual(
                line.vat,
                expected_vat,
                places=1,
                msg=f"Month {line.month}: VAT should be {expected_vat:.2f}"
            )
            
            expected_gross = line.net_payment + line.vat
            self.assertAlmostEqual(
                line.gross_payment,
                expected_gross,
                places=1,
                msg=f"Month {line.month}: Gross payment should be {expected_gross:.2f}"
            )

    def test_09_validation_constraints(self):
        """Test field validation constraints"""
        
        # Test negative cost price
        with self.assertRaises(ValidationError, msg="Should reject negative cost price"):
            self.env['lessor.lease.contract'].create({
                'lessee_id': self.partner.id,
                'asset_name': 'Test Asset',
                'cost_price': -1000.00,
                'total_gross_amount': 160000.00,
                'down_payment_percent': 10.00,
                'annual_interest_rate': 15.00,
                'term_months': 48,
                'start_date': '2025-01-01',
                'vat_rate_id': self.vat_tax_7.id,
                'accounting_method': 'gross',
            })
        
        # Test invalid down payment percentage
        with self.assertRaises(ValidationError, msg="Should reject down payment > 100%"):
            self.env['lessor.lease.contract'].create({
                'lessee_id': self.partner.id,
                'asset_name': 'Test Asset',
                'cost_price': 89430.00,
                'total_gross_amount': 160000.00,
                'down_payment_percent': 150.00,
                'annual_interest_rate': 15.00,
                'term_months': 48,
                'start_date': '2025-01-01',
                'vat_rate_id': self.vat_tax_7.id,
                'accounting_method': 'gross',
            })
        
        # Test negative annual interest rate
        with self.assertRaises(ValidationError, msg="Should reject negative interest rate"):
            self.env['lessor.lease.contract'].create({
                'lessee_id': self.partner.id,
                'asset_name': 'Test Asset',
                'cost_price': 89430.00,
                'total_gross_amount': 160000.00,
                'down_payment_percent': 10.00,
                'annual_interest_rate': -5.00,
                'term_months': 48,
                'start_date': '2025-01-01',
                'vat_rate_id': self.vat_tax_7.id,
                'accounting_method': 'gross',
            })
        
        # Test zero/negative term months
        with self.assertRaises(ValidationError, msg="Should reject zero term months"):
            self.env['lessor.lease.contract'].create({
                'lessee_id': self.partner.id,
                'asset_name': 'Test Asset',
                'cost_price': 89430.00,
                'total_gross_amount': 160000.00,
                'down_payment_percent': 10.00,
                'annual_interest_rate': 15.00,
                'term_months': 0,
                'start_date': '2025-01-01',
                'vat_rate_id': self.vat_tax_7.id,
                'accounting_method': 'gross',
            })

    def test_10_different_vat_rate(self):
        """Test calculations with different VAT rate (15%)"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 100000.00,
            'total_gross_amount': 188880.00,
            'down_payment_percent': 20.00,
            'annual_interest_rate': 12.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'vat_rate_id': self.vat_tax_15.id,
            'accounting_method': 'gross',
        })
        
        # Test VAT rate
        self.assertAlmostEqual(
            contract.vat_rate_id.amount,
            15.00,
            places=2,
            msg="VAT rate should be 15%"
        )
        
        # Test net amount
        expected_net = 188880.00 / 1.15
        self.assertAlmostEqual(
            contract.total_net_amount,
            expected_net,
            places=2,
            msg=f"Total net should be {expected_net:.2f}"
        )
        
        # Test VAT amount
        expected_vat = 188880.00 - expected_net
        self.assertAlmostEqual(
            contract.total_vat,
            expected_vat,
            places=2,
            msg=f"Total VAT should be {expected_vat:.2f}"
        )

    def test_11_contract_workflow(self):
        """Test contract state workflow"""
        
        contract = self.env['lessor.lease.contract'].create({
            'lessee_id': self.partner.id,
            'asset_name': 'Test Asset',
            'cost_price': 89430.00,
            'total_gross_amount': 160000.00,
            'down_payment_percent': 10.00,
            'annual_interest_rate': 15.00,
            'term_months': 48,
            'start_date': '2025-01-01',
            'vat_rate_id': self.vat_tax_7.id,
            'accounting_method': 'gross',
        })
        
        # Initial state should be draft
        self.assertEqual(contract.state, 'draft', msg="Initial state should be draft")
        
        # Confirm contract
        contract.action_confirm()
        self.assertEqual(contract.state, 'confirmed', msg="State should be confirmed")
        self.assertTrue(
            len(contract.schedule_line_ids) > 0,
            msg="Schedule should be generated after confirmation"
        )
        
        # Activate contract
        contract.action_activate()
        self.assertEqual(contract.state, 'active', msg="State should be active")
        
        # Close contract
        contract.action_close()
        self.assertEqual(contract.state, 'closed', msg="State should be closed")
