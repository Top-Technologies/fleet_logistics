from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WbLogisticsDailyLine(models.Model):
    _name = 'wb.logistics.daily.line'
    _description = 'WB Fleet Logistics Daily KM Log'
    _order = 'date, id'

    logistics_id = fields.Many2one(
        'wb.logistics.record', string='Logistics Record', required=True,
        ondelete='cascade', index=True,
    )
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    starting_km = fields.Float(string='Daily Starting KM', required=True, digits=(16, 2))
    ending_km = fields.Float(string='Daily Ending KM', required=True, digits=(16, 2))
    km_difference = fields.Float(
        string='Daily KM Difference', compute='_compute_km_difference',
        store=True, digits=(16, 2),
    )

    @api.depends('starting_km', 'ending_km')
    def _compute_km_difference(self):
        for line in self:
            line.km_difference = line.ending_km - line.starting_km

    @api.constrains('starting_km', 'ending_km')
    def _check_odometer_readings(self):
        for line in self:
            if line.starting_km < 0 or line.ending_km < 0:
                raise ValidationError(_('Daily odometer readings cannot be negative.'))
            if line.ending_km < line.starting_km:
                raise ValidationError(_('Daily Ending KM cannot be less than Daily Starting KM.'))
