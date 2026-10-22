from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


REGION_SELECTION = [
    ('amhara', 'Amhara'),
    ('central_eth', 'Central ETH'),
    ('oromia', 'Oromia'),
    ('oromia_wollega', 'Oromia Wollega'),
    ('sidama', 'Sidama'),
    ('somali', 'Somali'),
    ('somali_liben', 'Somali Liben'),
    ('south_west', 'South West'),
    ('tigray', 'Tigray'),
    ('afar', 'Afar'),
    ('b_gumuz', 'B/Gumuz'),
    ('harari', 'Harari'),
    ('dire_dawa', 'Dire Dawa'),
    ('gambella', 'Gambella'),
    ('south_ethiopia', 'South Ethiopia'),
]

VEHICLE_TYPE_SELECTION = [
    ('fsr', 'FSR'),
    ('isuzu', 'Isuzu'),
    ('land_cruiser_1', 'Land Cruiser 1'),
    ('land_cruiser_2', 'Land Cruiser 2'),
]


class WbLogisticsRate(models.Model):
    _name = 'wb.logistics.rate'
    _description = 'WB Logistics Daily Rate'
    _order = 'region, vehicle_type'
    _rec_name = 'display_name'

    region = fields.Selection(REGION_SELECTION, required=True, index=True)
    vehicle_type = fields.Selection(VEHICLE_TYPE_SELECTION, required=True, index=True)
    daily_rate = fields.Monetary(required=True, currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.company.currency_id,
    )
    active = fields.Boolean(default=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('region', 'vehicle_type')
    def _compute_display_name(self):
        for rec in self:
            region = dict(REGION_SELECTION).get(rec.region, '')
            vehicle = dict(VEHICLE_TYPE_SELECTION).get(rec.vehicle_type, '')
            rec.display_name = '%s - %s' % (region, vehicle) if region and vehicle else _('New Rate')

    @api.constrains('region', 'vehicle_type', 'active')
    def _check_unique_active_rate(self):
        for rec in self.filtered('active'):
            duplicate = self.search([
                ('id', '!=', rec.id), ('region', '=', rec.region),
                ('vehicle_type', '=', rec.vehicle_type), ('active', '=', True),
            ], limit=1)
            if duplicate:
                raise ValidationError(_('There is already an active rate for this region and vehicle type. Archive it before adding another.'))
