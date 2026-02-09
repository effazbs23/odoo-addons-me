# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools import SQL


class LessorLeaseDashboard(models.Model):
    _name = 'lessor.lease.dashboard'
    _description = 'Lessor Lease Dashboard'
    _auto = False
    
    # This is a SQL view model for dashboard analytics
    
    @api.model
    def get_dashboard_data(self):
        """
        Get comprehensive dashboard data for lease management
        
        Returns dict with:
        - KPIs (counts, amounts)
        - Charts data
        - Recent activities
        """
        self.env.cr.execute("""
            -- Get active contracts count
            SELECT COUNT(*) as active_contracts
            FROM lessor_lease_contract
            WHERE state = 'active'
        """)
        active_contracts = self.env.cr.fetchone()[0] or 0
        
        self.env.cr.execute("""
            -- Get total lease value
            SELECT COALESCE(SUM(total_lease_value), 0) as total_value
            FROM lessor_lease_contract
            WHERE state IN ('active', 'confirmed')
        """)
        total_lease_value = self.env.cr.fetchone()[0] or 0
        
        self.env.cr.execute("""
            -- Get invoices this month
            SELECT COUNT(*) as count
            FROM lessor_lease_schedule_line
            WHERE EXTRACT(MONTH FROM payment_date) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM payment_date) = EXTRACT(YEAR FROM CURRENT_DATE)
            AND is_invoiced = True
        """)
        invoices_this_month = self.env.cr.fetchone()[0] or 0
        
        self.env.cr.execute("""
            -- Get unpaid invoices
            SELECT COUNT(*) as count
            FROM lessor_lease_schedule_line
            WHERE is_invoiced = True
            AND is_paid = False
            AND payment_date <= CURRENT_DATE
        """)
        unpaid_invoices = self.env.cr.fetchone()[0] or 0
        
        self.env.cr.execute("""
            -- Get overdue amount
            SELECT COALESCE(SUM(gross_payment), 0) as amount
            FROM lessor_lease_schedule_line
            WHERE is_invoiced = True
            AND is_paid = False
            AND payment_date < CURRENT_DATE
        """)
        overdue_amount = self.env.cr.fetchone()[0] or 0
        
        self.env.cr.execute("""
            -- Get pending recognition entries (draft journal entries)
            SELECT COUNT(DISTINCT am.id) as count
            FROM account_move am
            INNER JOIN lessor_lease_schedule_line lsl ON am.id = lsl.move_id
            WHERE am.state = 'draft'
        """)
        pending_recognitions = self.env.cr.fetchone()[0] or 0
        
        # Get chart data - Monthly revenue
        self.env.cr.execute("""
            SELECT 
                TO_CHAR(payment_date, 'YYYY-MM') as month,
                COALESCE(SUM(net_payment), 0) as revenue,
                COALESCE(SUM(vat), 0) as vat,
                COALESCE(SUM(interest), 0) as interest
            FROM lessor_lease_schedule_line
            WHERE payment_date >= CURRENT_DATE - INTERVAL '12 months'
            AND is_invoiced = True
            GROUP BY TO_CHAR(payment_date, 'YYYY-MM')
            ORDER BY month
        """)
        monthly_revenue = [
            {
                'month': row[0],
                'revenue': float(row[1]),
                'vat': float(row[2]),
                'interest': float(row[3])
            }
            for row in self.env.cr.fetchall()
        ]
        
        # Get contracts by status
        self.env.cr.execute("""
            SELECT state, COUNT(*) as count
            FROM lessor_lease_contract
            GROUP BY state
        """)
        contracts_by_status = [
            {'state': row[0], 'count': row[1]}
            for row in self.env.cr.fetchall()
        ]
        
        # Get upcoming payments (next 30 days)
        self.env.cr.execute("""
            SELECT 
                lsl.payment_date,
                llc.name as contract_name,
                lsl.gross_payment,
                lsl.is_invoiced
            FROM lessor_lease_schedule_line lsl
            INNER JOIN lessor_lease_contract llc ON lsl.contract_id = llc.id
            WHERE lsl.payment_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            AND lsl.is_paid = False
            ORDER BY lsl.payment_date
            LIMIT 10
        """)
        upcoming_payments = [
            {
                'date': row[0].strftime('%Y-%m-%d'),
                'contract': row[1],
                'amount': float(row[2]),
                'invoiced': row[3]
            }
            for row in self.env.cr.fetchall()
        ]
        
        return {
            'kpis': {
                'active_contracts': active_contracts,
                'total_lease_value': total_lease_value,
                'invoices_this_month': invoices_this_month,
                'unpaid_invoices': unpaid_invoices,
                'overdue_amount': overdue_amount,
                'pending_recognitions': pending_recognitions,
            },
            'charts': {
                'monthly_revenue': monthly_revenue,
                'contracts_by_status': contracts_by_status,
            },
            'upcoming_payments': upcoming_payments,
        }
