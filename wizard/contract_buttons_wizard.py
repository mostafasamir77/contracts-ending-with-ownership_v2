# from email.policy import default
from email.policy import default
from os.path import exists

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class CancelButton(models.TransientModel):
    _name = 'cancel.button'

    contract_wizard_id = fields.Many2one('contract')

    reason = fields.Text(required=1)

    def action_confirm(self):
        self.contract_wizard_id.states = 'cancelled'


class ConfirmButton(models.TransientModel):
    _name = 'confirm.button'

    contract_wizard_id = fields.Many2one('contract')

    def action_confirm(self):
        if self.contract_wizard_id.paid_advance_amount < self.contract_wizard_id.advance_amount_value:
            raise ValidationError("you have to pay advance amount first")

        # search for the record that have the boolean field is_rented is true
        rented_state = self.env['fleet.vehicle.state'].search([('is_rented', '=', True)])
        # change the state of fleet vehicle to rented
        self.contract_wizard_id.vehicle_id.state_id = rented_state.id

        # change the state of contract to open
        self.contract_wizard_id.states = 'open'

        # set the value of sequence
        if self.contract_wizard_id.name == 'New':
            self.contract_wizard_id.name = self.env['ir.sequence'].next_by_code('contract_seq')


class PickupButton(models.TransientModel):
    _name = 'pickup.button'

    contract_wizard_id = fields.Many2one('contract')

    km_out = fields.Float()
    # fuel_out = fields.Float()
    fuel_out = fields.Selection([
        ('0', '0'),
        ('0.25', '0.25'),
        ('0.5', '0.5'),
        ('0.75', '0.75'),
        ('1', '1'),
    ])

    ac_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    radio_stereo_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    screen_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    spere_time_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    tires_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    spere_tires_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    speedometer_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    keys_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    car_seats_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    safety_triangle_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    fire_extinguisher_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    first_aid_kit_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    vehicle_status_out = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    image_1 = fields.Binary()
    image_2 = fields.Binary()
    image_3 = fields.Binary()
    image_4 = fields.Binary()
    image_5 = fields.Binary()
    image_6 = fields.Binary()
    image_7 = fields.Binary()
    image_8 = fields.Binary()
    image_9 = fields.Binary()
    image_10 = fields.Binary()

    # Fields related to check out

    # Fields related to check out

    def action_confirm(self):
        """" set value to pickup page """

        # change state of contract to withdraw_inprogress
        self.contract_wizard_id.states = 'withdraw_inprogress'

        if self.contract_wizard_id.vehicle_id:
            self.contract_wizard_id.vehicle_id.odometer = self.km_out

        if not self.contract_wizard_id:
            raise UserError("No contract linked to this wizard.")

        vals = {
            'is_clickd_pickup': True,
            'km_out': self.km_out,
            'fuel_out': self.fuel_out,
            'ac_out': self.ac_out,
            'radio_stereo_out': self.radio_stereo_out,
            'screen_out': self.screen_out,
            'spere_time_out': self.spere_time_out,
            'tires_out': self.tires_out,
            'spere_tires_out': self.spere_tires_out,
            'speedometer_out': self.speedometer_out,
            'keys_out': self.keys_out,
            'car_seats_out': self.car_seats_out,
            'safety_triangle_out': self.safety_triangle_out,
            'fire_extinguisher_out': self.fire_extinguisher_out,
            'first_aid_kit_out': self.first_aid_kit_out,
            'vehicle_status_out': self.vehicle_status_out,
            'image_1': self.image_1,
            'image_2': self.image_2,
            'image_3': self.image_3,
            'image_4': self.image_4,
            'image_5': self.image_5,
            'image_6': self.image_6,
            'image_7': self.image_7,
            'image_8': self.image_8,
            'image_9': self.image_9,
            'image_10': self.image_10,
            'delivery_state': 'picked',
        }
        self.contract_wizard_id.write(vals)

        # create picking
        destination_location = self.env['stock.location'].search([('rented', '=', True)])

        stock_picking_rec = self.env['stock.picking'].create({
            'location_id': self.contract_wizard_id.picup_branch.id,
            'location_dest_id': destination_location.id,
            'move_type': 'direct',
            'picking_type_id': destination_location.warehouse_id.out_type_id.id,
            'smart_contract_id': self.contract_wizard_id.id,
        })


