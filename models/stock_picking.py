from odoo import fields,models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    smart_contract_id =  fields.Many2one('contract')