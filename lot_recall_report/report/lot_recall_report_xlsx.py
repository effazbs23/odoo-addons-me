import io

from odoo import models


class LotRecallReportXlsx(models.AbstractModel):
    """Self-contained XLSX builder for lot.recall.report.

    The ERP23 catalog does not yet contain a shared ``base_xlsx`` report
    abstraction to reuse (this repository currently ships only this
    module), so the workbook is built directly with ``xlsxwriter``, which
    ships as a core Odoo dependency. Once a shared base_xlsx module exists
    elsewhere in the catalog, this class can be rewritten to extend it.
    """
    _name = 'lot.recall.report.xlsx'
    _description = 'Lot Recall Report XLSX Builder'

    def build(self, report):
        import xlsxwriter

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#6f42c1', 'font_color': 'white',
            'border': 1,
        })
        title_fmt = workbook.add_format({'bold': True, 'font_size': 14})
        cell_fmt = workbook.add_format({'border': 1})

        forward_sheet = workbook.add_worksheet('Forward Trace')
        forward_sheet.write(0, 0, 'Lot Recall Report - %s' % report.name, title_fmt)
        forward_headers = [
            'Lot/Serial', 'Customer', 'Sales Order', 'Delivery',
            'Quantity', 'UoM', 'Delivery Date',
        ]
        for col, header in enumerate(forward_headers):
            forward_sheet.write(2, col, header, header_fmt)
        row = 3
        for line in report.forward_line_ids:
            forward_sheet.write(row, 0, line.lot_id.name or '', cell_fmt)
            forward_sheet.write(row, 1, line.partner_id.name or '', cell_fmt)
            forward_sheet.write(row, 2, line.sale_order_id.name or '', cell_fmt)
            forward_sheet.write(row, 3, line.delivery_id.name or '', cell_fmt)
            forward_sheet.write(row, 4, line.quantity, cell_fmt)
            forward_sheet.write(row, 5, line.uom_id.name or '', cell_fmt)
            forward_sheet.write(row, 6, str(line.delivery_date or ''), cell_fmt)
            row += 1
        forward_sheet.autofit()

        backward_sheet = workbook.add_worksheet('Backward Trace')
        backward_headers = [
            'Lot/Serial', 'Type', 'Purchase Order', 'Manufacturing Order',
            'Vendor', 'Component Lot', 'Quantity', 'Date',
        ]
        for col, header in enumerate(backward_headers):
            backward_sheet.write(0, col, header, header_fmt)
        row = 1
        for line in report.backward_line_ids:
            backward_sheet.write(row, 0, line.lot_id.name or '', cell_fmt)
            backward_sheet.write(row, 1, line.source_type or '', cell_fmt)
            backward_sheet.write(row, 2, line.purchase_order_id.name or '', cell_fmt)
            backward_sheet.write(row, 3, line.production_id.name or '', cell_fmt)
            backward_sheet.write(row, 4, line.partner_id.name or '', cell_fmt)
            backward_sheet.write(row, 5, line.component_lot_id.name or '', cell_fmt)
            backward_sheet.write(row, 6, line.quantity, cell_fmt)
            backward_sheet.write(row, 7, str(line.delivery_date or ''), cell_fmt)
            row += 1
        backward_sheet.autofit()

        workbook.close()
        output.seek(0)
        return output.read()