class ReturnButton(models.TransientModel):
    _name = 'return.button'

    contract_wizard_id = fields.Many2one('contract')

    km_in = fields.Float()
    fuel_in = fields.Selection([
        ('0', '0'),
        ('0.25', '0.25'),
        ('0.5', '0.5'),
        ('0.75', '0.75'),
        ('1', '1'),
    ])

    ac_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    radio_stereo_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    screen_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    spere_time_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    tires_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    spere_tires_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    speedometer_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    keys_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    car_seats_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    safety_triangle_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    fire_extinguisher_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    first_aid_kit_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')
    vehicle_status_in = fields.Selection([
        ('excellent', 'Excellent'),
        ('working', 'Working'),
        ('available', 'Available'),
    ], default='excellent')

    image_1_in = fields.Binary()
    image_2_in = fields.Binary()
    image_3_in = fields.Binary()
    image_4_in = fields.Binary()
    image_5_in = fields.Binary()
    image_6_in = fields.Binary()
    image_7_in = fields.Binary()
    image_8_in = fields.Binary()
    image_9_in = fields.Binary()
    image_10_in = fields.Binary()

    def action_confirm(self):
        """" set value to pickup page """

        # change state of contract to delivered_pending
        self.contract_wizard_id.states = 'delivered_pending'

        if self.contract_wizard_id.vehicle_id:
            self.contract_wizard_id.vehicle_id.odometer = self.km_in
            self.contract_wizard_id.vehicle_id.state_id = self.env['fleet.vehicle.state'].search(
                [('is_requested_for_withdraw', '=', True)]).id

        if not self.contract_wizard_id:
            raise UserError("No contract linked to this wizard.")

        vals = {
            'is_clickd_return': True,
            'km_in': self.km_in,
            'fuel_in': self.fuel_in,
            'ac_in': self.ac_in,
            'radio_stereo_in': self.radio_stereo_in,
            'screen_in': self.screen_in,
            'spere_time_in': self.spere_time_in,
            'tires_in': self.tires_in,
            'spere_tires_in': self.spere_tires_in,
            'speedometer_in': self.speedometer_in,
            'keys_in': self.keys_in,
            'car_seats_in': self.car_seats_in,
            'safety_triangle_in': self.safety_triangle_in,
            'fire_extinguisher_in': self.fire_extinguisher_in,
            'first_aid_kit_in': self.first_aid_kit_in,
            'vehicle_status_in': self.vehicle_status_in,
            'image_1_in': self.image_1_in,
            'image_2_in': self.image_2_in,
            'image_3_in': self.image_3_in,
            'image_4_in': self.image_4_in,
            'image_5_in': self.image_5_in,
            'image_6_in': self.image_6_in,
            'image_7_in': self.image_7_in,
            'image_8_in': self.image_8_in,
            'image_9_in': self.image_9_in,
            'image_10_in': self.image_10_in,
            'delivery_state': 'not_picked',
        }
        self.contract_wizard_id.write(vals)

        # create picking
        destination_location = self.env['stock.location'].search([('rented', '=', True)])

        stock_picking_rec = self.env['stock.picking'].create({
            'location_id': destination_location.id,
            'location_dest_id': self.contract_wizard_id.picup_branch.id,
            'move_type': 'direct',
            'picking_type_id': destination_location.warehouse_id.in_type_id.id,
            'smart_contract_id': self.contract_wizard_id.id,
        })

        # assign the stock picking related rec to the field that for smart button
        # self.contract_wizard_id.stock_picking_id = stock_picking_rec.id


