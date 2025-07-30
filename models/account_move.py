from odoo import fields,models

class AccountMove(models.Model):
    _inherit = 'account.move'

    contract_id = fields.Many2one('contract')