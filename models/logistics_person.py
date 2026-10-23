from odoo import fields, models


class WbLogisticsDriver(models.Model):
    _name = 'wb.logistics.driver'
    _description = 'Logistics Driver'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('driver_name_unique', 'unique(name)', 'A driver with this name already exists.'),
    ]


class WbLogisticsTechnician(models.Model):
    _name = 'wb.logistics.technician'
    _description = 'Logistics Technician'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('technician_name_unique', 'unique(name)', 'A technician with this name already exists.'),
    ]