class WithdrawButton(models.TransientModel):
    _name = 'withdraw.button'

    contract_wizard_id = fields.Many2one('contract')

    def action_confirm(self):
        self.contract_wizard_id.states = 'withdraw_inprogress'

        # search for the record that have the boolean field is_requested_for_withdraw is true
        requested_for_withdraw_state = self.env['fleet.vehicle.state'].search(
            [('is_requested_for_withdraw', '=', True)])
        # change the state of fleet vehicle to Requested for withdraw
        self.contract_wizard_id.vehicle_id.state_id = requested_for_withdraw_state.id


class OtherChargeButton(models.TransientModel):
    _name = 'other.charge.button'

    contract_wizard_id = fields.Many2one('contract')

    product = fields.Many2one('product.template')
    price = fields.Float()
    date = fields.Date()
    duration = fields.Integer()

    def action_confirm(self):
        # this for hide the other charge page by pass value to the field that in contact model
        self.contract_wizard_id.is_clicked_other_charge = True

        i = 0
        first_date = self.date
        while i < self.duration:
            self.env['other.charge.lines'].create({
                'contract_id': self.contract_wizard_id.id,
                'date': first_date,
                'product': self.product.id,
                'amount': self.price / self.duration,

            })
            first_date += relativedelta(months=1)
            i += 1


class CollectAdvanceAmountButton(models.TransientModel):
    _name = 'collect.advance.amount.button'

    contract_wizard_id = fields.Many2one('contract')

    journal = fields.Many2one('account.journal', domain=[('type', 'in', ('cash', 'bank'))])
    date = fields.Date(compute='_compute_date')
    amount = fields.Float()
    # pyment_method = fields.Many2one('account.payment.term')
    pyment_method = fields.Many2one('payment.method')

    # memo = fields.Char()

    @api.depends('amount')
    def _compute_date(self):
        self.date = fields.Date.today()

    def check_if_valid_amount(self):
        if self.amount > (
                self.contract_wizard_id.advance_amount_value_compute - self.contract_wizard_id.paid_advance_amount):
            raise UserError("this amount are more than the actual advance amount")

    def action_pay(self):
        # the validation
        self.check_if_valid_amount()

        # set value to paid_advance_amount that indicates to the paid amount and make sure that he paid all advance amount
        self.contract_wizard_id.paid_advance_amount += self.amount

        # Create the invoice
        invoice = self.env['account.move'].create({
            'contract_id': self.contract_wizard_id.id,
            'move_type': 'out_invoice',
            'partner_id': self.contract_wizard_id.customer_id.id,
            'journal_id': self.contract_wizard_id.picup_branch.warehouse_id.sales_journal.id,
            'invoice_date': self.date,
            'invoice_line_ids': [(0, 0, {
                'product_id': int(self.env['ir.config_parameter'].sudo().get_param(
                    'contracts_ending_with_ownership.advance_product_id')),
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, [])],
                'name': 'Advance Payment',
            })],
        })

        # Post the invoice
        invoice.action_post()
        # self.contract_wizard_id.invoice_id = invoice.id

        # Get the payment method line for the journal
        payment_method_line = self._get_payment_method_line(self.journal.id)

        # Create payment using the register payment wizard
        payment_wizard = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'journal_id': self.journal.id,
            'payment_method_line_id': payment_method_line.id,
            'amount': self.amount,
            'payment_date': self.date,
            'communication': f'Payment for Invoice {invoice.name}',
        })

        # Create the payment
        payments = payment_wizard.action_create_payments()

    def _get_payment_method_line(self, journal_id):
        """Get the payment method line for inbound payments for the specified journal"""
        payment_method_line = self.env['account.payment.method.line'].search([
            ('journal_id', '=', journal_id),
            ('payment_type', '=', 'inbound')
        ], limit=1)

        if not payment_method_line:
            # If no payment method line found for this journal, get the default manual method
            manual_method = self.env['account.payment.method'].search([
                ('code', '=', 'manual'),
                ('payment_type', '=', 'inbound')
            ], limit=1)

            if manual_method:
                # Create payment method line for this journal
                payment_method_line = self.env['account.payment.method.line'].create({
                    'journal_id': journal_id,
                    'payment_method_id': manual_method.id,
                    'name': manual_method.name,
                })

        return payment_method_line

    def _get_payment_journal_id(self):
        """Get the appropriate payment journal"""
        # Get default bank journal
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if bank_journal:
            return bank_journal.id

        # Fallback to cash journal
        cash_journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        return cash_journal.id if cash_journal else False


