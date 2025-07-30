# models/res_config_settings.py
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    advance_product = fields.Many2one(
        'product.product',
        string="Advance Product",
        config_parameter='contracts_ending_with_ownership.advance_product_id',
        help="Select the product to use for advance payments"
    )