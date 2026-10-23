from io import BytesIO
from datetime import datetime, time

import xlsxwriter

from odoo import http
from odoo.http import request, content_disposition


class WbLogisticsReportController(http.Controller):
    @http.route('/fleet_logistics/report/xlsx', type='http', auth='user')
    def export_logistics_xlsx(self, ids='', **kwargs):
        try:
            record_ids = [int(value) for value in ids.split(',') if value]
        except ValueError:
            return request.not_found()
        if not record_ids:
            return request.not_found()

        records = request.env['wb.logistics.record'].browse(record_ids).exists()
        records.check_access_rights('read')
        records.check_access_rule('read')

        columns = [
            ('payment_period', 'Payment Period'), ('name', 'No'),
            ('company_name', 'Transport Company / Supplier'), ('driver_name', 'Driver Name'),
            ('vehicle_id', 'Fleet Vehicle'), ('plate_no', 'Plate Number'), ('region', 'Region'), ('technician', 'Technician'),
            ('vehicle_type', 'Vehicle Type'), ('date_start', 'Starting Date'), ('date_end', 'To Date'),
            ('working_days', 'Working Days'), ('working_days_reason', 'Reason for Working Date Change'),
            ('starting_km', 'Starting KM'), ('ending_km', 'Ending KM'), ('km_difference', 'KM Difference'),
            ('fuel_per_km', 'Fuel per KM'), ('fuel_liters', 'Total Fuel / Liter'), ('fuel_price', 'Fuel Price'),
            ('fuel_cost', 'Fuel Cost'), ('total_fuel_cost', 'Total Fuel Cost'), ('tcw40_qty', 'TCW 40 Quantity'),
            ('unit_cost', 'Unit Cost'), ('offloading_cost', 'Offloading Cost'), ('daily_rate', 'Daily Rate'),
            ('total_rent', 'Total Rent Payment'), ('fuel_payment', 'Total Fuel Payment'),
            ('car_rent_cost', 'Car Rent Cost'), ('total_payment', 'Total Payment'), ('remark', 'Remark'),
            ('currency_id', 'Currency'), ('rate_found', 'Rate Configured'),
        ]
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('WB Fleet Logistics')
        header = workbook.add_format({'bold': True, 'bg_color': '#D9EAF7', 'border': 1, 'text_wrap': True, 'valign': 'vcenter'})
        date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy'})
        money_format = workbook.add_format({'num_format': '#,##0.00'})
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, len(records), len(columns) - 1)
        sheet.set_row(0, 32)
        for col, (_, label) in enumerate(columns):
            sheet.write(0, col, label, header)
            sheet.set_column(col, col, min(max(len(label) + 2, 12), 27))
        monetary_fields = {'fuel_price', 'fuel_cost', 'total_fuel_cost', 'unit_cost', 'offloading_cost', 'daily_rate', 'total_rent', 'fuel_payment', 'car_rent_cost', 'total_payment'}
        for row, record in enumerate(records, 1):
            for col, (field_name, _) in enumerate(columns):
                value = record[field_name]
                if field_name in ('date_start', 'date_end') and value:
                    sheet.write_datetime(row, col, datetime.combine(value, time.min), date_format)
                elif field_name == 'vehicle_type':
                    labels = dict(record._fields['vehicle_type'].selection)
                    sheet.write(row, col, labels.get(value, value or ''))
                elif field_name == 'currency_id':
                    sheet.write(row, col, value.name or '')
                elif field_name == 'vehicle_id':
                    sheet.write(row, col, value.display_name or '')
                elif field_name in monetary_fields:
                    sheet.write_number(row, col, value or 0.0, money_format)
                elif isinstance(value, (int, float)):
                    sheet.write_number(row, col, value)
                else:
                    sheet.write(row, col, value or '')
        workbook.close()
        output.seek(0)
        filename = 'WB_Fleet_Logistics_Report.xlsx'
        return request.make_response(output.getvalue(), headers=[
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(filename)),
        ])
