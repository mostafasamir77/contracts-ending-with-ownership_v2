
from odoo import fields,models,api
from odoo.exceptions import ValidationError

class FleetVehicleState(models.Model):
    _inherit = 'fleet.vehicle.state'


    # adding field to fleet.vehicle.state for use it to chance the state later
    is_rented = fields.Boolean()
    is_ready = fields.Boolean()
    is_requested_for_withdraw = fields.Boolean()




    @api.model
    def write(self, vals):
        res = super(FleetVehicleState,self).write(vals)

        # validation for is_rented
        existing = self.search([
            ('is_rented', '=', True),
        ])
        if len(existing) > 1:
            raise ValidationError("is_rented must be unique!")

        # validation for is_ready
        existing = self.search([
            ('is_ready', '=', True),
        ])
        if len(existing) > 1:
            raise ValidationError("is_ready must be unique!")


        # validation for is_requested_for_withdraw
        existing = self.search([
            ('is_requested_for_withdraw', '=', True),
        ])
        if len(existing) > 1:
            raise ValidationError("is_requested_for_withdraw must be unique!")

        return res
