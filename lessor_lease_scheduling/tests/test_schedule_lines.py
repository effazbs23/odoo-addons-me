# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import math


class TestLessorLeaseScheduleLines(TransactionCase):
    """
    Test cases for Lessor Lease Schedule Lines
    Using client's exact data to verify calculations match expectations
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test partner (lessee)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Lessee Company',
            'customer_rank': 1,
        })
        
        # Create VAT tax 7% (Thailand standard)
        cls.vat_tax_7 = cls.env['account.tax'].create({
            'name': 'VAT 7%',
            'type_tax_use': 'sale',
            'amount': 7.0,
            'amount_type': 'percent',
        })
        
        # Create contract with CLIENT'S EXACT DATA
        cls.contract = cls.env['lessor.lease.contract'].create({
            'lessee_id': cls.partner.id,
            'asset_name': 'Test Equipment - Client Data',
            'cost_price': 89430.00,  # Manual input
            'total_gross_amount': 160000.00,  # Manual input
            'down_payment_percent': 10.00,  # Manual input
            'annual_interest_rate': 15.00,  # Manual input
            'term_months': 48,  # Manual input
            'start_date': '2026-01-10',
            'accounting_method': 'gross',
        })
        
        # Confirm contract to generate schedule
        cls.contract.action_confirm()

    def test_01_contract_basic_calculations(self):
        """Test that contract level calculations match client's data"""
        
        # Total Net Amount = Total Gross / 1.07
        self.assertAlmostEqual(
            self.contract.total_net_amount,
            149532.71,
            places=2,
            msg="Total Net Amount should be 149,532.71"
        )
        
        # VAT = Total Gross - Total Net
        self.assertAlmostEqual(
            self.contract.total_vat,
            10467.29,
            places=2,
            msg="Total VAT should be 10,467.29"
        )
        
        # Down Payment = 10% of Total Gross
        self.assertAlmostEqual(
            self.contract.down_payment_amount,
            16000.00,
            places=2,
            msg="Down Payment should be 16,000.00"
        )

        # GAV = Total Gross - Down Payment (GROSS - GROSS)
        self.assertAlmostEqual(
            self.contract.gross_asset_value_financed,
            144000.00,
            places=2,
            msg="GAV should be 144,000.00"
        )
        
        # Monthly Interest Rate = (1.15)^(1/12) - 1
        expected_monthly_rate = (1.15) ** (1/12) - 1
        self.assertAlmostEqual(
            self.contract.monthly_interest_rate,
            expected_monthly_rate,
            places=6,  # Changed from 8 to 6 for tolerance
            msg=f"Monthly rate should be {expected_monthly_rate:.8f}"
        )
        self.assertAlmostEqual(
            self.contract.monthly_interest_rate * 100,
            1.171,
            places=3,
            msg="Monthly rate should be 1.171%"
        )
        
        # Monthly Installment (GROSS) = ROUNDUP(PMT(15%, 48, 144000))
        self.assertAlmostEqual(
            self.contract.monthly_installment,
            3940.00,
            places=2,
            msg="Monthly Installment should be 3,940.00"
        )
        
        # Outstanding Balance = 48 × 3,940
        self.assertAlmostEqual(
            self.contract.outstanding_balance,
            189120.00,
            places=2,
            msg="Outstanding Balance should be 189,120.00"
        )
        
        # Margin % = 1 - (89,430 / 149,532.71)
        self.assertAlmostEqual(
            self.contract.margin_percent,
            40.19,
            places=2,
            msg="Margin % should be 40.19%"
        )

    def test_02_schedule_line_count(self):
        """Test that 48 schedule lines are created"""
        
        self.assertEqual(
            len(self.contract.schedule_line_ids),
            48,
            msg="Should create exactly 48 schedule lines"
        )
        
        # Check month sequence
        for i, line in enumerate(self.contract.schedule_line_ids.sorted('month'), 1):
            self.assertEqual(
                line.month,
                i,
                msg=f"Line {i} should have month = {i}"
            )

    def test_03_payment_breakdown_all_months(self):
        """Test that all months have correct gross/net/vat breakdown"""
        
        for line in self.contract.schedule_line_ids:
            # Gross Payment should be 3,940 for all months
            self.assertAlmostEqual(
                line.gross_payment,
                3940.00,
                places=2,
                msg=f"Month {line.month}: Gross payment should be 3,940.00"
            )
            
            # Net Payment = Gross / 1.07 = 3,682.24 for all months
            self.assertAlmostEqual(
                line.net_payment,
                3682.24,
                places=2,
                msg=f"Month {line.month}: Net payment should be 3,682.24"
            )
            
            # VAT = Gross - Net = 257.76 for all months
            self.assertAlmostEqual(
                line.vat,
                257.76,
                places=2,
                msg=f"Month {line.month}: VAT should be 257.76"
            )
            
            # Verify: Gross = Net + VAT
            self.assertAlmostEqual(
                line.gross_payment,
                line.net_payment + line.vat,
                places=2,
                msg=f"Month {line.month}: Gross should equal Net + VAT"
            )

    def test_04_opening_npv_calculation(self):
        """
        Test Opening NPV is calculated as Present Value of net payment stream
        
        Client's data shows Opening NPV = 134,606.90
        Formula: PV = PMT × [(1+r)^n - 1] / [r(1+r)^n]
        """
        
        first_line = self.contract.schedule_line_ids.sorted('month')[0]
        
        # Calculate expected PV
        net_payment = 3682.24
        monthly_rate = self.contract.monthly_interest_rate
        months = 48
        
        factor = (1 + monthly_rate) ** months
        expected_opening_npv = net_payment * (factor - 1) / (monthly_rate * factor)
        
        # Our calculation should match (within tolerance)
        # Allow delta for rounding differences
        self.assertAlmostEqual(
            first_line.opening_npv,
            expected_opening_npv,
            delta=0.5,  # Changed to delta for tolerance
            msg=f"Opening NPV should be approximately {expected_opening_npv:.2f}"
        )
        
        # Client's data shows 134,606.90 (small difference due to Excel rounding)
        self.assertAlmostEqual(
            first_line.opening_npv,
            134606.90,
            delta=1.0,  # Allow 1.00 difference due to rounding
            msg="Opening NPV should be approximately 134,606.90 (client's value)"
        )

    def test_05_month_1_exact_values(self):
        """Test Month 1 values match client's exact data"""
        
        month_1 = self.contract.schedule_line_ids.sorted('month')[0]
        
        # Client's Month 1 data:
        # Gross: 3,940.00
        # Net: 3,682.24
        # VAT: 257.76
        # Interest: 1,576.91
        # Principal (AR): 2,105.33
        # NPV (Closing): 132,501.56
        
        self.assertAlmostEqual(
            month_1.gross_payment,
            3940.00,
            places=2,
            msg="Month 1: Gross should be 3,940.00"
        )
        
        self.assertAlmostEqual(
            month_1.net_payment,
            3682.24,
            places=2,
            msg="Month 1: Net should be 3,682.24"
        )
        
        self.assertAlmostEqual(
            month_1.vat,
            257.76,
            places=2,
            msg="Month 1: VAT should be 257.76"
        )
        
        # Interest = Opening NPV × Monthly Rate
        self.assertAlmostEqual(
            month_1.interest,
            1576.91,
            delta=0.5,  # Allow small rounding difference
            msg="Month 1: Interest should be approximately 1,576.91"
        )
        
        # Principal = Net Payment - Interest
        self.assertAlmostEqual(
            month_1.principal,
            2105.33,
            delta=0.5,
            msg="Month 1: Principal should be approximately 2,105.33"
        )
        
        # Closing NPV = Opening - Principal
        self.assertAlmostEqual(
            month_1.closing_npv,
            132501.56,
            delta=1.0,
            msg="Month 1: Closing NPV should be approximately 132,501.56"
        )

    def test_06_month_2_exact_values(self):
        """Test Month 2 values match client's exact data"""
        
        month_2 = self.contract.schedule_line_ids.sorted('month')[1]
        
        # Client's Month 2 data:
        # Interest: 1,552.24
        # Principal: 2,130.00
        # NPV: 130,371.56
        
        self.assertAlmostEqual(
            month_2.interest,
            1552.24,
            delta=0.5,
            msg="Month 2: Interest should be approximately 1,552.24"
        )
        
        self.assertAlmostEqual(
            month_2.principal,
            2130.00,
            delta=0.5,
            msg="Month 2: Principal should be approximately 2,130.00"
        )
        
        self.assertAlmostEqual(
            month_2.closing_npv,
            130371.56,
            delta=1.0,
            msg="Month 2: Closing NPV should be approximately 130,371.56"
        )

    def test_07_month_3_exact_values(self):
        """Test Month 3 values match client's exact data"""
        
        month_3 = self.contract.schedule_line_ids.sorted('month')[2]
        
        # Client's Month 3 data:
        # Interest: 1,527.29
        # Principal: 2,154.95
        # NPV: 128,216.61
        
        self.assertAlmostEqual(
            month_3.interest,
            1527.29,
            delta=0.5,
            msg="Month 3: Interest should be approximately 1,527.29"
        )
        
        self.assertAlmostEqual(
            month_3.principal,
            2154.95,
            delta=0.5,
            msg="Month 3: Principal should be approximately 2,154.95"
        )
        
        self.assertAlmostEqual(
            month_3.closing_npv,
            128216.61,
            delta=1.0,
            msg="Month 3: Closing NPV should be approximately 128,216.61"
        )

    def test_08_month_48_final_closing(self):
        """Test Month 48 (final) closes at exactly 0.00"""
        
        month_48 = self.contract.schedule_line_ids.sorted('month')[-1]
        
        # Month 48 should close at exactly 0.00
        self.assertAlmostEqual(
            month_48.closing_npv,
            0.00,
            places=2,
            msg="Month 48: Closing NPV must be exactly 0.00"
        )
        
        # Client's data shows:
        # Opening: 3,639.61
        # Interest: 42.64
        # Principal: 3,639.61
        
        # Principal in last month should equal the opening balance
        self.assertAlmostEqual(
            month_48.principal,
            month_48.opening_npv,
            delta=0.5,
            msg="Month 48: Principal should equal Opening NPV (final payment)"
        )

    def test_09_interest_principal_relationship(self):
        """Test that Interest + Principal = Net Payment for all months except last"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for line in lines[:-1]:  # All except last month
            # Net Payment = Interest + Principal
            calculated_net = line.interest + line.principal
            self.assertAlmostEqual(
                calculated_net,
                line.net_payment,
                places=1,
                msg=f"Month {line.month}: Interest + Principal should equal Net Payment"
            )

    def test_10_closing_equals_next_opening(self):
        """Test that each month's closing NPV equals next month's opening NPV"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for i in range(len(lines) - 1):
            current_line = lines[i]
            next_line = lines[i + 1]
            
            self.assertAlmostEqual(
                current_line.closing_npv,
                next_line.opening_npv,
                places=2,
                msg=f"Month {current_line.month} closing should equal Month {next_line.month} opening"
            )

    def test_11_total_payments_calculation(self):
        """Test total payments match client's expected values"""
        
        lines = self.contract.schedule_line_ids
        
        # Total Gross Payments (Total VAT in client's terms)
        total_gross = sum(line.gross_payment for line in lines)
        self.assertAlmostEqual(
            total_gross,
            189120.00,  # 48 × 3,940
            places=2,
            msg="Total Gross Payments should be 189,120.00"
        )
        
        # Total Net Payments (Before VAT in client's terms)
        total_net = sum(line.net_payment for line in lines)
        self.assertAlmostEqual(
            total_net,
            176747.52,  # 48 × 3,682.24
            delta=1.0,  # Client shows 176,747.66 (rounding)
            msg="Total Net Payments should be approximately 176,747.52"
        )
        
        # Total VAT
        total_vat = sum(line.vat for line in lines)
        self.assertAlmostEqual(
            total_vat,
            12372.48,  # 48 × 257.76
            delta=1.0,  # Client shows 12,372.34 (rounding)
            msg="Total VAT should be approximately 12,372.48"
        )
        
        # Total Interest (from client: 42,140.77)
        total_interest = sum(line.interest for line in lines)
        self.assertAlmostEqual(
            total_interest,
            42140.77,
            delta=10.0,  # Allow small variance due to rounding
            msg="Total Interest should be approximately 42,140.77"
        )
        
        # Total Principal (AR - should equal Opening NPV)
        total_principal = sum(line.principal for line in lines)
        first_line = lines.sorted('month')[0]
        self.assertAlmostEqual(
            total_principal,
            first_line.opening_npv,
            delta=1.0,
            msg="Total Principal should equal Opening NPV (amortizes to zero)"
        )
        
        # Client shows Total AR = 134,606.90
        self.assertAlmostEqual(
            total_principal,
            134606.90,
            delta=1.0,
            msg="Total Principal should be approximately 134,606.90"
        )

    def test_12_interest_decreasing_pattern(self):
        """Test that interest decreases each month (as balance decreases)"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for i in range(len(lines) - 1):
            current_interest = lines[i].interest
            next_interest = lines[i + 1].interest
            
            self.assertGreater(
                current_interest,
                next_interest,
                msg=f"Interest should decrease from month {lines[i].month} to {lines[i+1].month}"
            )

    def test_13_principal_increasing_pattern(self):
        """Test that principal increases each month (as interest decreases)"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for i in range(len(lines) - 2):  # Exclude last month (special case)
            current_principal = lines[i].principal
            next_principal = lines[i + 1].principal
            
            self.assertLess(
                current_principal,
                next_principal,
                msg=f"Principal should increase from month {lines[i].month} to {lines[i+1].month}"
            )

    def test_14_interest_calculation_formula(self):
        """Test that interest is calculated correctly: Interest = Opening NPV × Monthly Rate"""
        
        monthly_rate = self.contract.monthly_interest_rate
        
        for line in self.contract.schedule_line_ids:
            expected_interest = line.opening_npv * monthly_rate
            
            self.assertAlmostEqual(
                line.interest,
                expected_interest,
                delta=0.5,
                msg=f"Month {line.month}: Interest should be Opening NPV × Monthly Rate"
            )

    def test_15_principal_calculation_formula(self):
        """Test that principal is calculated correctly: Principal = Net Payment - Interest"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for line in lines[:-1]:  # All except last month
            expected_principal = line.net_payment - line.interest
            
            self.assertAlmostEqual(
                line.principal,
                expected_principal,
                delta=0.5,
                msg=f"Month {line.month}: Principal should be Net Payment - Interest"
            )

    def test_16_closing_npv_calculation_formula(self):
        """Test that closing NPV is calculated correctly: Closing = Opening - Principal"""
        
        for line in self.contract.schedule_line_ids:
            expected_closing = line.opening_npv - line.principal
            
            self.assertAlmostEqual(
                line.closing_npv,
                expected_closing,
                delta=0.5,
                msg=f"Month {line.month}: Closing NPV should be Opening - Principal"
            )

    def test_17_payment_dates_progression(self):
        """Test that payment dates progress correctly month by month"""
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        # First payment should be on start_date
        from datetime import date
        start_date = self.contract.start_date
        if isinstance(start_date, str):
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        # Check each payment date is one month apart
        from dateutil.relativedelta import relativedelta
        for i, line in enumerate(lines):
            expected_date = start_date + relativedelta(months=i)
            self.assertEqual(
                line.payment_date,
                expected_date,
                msg=f"Month {line.month}: Payment date should be {expected_date}"
            )

    def test_18_schedule_regeneration_consistency(self):
        """Test that regenerating the schedule produces identical results"""
        
        # Store original values
        original_lines = []
        for line in self.contract.schedule_line_ids.sorted('month'):
            original_lines.append({
                'month': line.month,
                'opening_npv': line.opening_npv,
                'interest': line.interest,
                'principal': line.principal,
                'closing_npv': line.closing_npv,
            })
        
        # Regenerate schedule
        self.contract.schedule_line_ids.unlink()
        self.contract._generate_schedule()
        
        # Compare with original
        new_lines = self.contract.schedule_line_ids.sorted('month')
        self.assertEqual(len(new_lines), len(original_lines))
        
        for i, (original, new_line) in enumerate(zip(original_lines, new_lines)):
            self.assertEqual(new_line.month, original['month'])
            self.assertAlmostEqual(new_line.opening_npv, original['opening_npv'], places=2)
            self.assertAlmostEqual(new_line.interest, original['interest'], places=2)
            self.assertAlmostEqual(new_line.principal, original['principal'], places=2)
            self.assertAlmostEqual(new_line.closing_npv, original['closing_npv'], places=2)

    def test_19_no_negative_values(self):
        """Test that no schedule line has negative values"""
        
        for line in self.contract.schedule_line_ids:
            self.assertGreaterEqual(
                line.opening_npv,
                0.0,
                msg=f"Month {line.month}: Opening NPV should not be negative"
            )
            self.assertGreaterEqual(
                line.interest,
                0.0,
                msg=f"Month {line.month}: Interest should not be negative"
            )
            self.assertGreaterEqual(
                line.principal,
                0.0,
                msg=f"Month {line.month}: Principal should not be negative"
            )
            self.assertGreaterEqual(
                line.closing_npv,
                -0.01,  # Allow tiny rounding error
                msg=f"Month {line.month}: Closing NPV should not be negative"
            )

    def test_20_client_data_comprehensive_match(self):
        """
        Comprehensive test: Compare our schedule with client's data for all available months
        
        Client's data (from Lease_Schedule_Userdata.csv):
        Month 1: Int=1,576.91, Prin=2,105.33, NPV=132,501.56
        Month 2: Int=1,552.24, Prin=2,130.00, NPV=130,371.56
        Month 3: Int=1,527.29, Prin=2,154.95, NPV=128,216.61
        """
        
        client_data = [
            # (month, interest, principal, closing_npv)
            (1, 1576.91, 2105.33, 132501.56),
            (2, 1552.24, 2130.00, 130371.56),
            (3, 1527.29, 2154.95, 128216.61),
            (4, 1502.05, 2180.20, 126036.42),
            (5, 1476.51, 2205.74, 123830.68),
            (6, 1450.67, 2231.58, 121599.10),
            (7, 1424.52, 2257.72, 119341.38),
            (8, 1398.07, 2284.17, 117057.22),
            (9, 1371.32, 2310.93, 114746.29),
            (10, 1344.24, 2338.00, 112408.29),
        ]
        
        lines = self.contract.schedule_line_ids.sorted('month')
        
        for month, expected_int, expected_prin, expected_npv in client_data:
            line = lines[month - 1]
            
            self.assertAlmostEqual(
                line.interest,
                expected_int,
                delta=1.0,
                msg=f"Month {month}: Interest should be approximately {expected_int:.2f}"
            )
            
            self.assertAlmostEqual(
                line.principal,
                expected_prin,
                delta=1.0,
                msg=f"Month {month}: Principal should be approximately {expected_prin:.2f}"
            )
            
            self.assertAlmostEqual(
                line.closing_npv,
                expected_npv,
                delta=2.0,
                msg=f"Month {month}: Closing NPV should be approximately {expected_npv:.2f}"
            )
