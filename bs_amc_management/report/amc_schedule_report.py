from collections import defaultdict
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, _

MONTH_LABELS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

# Column layout. AMC PERIOD spans two columns, and two columns carry a date on the
# upper header row over their caption, which is why the header is built by hand.
# Kept relative so inserting a column shifts everything after it on its own.
COL_CODE = 0
COL_AMC_REF = COL_CODE + 1
COL_SITE = COL_AMC_REF + 1
COL_FROM = COL_SITE + 1
COL_TO = COL_FROM + 1
COL_AMOUNT = COL_TO + 1
COL_DAYS = COL_AMOUNT + 1
COL_YEAR_AMOUNT = COL_DAYS + 1
COL_FIRST_MONTH = COL_YEAR_AMOUNT + 1
COL_TOTAL = COL_FIRST_MONTH + 12
COL_TILL_DATE = COL_TOTAL + 1
COL_REQUIRED = COL_TILL_DATE + 1
COL_SUPPLIER = COL_REQUIRED + 1


class AmcScheduleReportXlsx(models.AbstractModel):
    _name = 'report.bs_amc_management.report_amc_schedule'
    _inherit = 'amc.report.xlsx'
    _description = 'AMC Schedule Report XLSX'

    # ------------------------------------------------------------------
    # Data
    # ------------------------------------------------------------------

    def _amc_schedule_contracts(self, year, categ_id, site_ids):
        """Mother AMCs whose contract period overlaps the report year.

        Rows are driven by the contracts rather than by the provision entries, so a
        contract that has not been provisioned yet still shows up with its period,
        value and theoretical yearly amount, and simply carries empty months.
        """
        domain = [
            ('parent_amc_id', '=', False),
            ('start_date', '<=', date(year, 12, 31)),
            ('end_date', '>=', date(year, 1, 1)),
        ]
        if categ_id:
            domain.append(('product_categ_id', '=', categ_id))
        if site_ids:
            domain.append(('site_id', 'in', site_ids))
        return self.env['amc.contract'].search(domain, order='site_id, start_date, id')

    def _amc_schedule_monthly(self, contracts, year):
        """{contract id: {month number: signed amount}} taken from the provision entries.

        Months come from the line's accounting date, not from amc_provision_month, so a
        catch-up entry lands in the month it was actually booked in.

        Each (entry, contract) pair carries exactly one debit and one credit line of the
        same amount, so restricting to debit lines yields the magnitude once. A reversal
        flips the pair, hence the sign: it reduces the month it is booked in.

        Draft entries count. Provisioning creates entries in draft for review, so
        filtering on posted alone would leave the schedule empty; only cancelled
        entries are excluded. Read as sudo -- AMC roles drive contracts but need not
        hold accounting access.
        """
        amounts = defaultdict(lambda: defaultdict(float))
        if not contracts:
            return amounts
        lines = self.env['account.move.line'].sudo().search([
            ('amc_id', 'in', contracts.ids),
            ('move_id.amc_provision_type', '!=', False),
            ('parent_state', '!=', 'cancel'),
            ('date', '>=', date(year, 1, 1)),
            ('date', '<=', date(year, 12, 31)),
            ('debit', '>', 0.0),
        ])
        for line in lines:
            sign = -1 if line.move_id.amc_provision_type == 'reversal' else 1
            amounts[line.amc_id.id][line.date.month] += sign * line.debit
        return amounts

    def _amc_schedule_as_of(self, year):
        """(till date, required date) for the two trailing columns.

        Derived from today and clamped into the report year, so a report pulled for a
        past year shows the full year as provisioned and one for a future year shows
        nothing yet. Both dates are printed in the column headers so the basis of each
        figure is visible in the output.
        """
        today = fields.Date.context_today(self)
        if today.year > year:
            till = date(year, 12, 31)
        elif today.year < year:
            # Nothing in the report year has been reached yet.
            till = date(year, 1, 1) - relativedelta(days=1)
        else:
            till = today + relativedelta(day=31)
        required = till + relativedelta(days=1) + relativedelta(day=31)
        return till, required

    def _amc_schedule_row_values(self, contract, months, year, till, required):
        """Every computed figure for one contract row."""
        year_start, year_end = date(year, 1, 1), date(year, 12, 31)
        overlap_start = max(contract.start_date, year_start)
        overlap_end = min(contract.end_date, year_end)
        days = (overlap_end - overlap_start).days + 1 if overlap_end >= overlap_start else 0

        if till.year > year:
            till_months = 12
        elif till.year == year:
            till_months = till.month
        else:
            till_months = 0

        return {
            'days': days,
            # Theoretical share of the year, from the contract's own daily rate. Shown
            # beside TOTAL (what was actually provisioned) so the two can be compared.
            'year_amount': contract._amc_daily_rate() * days,
            'total': sum(months.values()),
            'till_date': sum(months.get(month, 0.0) for month in range(1, till_months + 1)),
            'required': months.get(required.month, 0.0) if required.year == year else 0.0,
        }

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _amc_schedule_formats(self, workbook):
        base = {'border': 1, 'valign': 'vcenter'}
        return {
            'title': workbook.add_format({'bold': True, 'font_size': 13, 'align': 'center'}),
            'header': workbook.add_format(dict(base, bold=True, align='center',
                                               text_wrap=True, bg_color='#F2F2F2')),
            'text': workbook.add_format(dict(base)),
            'code': workbook.add_format(dict(base, bold=True)),
            'date': workbook.add_format(dict(base, bold=True, num_format='dd-mmm-yy',
                                             align='center')),
            'amount': workbook.add_format(dict(base, bold=True, num_format='#,##0.00')),
            'number': workbook.add_format(dict(base, num_format='#,##0')),
            'number_bold': workbook.add_format(dict(base, bold=True, num_format='#,##0')),
            'integer': workbook.add_format(dict(base, num_format='0', align='center')),
        }

    def _amc_schedule_write_header(self, sheet, formats, year, till, required, title):
        head = formats['header']
        sheet.merge_range(0, COL_CODE, 0, COL_SUPPLIER, title, formats['title'])

        top, bottom = 2, 3
        sheet.merge_range(top, COL_CODE, bottom, COL_CODE, _('CODE'), head)
        sheet.merge_range(top, COL_AMC_REF, bottom, COL_AMC_REF, _('AMC REFERENCE'), head)
        sheet.merge_range(top, COL_SITE, bottom, COL_SITE, _('Site'), head)
        sheet.merge_range(top, COL_FROM, top, COL_TO, _('AMC PERIOD'), head)
        sheet.write(bottom, COL_FROM, _('From'), head)
        sheet.write(bottom, COL_TO, _('To'), head)
        sheet.merge_range(top, COL_AMOUNT, bottom, COL_AMOUNT, _('Amount'), head)

        # These two keep the year boundary on the upper row. lstrip('0') rather than
        # %-d, which is not portable across platforms.
        sheet.write(top, COL_DAYS, date(year, 1, 1).strftime('%d-%b-%y').lstrip('0'), head)
        sheet.write(bottom, COL_DAYS, _('NO OF DAYS IN %s') % year, head)
        sheet.write(top, COL_YEAR_AMOUNT, date(year, 12, 31).strftime('%d-%b-%y').lstrip('0'), head)
        sheet.write(bottom, COL_YEAR_AMOUNT, _('AMOUNT IN %s') % year, head)

        for index, label in enumerate(MONTH_LABELS):
            column = COL_FIRST_MONTH + index
            sheet.merge_range(top, column, bottom, column, label, head)

        sheet.merge_range(top, COL_TOTAL, bottom, COL_TOTAL, _('TOTAL'), head)
        sheet.merge_range(top, COL_TILL_DATE, bottom, COL_TILL_DATE,
                          _('Provision till date (%s)') % till.strftime('%d.%m.%Y'), head)
        sheet.merge_range(top, COL_REQUIRED, bottom, COL_REQUIRED,
                          _('Provision reqd as on %s') % required.strftime('%d.%m.%Y'), head)
        sheet.merge_range(top, COL_SUPPLIER, bottom, COL_SUPPLIER, _('Supplier'), head)

        sheet.set_column(COL_CODE, COL_CODE, 10)
        sheet.set_column(COL_AMC_REF, COL_AMC_REF, 20)
        sheet.set_column(COL_SITE, COL_SITE, 22)
        sheet.set_column(COL_FROM, COL_TO, 12)
        sheet.set_column(COL_AMOUNT, COL_AMOUNT, 13)
        sheet.set_column(COL_DAYS, COL_YEAR_AMOUNT, 12)
        sheet.set_column(COL_FIRST_MONTH, COL_TOTAL, 10)
        sheet.set_column(COL_TILL_DATE, COL_REQUIRED, 16)
        sheet.set_column(COL_SUPPLIER, COL_SUPPLIER, 24)
        sheet.set_row(top, 22)
        sheet.set_row(bottom, 32)
        sheet.freeze_panes(bottom + 1, COL_FROM)

    def _amc_schedule_write_row(self, sheet, row, formats, contract, months, values):
        sheet.write(row, COL_CODE, contract.site_id.code or '', formats['code'])
        sheet.write(row, COL_AMC_REF, contract.amc_ref or '', formats['code'])
        sheet.write(row, COL_SITE, contract.site_id.name or contract.name or '', formats['text'])
        if contract.start_date:
            sheet.write_datetime(row, COL_FROM, contract.start_date, formats['date'])
        else:
            sheet.write(row, COL_FROM, '', formats['date'])
        if contract.end_date:
            sheet.write_datetime(row, COL_TO, contract.end_date, formats['date'])
        else:
            sheet.write(row, COL_TO, '', formats['date'])

        sheet.write_number(row, COL_AMOUNT, contract.amc_charge_annum or 0.0, formats['amount'])
        sheet.write_number(row, COL_DAYS, values['days'], formats['integer'])
        sheet.write_number(row, COL_YEAR_AMOUNT, values['year_amount'], formats['number_bold'])

        for index in range(12):
            amount = months.get(index + 1)
            column = COL_FIRST_MONTH + index
            # Blank rather than zero for a month with no provision.
            if amount:
                sheet.write_number(row, column, amount, formats['number'])
            else:
                sheet.write(row, column, '', formats['number'])

        sheet.write_number(row, COL_TOTAL, values['total'], formats['number_bold'])
        sheet.write_number(row, COL_TILL_DATE, values['till_date'], formats['number'])
        sheet.write_number(row, COL_REQUIRED, values['required'], formats['number'])
        sheet.write(row, COL_SUPPLIER, contract.contractor_id.name or '', formats['text'])

    def generate_xlsx_report(self, workbook, data, records):
        data = data or {}
        # The wizard's data round-trips through the client, so nothing here can assume
        # a type.
        year = int(data.get('year') or fields.Date.context_today(self).year)
        categ_id = int(data['product_categ_id']) if data.get('product_categ_id') else False
        categ_name = data.get('product_categ_name') or ''
        site_ids = [int(one) for one in data.get('site_ids') or []]

        contracts = self._amc_schedule_contracts(year, categ_id, site_ids)
        monthly = self._amc_schedule_monthly(contracts, year)
        till, required = self._amc_schedule_as_of(year)

        title = _('AMC FOR %(categ)s FOR THE YEAR %(year)s',
                  categ=(categ_name or _('ALL CATEGORIES')).upper(), year=year)

        sheet = workbook.add_worksheet(_('AMC Schedule %s') % year)
        sheet.set_landscape()
        formats = self._amc_schedule_formats(workbook)
        self._amc_schedule_write_header(sheet, formats, year, till, required, title)

        row = 4
        for contract in contracts:
            months = monthly.get(contract.id, {})
            values = self._amc_schedule_row_values(contract, months, year, till, required)
            self._amc_schedule_write_row(sheet, row, formats, contract, months, values)
            row += 1
