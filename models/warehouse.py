from odoo import fields,models,api



class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    sales_journal = fields.Many2one('account.journal')