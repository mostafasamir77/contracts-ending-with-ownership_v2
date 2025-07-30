from odoo import fields, models, api


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_contract_payment = fields.Boolean(
        string='Contract Payment',
        compute='_compute_contract_payment',
        store=True,
        help='Payment related to a contract'
    )

    contract_id = fields.Many2one(
        'contract',
        string='Related Contract',
        compute='_compute_contract_payment',
        store=True
    )

    @api.depends('reconciled_invoice_ids.contract_id')
    def _compute_contract_payment(self):
        for payment in self:
            # Get contract from reconciled invoices
            contracts = payment.reconciled_invoice_ids.mapped('contract_id')
            contract = contracts[0] if contracts else False

            payment.contract_id = contract
            payment.is_contract_payment = bool(contract)