class AddStatement(models.TransientModel):
    _name = 'add.statement.button'

    contract_wizard_id = fields.Many2one('contract')

    statement_type = fields.Selection([
        ('phone', 'Phone'),
        ('visit', 'Visit'),
    ], required=True)

    call_status = fields.Selection([
        ('answered', 'Answered'),
        ('not_answered', 'Not Answered'),
        ('busy', 'Busy'),
    ])

    statement_status = fields.Selection([
        ('pledge_to_payment', 'Pledge To Payment'),
        ('objection', 'Objection'),
        ('other', 'Other'),
        ('customer_is_busy', 'Customer Is busy'),
    ])

    payment_date = fields.Date()

    details = fields.Text()

    def action_add_statement(self):
        statement_message = f"{self.statement_type} - {self.call_status} - {self.statement_status} - {self.payment_date} - {self.details}"

        list_words = statement_message.split(' - ')
        final_message = ""
        for word in list_words:
            if word == 'False':
                pass
            elif word == list_words[0]:
                final_message += word
            else:
                final_message += f" - {word}"

        self.env['statement.lines'].create({
            'contract_id': self.contract_wizard_id.id,
            'statement': final_message,
            'payment_date_for_notification': self.payment_date,
        })


class CloseContract(models.TransientModel):
    _name = 'close.contract.button'

    contract_wizard_id = fields.Many2one('contract')
    close_date = fields.Date(required=True)

    def action_close_contract(self):
        self.contract_wizard_id.states = 'closed'

        installment_lines = self.env['installment.lines'].search([
            ('contract_id', '=', self.contract_wizard_id.id),
        ])

        if not installment_lines:
            return

        # Get dates before any modifications
        installment_date_list = installment_lines.mapped('date')
        first_installment_date = min(installment_date_list)
        last_installment_date = max(installment_date_list)

        # Validation: close date cannot be before first installment
        if self.close_date < first_installment_date:
            raise ValidationError("You Can't set date before first installment date")

        # Validation: close date cannot be after last installment (unless exact match)
        if self.close_date not in installment_date_list and self.close_date > last_installment_date:
            raise ValidationError("The close date is bigger than last installment")

        # Collect records to unlink (avoid iterating while unlinking)
        records_to_unlink = self.env['installment.lines']

        for installment in installment_lines:
            # Skip if already paid or date is before/equal to close date
            if installment.remaining_amount == 0 or self.close_date >= installment.date:
                continue
            records_to_unlink |= installment

        # Unlink all collected records at once
        if records_to_unlink:
            records_to_unlink.unlink()

        # Create new installment if close_date is not in existing dates
        if self.close_date not in installment_date_list:
            self.env['installment.lines'].create({
                'contract_id': self.contract_wizard_id.id,
                'date': self.close_date,
                'amount': self.contract_wizard_id.installment_value,
            })

        # Update all remaining unpaid lines to 'due'
        self.env['installment.lines'].search([
            ('contract_id', '=', self.contract_wizard_id.id),
            ('state', '!=', 'paid')
        ]).write({
            'state': 'due',
        })


