from odoo import fields, models


class WbLogisticsVehicleType(models.Model):
    _name = 'wb.logistics.vehicle.type'
    _description = 'WB Logistics Vehicle Type'
    _order = 'name'

    name = fields.Char(string='Vehicle Type', required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('vehicle_type_name_unique', 'unique(name)', 'This vehicle type already exists.'),
    ]
