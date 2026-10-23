from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .logistics_rate import REGION_SELECTION, VEHICLE_TYPE_SELECTION


class WbLogisticsRecord(models.Model):
    _name = 'wb.logistics.record'
    _description = 'WB Fleet Logistics Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc, id desc'
    _rec_name = 'name'

    def action_export_logistics_xlsx(self):
        ids = self.ids or self.env.context.get('active_ids', [])
        return {
            'type': 'ir.actions.act_url',
            'url': '/fleet_logistics/report/xlsx?ids=%s' % ','.join(map(str, ids)),
            'target': 'new',
        }

    name = fields.Char(string='Reference', required=True, copy=False, default=lambda self: _('New'), tracking=True)
    payment_period = fields.Char(string='Payment Period', help='For example: Payment 1, Payment 2, or March 2026.')
    company_name = fields.Char(string='Transport Company / Supplier')
    driver_id = fields.Many2one('wb.logistics.driver', string='Driver Name', tracking=True, ondelete='restrict')
    driver_name = fields.Char(related='driver_id.name', store=True, string='Driver Name', readonly=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle', ondelete='set null', tracking=True)
    plate_no = fields.Char(string='Plate Number', tracking=True, help='Use this if the vehicle is not yet registered in Fleet.')
    region = fields.Selection(REGION_SELECTION, required=True, tracking=True, index=True)
    vehicle_type = fields.Selection(VEHICLE_TYPE_SELECTION, required=True, default='fsr', tracking=True)
    technician_id = fields.Many2one('wb.logistics.technician', string='Technician', tracking=True, ondelete='set null')
    technician = fields.Char(related='technician_id.name', store=True, string='Technician', readonly=True)
    date_start = fields.Date(string='Starting Date', required=True, tracking=True)
    date_end = fields.Date(string='To Date', required=True, tracking=True)
    working_days = fields.Integer(string='Working Days', default=0, help='Automatically filled from the dates when they are changed, but you can edit this value manually.')
    working_days_reason = fields.Text(string='Reason for Working Date Change')
    starting_km = fields.Float(string='Starting KM', digits=(16, 2))
    ending_km = fields.Float(string='Ending KM', digits=(16, 2))
    km_difference = fields.Float(string='KM Difference', compute='_compute_km_difference', store=True, digits=(16, 2))
    fuel_per_km = fields.Float(string='Fuel per KM', default=3.5, digits=(16, 4), help='Spreadsheet formula uses KM difference divided by this value.')
    fuel_price = fields.Monetary(string='Fuel Price', currency_field='currency_id')
    fuel_liters = fields.Float(string='Total Fuel / Liter', compute='_compute_fuel_liters', store=True, digits=(16, 2))
    fuel_cost = fields.Monetary(string='Fuel Cost', compute='_compute_fuel_cost', store=True, currency_field='currency_id')
    fuel_payment = fields.Monetary(string='Total Fuel Payment', compute='_compute_fuel_payment', store=True, currency_field='currency_id')
    total_fuel_cost = fields.Monetary(string='Total Fuel Cost', compute='_compute_total_fuel_cost', store=True, currency_field='currency_id')
    tcw40_qty = fields.Float(string='TCW 40 Quantity', digits=(16, 2))
    unit_cost = fields.Monetary(string='Unit Cost', currency_field='currency_id', default=300.0)
    offloading_cost = fields.Monetary(string='Offloading Cost', compute='_compute_offloading_cost', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', required=True, default=lambda self: self.env.company.currency_id)
    daily_rate = fields.Monetary(string='Daily Rate', currency_field='currency_id', default=0.0, readonly=False)
    total_rent = fields.Monetary(string='Total Rent Payment', compute='_compute_total_rent', store=True, currency_field='currency_id')
    car_rent_cost = fields.Monetary(string='Car Rent Cost', compute='_compute_car_rent_cost', store=True, currency_field='currency_id')
    total_payment = fields.Monetary(string='Total Payment', compute='_compute_total_payment', store=True, currency_field='currency_id')
    remark = fields.Text(string='Remark')
    rate_found = fields.Boolean(string='Rate Found', compute='_compute_rate_found', store=True)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        for rec in self:
            if rec.vehicle_id:
                rec.plate_no = rec.vehicle_id.license_plate
                # Vehicle type is intentionally not guessed from the vehicle model name.
                # Choose it explicitly so the rate lookup uses the correct category.

    @api.onchange('date_start', 'date_end')
    def _onchange_dates_set_working_days(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end >= rec.date_start:
                rec.working_days = (rec.date_end - rec.date_start).days + 1
            elif rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                rec.working_days = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('driver_id'):
                raise ValidationError(_('Select or create a driver.'))
            if not vals.get('working_days') and vals.get('date_start') and vals.get('date_end') and vals['date_end'] >= vals['date_start']:
                from datetime import date
                start = fields.Date.to_date(vals['date_start'])
                end = fields.Date.to_date(vals['date_end'])
                vals['working_days'] = (end - start).days + 1
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wb.logistics.record') or _('New')
        return super().create(vals_list)

    @api.depends('starting_km', 'ending_km')
    def _compute_km_difference(self):
        for rec in self:
            rec.km_difference = max(rec.ending_km - rec.starting_km, 0.0)

    @api.depends('km_difference', 'fuel_per_km')
    def _compute_fuel_liters(self):
        for rec in self:
            rec.fuel_liters = rec.km_difference / rec.fuel_per_km if rec.fuel_per_km > 0 else 0.0

    @api.depends('fuel_liters', 'fuel_price')
    def _compute_fuel_cost(self):
        for rec in self:
            rec.fuel_cost = rec.fuel_liters * rec.fuel_price

    @api.depends('fuel_cost')
    def _compute_fuel_payment(self):
        for rec in self:
            rec.fuel_payment = rec.fuel_cost

    @api.depends('fuel_cost', 'offloading_cost')
    def _compute_total_fuel_cost(self):
        for rec in self:
            rec.total_fuel_cost = rec.fuel_cost + rec.offloading_cost

    @api.depends('tcw40_qty', 'unit_cost')
    def _compute_offloading_cost(self):
        for rec in self:
            rec.offloading_cost = rec.tcw40_qty * rec.unit_cost

    @api.onchange('region', 'vehicle_type', 'currency_id')
    def _onchange_daily_rate(self):
        Rate = self.env['wb.logistics.rate']
        for rec in self:
            if not rec.region or not rec.vehicle_type:
                rec.daily_rate = 0.0
                continue
            rate = Rate.search([
                ('region', '=', rec.region), ('vehicle_type', '=', rec.vehicle_type),
                ('active', '=', True),
            ], limit=1)
            if rate:
                daily_rate = rate.daily_rate
                if rate.currency_id != rec.currency_id:
                    daily_rate = rate.currency_id._convert(rate.daily_rate, rec.currency_id, self.env.company, fields.Date.context_today(rec))
                rec.daily_rate = daily_rate
            else:
                rec.daily_rate = 0.0

    @api.depends('region', 'vehicle_type')
    def _compute_rate_found(self):
        Rate = self.env['wb.logistics.rate']
        for rec in self:
            rec.rate_found = bool(rec.region and rec.vehicle_type and Rate.search_count([
                ('region', '=', rec.region), ('vehicle_type', '=', rec.vehicle_type), ('active', '=', True),
            ]))

    @api.depends('daily_rate', 'working_days')
    def _compute_total_rent(self):
        for rec in self:
            rec.total_rent = rec.daily_rate * rec.working_days

    @api.depends('fuel_payment', 'offloading_cost')
    def _compute_car_rent_cost(self):
        for rec in self:
            rec.car_rent_cost = rec.fuel_payment + rec.offloading_cost

    @api.depends('car_rent_cost', 'total_rent')
    def _compute_total_payment(self):
        for rec in self:
            rec.total_payment = rec.car_rent_cost + rec.total_rent

    @api.constrains('working_days', 'date_start', 'date_end', 'working_days_reason')
    def _check_working_days_reason(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end >= rec.date_start:
                expected_days = (rec.date_end - rec.date_start).days + 1
                if rec.working_days != expected_days and not (rec.working_days_reason or '').strip():
                    raise ValidationError(_('Enter a reason when Working Days differs from the date range.'))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError(_('The end date cannot be earlier than the start date.'))

    @api.constrains('starting_km', 'ending_km')
    def _check_odometer(self):
        for rec in self:
            if rec.starting_km < 0 or rec.ending_km < 0:
                raise ValidationError(_('Odometer values cannot be negative.'))
            if rec.ending_km and rec.starting_km and rec.ending_km < rec.starting_km:
                raise ValidationError(_('Ending KM cannot be less than Starting KM.'))