class RegisterPayment(models.TransientModel):
    _name = 'register.payment.button'

    contract_wizard_id = fields.Many2one('contract')

    journal_id = fields.Many2one('account.journal')
    amount = fields.Float()
    date = fields.Date(default=fields.Date.today())
    payment_method_id = fields.Many2one('account.payment.method')

    def action_register_payment(self):
        installment_lines = self.contract_wizard_id.installment_lines_ids
        amount_value = self.amount

        if self.amount == self.contract_wizard_id.total_remaining:
            self.contract_wizard_id.states = 'closed'

        # Process installments in priority order (late -> due -> not_yet_due)
        # and by date within each category
        ordered_lines = installment_lines.filtered(lambda l: l.remaining_amount > 0).sorted(
            key=lambda l: (
                {'late': 0, 'due': 1, 'not_yet_due': 2}.get(l.state, 3),
                l.date
            )
        )

        for line in ordered_lines:
            if amount_value <= 0:
                break

            # Calculate payment amount for this line
            payment_amount = min(line.remaining_amount, amount_value)

            if payment_amount > 0:
                # Update amounts
                line.paid_amount += payment_amount
                amount_value -= payment_amount

                print(f"Paid {payment_amount} for {line.state} installment. Remaining: {amount_value}")

            if line.remaining_amount == 0:
                line.state = 'done'

        if amount_value > 0:
            # Handle excess payment if needed
            print(f"Excess payment: {amount_value}")

        # for creating the invoice and payment =>

    # Create the invoice
        invoice = self.env['account.move'].create({
            'contract_id': self.contract_wizard_id.id,
            'move_type': 'out_invoice',
            'partner_id': self.contract_wizard_id.customer_id.id,
            'journal_id': self.contract_wizard_id.picup_branch.warehouse_id.sales_journal.id,
            'invoice_date': self.date,
            'invoice_line_ids': [(0, 0, {
                'product_id': int(self.env['ir.config_parameter'].sudo().get_param(
                    'contracts_ending_with_ownership.advance_product_id')),
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, [])],
                'name': 'Register Payment',
            })],
        })

        # Post the invoice
        invoice.action_post()
        # self.contract_wizard_id.invoice_id = invoice.id

        # Get the payment method line for the journal
        payment_method_line = self._get_payment_method_line(self.journal_id.id)

        # Create payment using the register payment wizard
        payment_wizard = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'journal_id': self.journal_id.id,
            'payment_method_line_id': payment_method_line.id,
            'amount': self.amount,
            'payment_date': self.date,
            'communication': f'Payment for Invoice {invoice.name}',
        })

        # Create the payment
        payments = payment_wizard.action_create_payments()


        self.contract_wizard_id.installment_lines_ids.payment_ids = [(4, invoice.matched_payment_ids.id)]

    def _get_payment_method_line(self, journal_id):
        """Get the payment method line for inbound payments for the specified journal"""
        payment_method_line = self.env['account.payment.method.line'].search([
            ('journal_id', '=', journal_id),
            ('payment_type', '=', 'inbound')
        ], limit=1)

        if not payment_method_line:
            # If no payment method line found for this journal, get the default manual method
            manual_method = self.env['account.payment.method'].search([
                ('code', '=', 'manual'),
                ('payment_type', '=', 'inbound')
            ], limit=1)

            if manual_method:
                # Create payment method line for this journal
                payment_method_line = self.env['account.payment.method.line'].create({
                    'journal_id': journal_id,
                    'payment_method_id': manual_method.id,
                    'name': manual_method.name,
                })

        return payment_method_line

    def _get_payment_journal_id(self):
        """Get the appropriate payment journal"""
        # Get default bank journal
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if bank_journal:
            return bank_journal.id

        # Fallback to cash journal
        cash_journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        return cash_journal.id if cash_journal else False



