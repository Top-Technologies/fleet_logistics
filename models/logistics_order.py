from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class WbLogisticsOrder(models.Model):
    _name = 'wb.logistics.order'
    _description = 'WB Fleet Logistics Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'), tracking=True)
    vehicle_type_id = fields.Many2one('wb.logistics.vehicle.type', string='Vehicle Type', required=True,
                                      tracking=True, ondelete='restrict')
    vehicle_id = fields.Many2one('fleet.vehicle', string='Fleet Vehicle', ondelete='set null')
    plate_no = fields.Char(string='Plate Number', required=True, tracking=True)
    tag_ids = fields.Many2many('fleet.vehicle.tag', string='Tags')
    destination_from = fields.Char(string='From', required=True, tracking=True)
    destination_to = fields.Char(string='To', required=True, tracking=True)
    tr_reference = fields.Char(string='TR Reference', tracking=True)
    check_in = fields.Datetime(string='Time Check In', tracking=True)
    check_out = fields.Datetime(string='Time Check Out', tracking=True)
    time_out_hours = fields.Float(string='Time Out', compute='_compute_time_out_hours', store=True,
                                  digits=(16, 2), help='Elapsed time between check in and check out, in hours.')
    driver_id = fields.Many2one('wb.logistics.driver', string='Driver Name', required=True,
                                tracking=True, ondelete='restrict')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wb.logistics.order') or _('New')
        return super().create(vals_list)

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        for order in self:
            if order.vehicle_id:
                order.plate_no = order.vehicle_id.license_plate
                order.tag_ids = order.vehicle_id.tag_ids

    @api.onchange('tag_ids')
    def _onchange_tag_ids(self):
        for order in self:
            if order.vehicle_id and order.tag_ids and not (order.vehicle_id.tag_ids & order.tag_ids):
                order.vehicle_id = False
                order.plate_no = False

    @api.depends('check_in', 'check_out')
    def _compute_time_out_hours(self):
        for order in self:
            if order.check_in and order.check_out and order.check_out >= order.check_in:
                order.time_out_hours = (order.check_out - order.check_in).total_seconds() / 3600.0
            else:
                order.time_out_hours = 0.0

    @api.constrains('check_in', 'check_out')
    def _check_check_times(self):
        for order in self:
            if order.check_in and order.check_out and order.check_out < order.check_in:
                raise ValidationError(_('Check Out cannot be earlier than Check In.'))


