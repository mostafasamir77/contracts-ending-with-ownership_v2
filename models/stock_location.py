from odoo import fields,models,api
from odoo.exceptions import ValidationError

class stockLocation(models.Model):
    _inherit = 'stock.location'

    is_leasing = fields.Boolean()

    rented = fields.Boolean()


    @api.constrains('rented')
    def _check_unique_name(self):
        for record in self:
            existing = self.search([
                ('rented', '=', True),
            ])
            if len(existing) > 1:
                raise ValidationError("Rented must be unique!")