class PayOtherCharge(models.TransientModel):
    _name = 'pay.other.charge.button'

    contract_wizard_id = fields.Many2one('contract')

    journal_id = fields.Many2one('account.journal')
    amount = fields.Float()
    date = fields.Date(default=fields.Date.today())
    payment_method_id = fields.Many2one('account.payment.method')

    def action_pay_other_charge(self):
        other_charge_lines = self.contract_wizard_id.other_charge_lines_ids
        amount_value = self.amount

        # Process installments in priority order (late -> due -> not_yet_due)
        # and by date within each category
        ordered_lines = other_charge_lines.filtered(lambda l: l.remaining > 0).sorted(
            key=lambda l: (
                {'late': 0, 'due': 1, 'not_yet_due': 2}.get(l.state, 3),
                l.date
            )
        )

        for line in ordered_lines:
            if amount_value <= 0:
                break

            # Calculate payment amount for this line
            payment_amount = min(line.remaining, amount_value)

            if payment_amount > 0:
                # Update amounts
                line.paid += payment_amount
                amount_value -= payment_amount

                print(f"Paid {payment_amount} for {line.state} installment. Remaining: {amount_value}")

            if line.remaining == 0:
                line.state = 'done'

        if amount_value > 0:
            # Handle excess payment if needed
            print(f"Excess payment: {amount_value}")

        # for creating the invoice and payment =>

        # Create the invoice
        invoice = self.env['account.move'].create({
            'contract_id': self.contract_wizard_id.id,
            'move_type': 'out_invoice',
            'partner_id': self.contract_wizard_id.customer_id.id,
            'journal_id': self.contract_wizard_id.picup_branch.warehouse_id.sales_journal.id,
            'invoice_date': self.date,
            'invoice_line_ids': [(0, 0, {
                'product_id': int(self.env['ir.config_parameter'].sudo().get_param(
                    'contracts_ending_with_ownership.advance_product_id')),
                'quantity': 1,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, [])],
                'name': 'Pay Other Charge',
            })],
        })

        # Post the invoice
        invoice.action_post()
        # self.contract_wizard_id.invoice_id = invoice.id

        # Get the payment method line for the journal
        payment_method_line = self._get_payment_method_line(self.journal_id.id)

        # Create payment using the register payment wizard
        payment_wizard = self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids
        ).create({
            'journal_id': self.journal_id.id,
            'payment_method_line_id': payment_method_line.id,
            'amount': self.amount,
            'payment_date': self.date,
            'communication': f'Payment for Invoice {invoice.name}',
        })

        # Create the payment
        payments = payment_wizard.action_create_payments()

    def _get_payment_method_line(self, journal_id):
        """Get the payment method line for inbound payments for the specified journal"""
        payment_method_line = self.env['account.payment.method.line'].search([
            ('journal_id', '=', journal_id),
            ('payment_type', '=', 'inbound')
        ], limit=1)

        if not payment_method_line:
            # If no payment method line found for this journal, get the default manual method
            manual_method = self.env['account.payment.method'].search([
                ('code', '=', 'manual'),
                ('payment_type', '=', 'inbound')
            ], limit=1)

            if manual_method:
                # Create payment method line for this journal
                payment_method_line = self.env['account.payment.method.line'].create({
                    'journal_id': journal_id,
                    'payment_method_id': manual_method.id,
                    'name': manual_method.name,
                })

        return payment_method_line

    def _get_payment_journal_id(self):
        """Get the appropriate payment journal"""
        # Get default bank journal
        bank_journal = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if bank_journal:
            return bank_journal.id

        # Fallback to cash journal
        cash_journal = self.env['account.journal'].search([
            ('type', '=', 'cash'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        return cash_journal.id if cash_journal else False



class EditPayment(models.TransientModel):
    _name = 'edit.payment.button'

    contract_wizard_id = fields.Many2one('contract')


    payment_id = fields.Many2one('account.payment',string="Choose Payment",required=True)
# field for new register payment
    journal_id = fields.Many2one('account.journal',required=True)
    amount = fields.Float(required=True)
    date = fields.Date(default=fields.Date.today())
    payment_method_id = fields.Many2one('account.payment.method',required=True)
# field for new register payment
    reason = fields.Text(required=True)

    def action_edit_payment(self):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"this is the {self.contract_wizard_id.installment_lines_ids}")
        # print(f"this is the {self.contract_wizard_id.installment_lines_ids}")