from email.policy import default

from pkg_resources import require

from odoo import fields,models,api
from dateutil.relativedelta import relativedelta

from odoo.api import readonly
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _name = 'contract'
    _rec_name = "name"
    installment_lines_ids = fields.One2many('installment.lines', 'contract_id')
    other_charge_lines_ids = fields.One2many('other.charge.lines', 'contract_id')
    guarantors_ids = fields.One2many('guarantors','contract_id')
    statement_ids = fields.One2many('statement.lines','contract_id')

    name  = fields.Char(string="Name",readonly=1,default="New")
    delivery_state = fields.Selection([
        ('not_picked','Not picked'),
        ('picked','Picked'),
    ],default='not_picked')
    states = fields.Selection([
        ('draft','Draft'),
        ('open','Open'),
        ('withdraw_inprogress','Withdraw Inprogress'),
        ('delivered_pending','Delivered Pending'),
        ('delivered_indebet','Delivered Indebet'),
        ('closed','Closed'),
        ('cancelled','Cancelled'),
    ],default="draft")


    # this for check if the state is not draft to cancel delete option


    check_state_restriction = fields.Boolean(compute='_compute_check_state_restriction')

    @api.depends('states')
    def _compute_check_state_restriction(self):
        for rec in self:
            rec.check_state_restriction = (rec.states == 'draft')

    def unlink(self):
        for rec in self:
            if not rec.check_state_restriction:
                raise UserError("You cannot delete a contract unless it is in 'draft' state.")
        return super().unlink()

# start constrains section


    @api.constrains('guarantors_ids')
    def check_guarantors_ids(self):
        for rec in self:
            if len(rec.guarantors_ids) == 0:
                raise ValidationError("you can't save without set at least one guarantor")

    @api.constrains('customer_id')
    def check_validation_customer(self):
        existing = self.search([
            ('customer_id', '=', self.customer_id.id),
        ])
        if len(existing) > 1 and self.states in ['draft', 'open', 'withdraw', 'delivered_pending ']:
            raise UserError("customer in use by anther contract")


    @api.constrains('vehicle_id')
    def check_validation_vehicle(self):
        existing = self.search([
            ('vehicle_id', '=', self.vehicle_id.id),
        ])
        if len(existing) > 1 and self.states in ['draft', 'open', 'withdraw', 'delivered_pending ']:
            raise UserError("vehicle in use by anther contract")

# end constrains section

    # this for hide the other charge page
    is_clicked_other_charge = fields.Boolean()



    # start fields that compute the total of [amount,paid_amount,remaining]
    total_amount = fields.Float(compute="_compute_totals", store=True)
    total_paid_amount = fields.Float(compute="_compute_totals", store=True)
    total_remaining = fields.Float(compute="_compute_totals", store=True)
    current_due_amount = fields.Float(compute='_compute_totals', store=True)
    total_other_charge = fields.Float(compute='_compute_total_other_charge', store=True)

    @api.depends('installment_lines_ids.amount', 'installment_lines_ids.paid_amount', 'installment_lines_ids.remaining_amount')
    def _compute_totals(self):
        for rec in self:
            t_amount = 0.0
            t_paid_amount = 0.0
            t_remaining = 0.0
            t_remaining_for_current_due_amount = 0.0
            for line in rec.installment_lines_ids:
                t_amount += line.amount
                t_paid_amount += line.paid_amount
                t_remaining += line.remaining_amount
                # this condition check if the state in due or late and sum the remaining amount of this lines
                if line.state in ['due', 'late']:
                    t_remaining_for_current_due_amount += line.remaining_amount

            rec.total_amount = t_amount
            rec.total_paid_amount = t_paid_amount
            rec.total_remaining = t_remaining
            rec.current_due_amount = t_remaining_for_current_due_amount

    def _compute_total_paid_amount(self):
        for rec in self:
            total = 0
            for line in rec.installment_lines_ids:
                total += line.paid_amount
            rec.total_paid_amount = total

    def _compute_total_remaining(self):
        for rec in self:
            total = 0
            for line in rec.installment_lines_ids:
                total += line.remaining
            rec.total_remaining = total

    @api.depends('other_charge_lines_ids','other_charge_lines_ids.amount')
    def _compute_total_other_charge(self):
        for rec in self:
            rec.total_other_charge = sum(rec.other_charge_lines_ids.mapped('amount')) - sum(rec.other_charge_lines_ids.mapped('paid'))
    # end fields that compute the total of [amount,paid_amount,remaining]


    # start for stock picking smart button
    stock_picking_id = fields.Many2one('stock.picking')
    stock_picking_count = fields.Integer(compute='_compute_stock_picking_count')

    def _compute_stock_picking_count(self):
        for rec in self:
            picking_for_count = self.env['stock.picking'].search([
                ('smart_contract_id', '=', self.id),
            ])
            rec.stock_picking_count = len(picking_for_count)

    def action_open_stock_picking(self):

        # Action to open related stock picking
        self.ensure_one()

        # Search for related stock picking
        picking = self.env['stock.picking'].search([
            ('smart_contract_id', '=', self.id),
        ])

        # If only one picking, open form view
        if len(picking) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'stock picking',
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # If multiple Picking, open list view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related picking',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [
                ('smart_contract_id', '=', self.id),
            ],
            'context': {
                'smart_contract_id': self.id,
            },
            'target': 'current',
        }

    # end for stock picking smart button

    # start for invoice smart button

    invoice_ids = fields.Many2many('account.move', compute='_compute_invoices')
    invoices_count = fields.Integer(compute='_compute_invoices')

    def _compute_invoices(self):
        for rec in self:
            invoices = self.env['account.move'].search([
                ('move_type','=','out_invoice'),
                ('contract_id','=',self.id),
            ])
            rec.invoices_count = len(invoices)
            rec.invoice_ids = invoices.ids



    def action_open_invoice(self):

        # Action to open related invoices
        self.ensure_one()

        # Search for related invoices
        invoice = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('contract_id', '=', self.id),
        ])
        # If only one invoice, open form view
        if len(invoice) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'account move',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',
            }

        # If multiple invoice, open list view
        return {
            'type': 'ir.actions.act_window',
            'name': 'invoice',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('contract_id', '=', self.id),
            ],
            'target': 'current',
        }

    # end for invoice smart button





    # start for pyments smart buttons

    account_payment_ids = fields.Many2many('account.payment')



    count_payments = fields.Integer(compute='_compute_count_payments')

    def _compute_count_payments(self):
        for rec in self:
            rec.count_payments = len(rec.invoice_ids.mapped('matched_payment_ids'))

    def action_open_payments(self):
        self.ensure_one()
        payments = self.invoice_ids.mapped('matched_payment_ids')

        self.account_payment_ids = payments.ids
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', payments.ids)],
            'target': 'current',
        }

    # end for pyments smart buttons





    # Start of field for customer details

    customer_id = fields.Many2one('res.partner', domain=[('is_leassing_customer','=', True)],required=1)
    national_identity_number = fields.Char(related='customer_id.national_identity_number')
    mobile = fields.Char(related='customer_id.mobile')
    license_number = fields.Char(related='customer_id.license_number')
    # id_type_code = fields.Selection([
    #     ('national','National'),
    #     ('resident','Resident'),
    #     ('visitor','Visitor'),
    # ],string="Id Type Code", related='customer_id.id_type_code')
    city = fields.Char(related='customer_id.city')
    # End of field for customer details



    # Start of fields for vehicle information

    license_plate = fields.Char(related='vehicle_id.license_plate')
    vehicle_id = fields.Many2one('fleet.vehicle', domain=[
        ('state_id.is_ready', '=', True),
    ] , required=True)
    category_id = fields.Many2one(related='vehicle_id.category_id')
    model_id = fields.Many2one(related='vehicle_id.model_id')
    picup_branch = fields.Many2one('stock.location', domain=[
        ('is_leasing','=',True)
    ],required=True)



    # End of fields for vehicle information


    # Start of fields for financial information

    contract_date = fields.Date(default=fields.Date.today(),required=True)
    vehicle_price  = fields.Float()
    first_installment_date = fields.Date(required=1,default=fields.Date.today())
    advance_amount_type = fields.Selection([
        ('percentage','Percentage'),
        ('amount','Amount'),
    ], default="amount" ,required=1)
    advance_amount_value = fields.Float()

    paid_advance_amount = fields.Float(readonly=True)
    advance_amount_value_compute = fields.Float(compute='_compute_installment_value', store=True)

    installment_number = fields.Integer()
    installment_value = fields.Float(compute='_compute_installment_value', store=True)

    # for_depend_create_installments_lines = fields.Boolean(compute='create_installments_lines')


    @api.constrains('advance_amount_value')
    def advance_amount_value_constrain(self):
        for rec in self:
            if rec.advance_amount_value <= 0 :
                raise UserError("advance amount value must be grater than Zero ")

    @api.constrains('installment_number')
    def installment_number_constrain(self):
        for rec in self:
            if rec.installment_number <= 0 :
                raise ValidationError("Installmen Nnumber Have to Be grater than Zero")

    @api.constrains('vehicle_price')
    def vehicle_price_constrain(self):
        for rec in self:
            if rec.vehicle_price <= 0 :
                raise UserError("vehicle price value must be grater than Zero ")

    def create_installments_lines(self):
        self.installment_lines_ids.unlink()

        # creating lines for installment.lines model equal to the num of installment_number field
        for rec in self:
            i = 0
            installment_date = rec.first_installment_date
            while i < rec.installment_number:
                self.env['installment.lines'].create({
                    'contract_id': rec.id,
                    'date': installment_date,
                    'name': f"{i + 1}/{rec.installment_number}",
                    'amount': rec.installment_value,
                })
                installment_date += relativedelta(months=1)
                i += 1


    @api.model
    def create(self, vals):
        """Create method - receives vals dict, returns created record"""
        record = super().create(vals)  # This returns the created record
        print("Record created:", record.id)
        record.create_installments_lines()  # Call on the actual record
        return record


    @api.model
    def write(self, vals):
        res = super().write(vals)

        if 'first_installment_date' in vals or 'installment_number' in vals or 'vehicle_price' in vals or 'advance_amount_type' in vals or 'advance_amount_value' in vals:
            for rec in self:
                rec.create_installments_lines()
        return res


    @api.depends('vehicle_price', 'advance_amount_value', 'installment_number' , 'advance_amount_type')
    def _compute_installment_value(self):
        for rec in self:
            # if rec.installment_number <= 0:
            #     raise UserError("Installmen Nnumber Have to Be grater than Zero")

            if rec.advance_amount_type == 'amount' and rec.installment_number > 0 :
                rec.advance_amount_value_compute = rec.advance_amount_value
                rec.installment_value = (rec.vehicle_price - rec.advance_amount_value) / rec.installment_number
            elif rec.advance_amount_type == 'percentage'  and rec.installment_number > 0:
                rec.advance_amount_value_compute = (rec.advance_amount_value / 100) * rec.vehicle_price
                rec.installment_value = (rec.vehicle_price - (rec.advance_amount_value / 100) * rec.vehicle_price ) / rec.installment_number



    # End of fields for financial information

    # Start of fields for check out

    # this field to hide check out page if the user don't clicked pick up button
    is_clickd_pickup = fields.Boolean()

    ac_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    radio_stereo_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    screen_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    spere_time_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    tires_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    spere_tires_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    speedometer_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    keys_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])

    car_seats_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    safety_triangle_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    fire_extinguisher_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])

    first_aid_kit_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    vehicle_status_out = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])

    km_out = fields.Float()
    # fuel_out = fields.Float()
    fuel_out = fields.Selection([
        ('0','0'),
        ('0.25','0.25'),
        ('0.5','0.5'),
        ('0.75','0.75'),
        ('1','1'),
    ])

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

    # End of fields for check out


    # start of fields for check in

    # this field to hide check in page if the user don't clicked return button
    is_clickd_return =fields.Boolean()

    km_in = fields.Float()
    fuel_in = fields.Selection([
        ('0','0'),
        ('0.25','0.25'),
        ('0.5','0.5'),
        ('0.75','0.75'),
        ('1','1'),
    ])

    ac_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    radio_stereo_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    screen_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    spere_time_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    tires_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    spere_tires_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    speedometer_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    keys_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])

    car_seats_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    safety_triangle_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    fire_extinguisher_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])

    first_aid_kit_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])
    vehicle_status_in = fields.Selection([
        ('excellent','Excellent'),
        ('working','Working'),
        ('available' ,'Available'),
    ])



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

    # End of fields for check in

    def action_confirm(self):
        """" Change the state to open and set the sequence and create the installment records
        in installment.lines model

        """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.confirm_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_cancel(self):
        """ Open wizard view """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.cancel_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_pickup(self):
        """ Open wizard view for pickup """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.pickup_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_return(self):
        """ Open wizard view for return """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.return_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action



    def action_withdraw(self):
        """ Open wizard view for withdraw """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.withdraw_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action



    def action_other_charge(self):
        """ Open wizard view for other charge """


        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.other_charge_button_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_collect_advance_amount(self):
        """ Open wizard view for collect advance amount """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.collect_advance_amount_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_add_statement(self):
        """ Open wizard view for collect advance amount """
        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.add_statement_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def action_reopen(self):
        for rec in self:
            rec.states = 'open'

            r_state = rec.env['fleet.vehicle.state'].search([ ('is_rented','=', True) ])
            rec.vehicle_id.state_id = r_state.id


    def close_contract_statement(self):
        """ Open wizard view for contract statement """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.close_contract_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action



    def register_payment_button(self):
        """ Open wizard view for register payment """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.register_payment_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def pay_other_charge_button(self):
        """ Open wizard view for pay other charge """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.pay_other_charge_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action


    def edit_payment_button(self):
        """ Open wizard view for edit payment """

        action = self.env['ir.actions.actions']._for_xml_id('contracts_ending_with_ownership.edit_payment_wizard_action')
        action['context'] = {'default_contract_wizard_id' : self.id}
        return action



    # def test_button(self):
    #
    #     to_add_list = self.env['installment.lines']
    #
    #     to_add_list |= self.env['installment.lines'].search([])
    #
    #     print(to_add_list)
    #
    #     pass




class InstallmentLines(models.Model):
    _name = 'installment.lines'
    contract_id = fields.Many2one('contract',ondelete='cascade')

    date = fields.Date()
    name = fields.Char()
    amount = fields.Float()
    paid_amount = fields.Float()
    remaining_amount = fields.Float(compute='_compute_remaining_amount', store=True)
    payment_state = fields.Selection([
        ('not_paid','Not Paid'),
        ('partial','Partial'),
        ('fully_paid','Fully Paid'),
    ],default="not_paid",compute='_compute_payment_state')

    state = fields.Selection([
        ('not_yet_due','Not Yet Due'),
        ('due','Due'),
        ('late','Late'),
        ('done','Done'),
    ],default="not_yet_due")


    payment_ids = fields.Many2many('account.payment')

    @api.depends('amount', 'paid_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.amount - rec.paid_amount

    @api.depends('remaining_amount','paid_amount','amount')
    def _compute_payment_state(self):
        for rec in self:
            if rec.remaining_amount == 0 :
                rec.payment_state = 'fully_paid'
            elif rec.remaining_amount > 0 and rec.remaining_amount < rec.amount:
                rec.payment_state = 'partial'
            else:
                rec.payment_state = 'not_paid'

# start automated actions

    def check_payment_date(self):
        print("anakldlklllkllkkkkkkkkkkkkkkk")
        for line in self.env['installment.lines'].search([]):
            if line.remaining_amount == 0 :
                line.state = 'done'
            elif line.date < fields.Date.today():
                line.state = 'not_yet_due'
            elif line.date == fields.Date.today():
                line.state = 'due'
            elif line.date < fields.Date.today():
                line.state = 'late'

# end automated actions




class OtherChargeLines(models.Model):
    _name = 'other.charge.lines'

    contract_id = fields.Many2one('contract',ondelete='cascade')

    date = fields.Date()
    product = fields.Many2one('product.template')
    amount = fields.Float()
    paid = fields.Float()
    remaining = fields.Float(compute='_compute_remaining')
    state = fields.Selection([
        ('not_yet_due','Not Yet Due'),
        ('due','Due'),
        ('late','Late'),
        ('done','Done'),
    ],default="not_yet_due")

    @api.depends('amount', 'paid')
    def _compute_remaining(self):
        for rec in self:
            rec.remaining = rec.amount - rec.paid


class Guarantors(models.Model):
    _name = 'guarantors'

    contract_id = fields.Many2one('contract',ondelete='cascade')

    name = fields.Char()
    phone = fields.Char(size=10)
    id_number = fields.Char(required=True,size=10)
    expire_date_id = fields.Date()
    note = fields.Char()

    @api.constrains('id_number')
    def id_number_constrain(self):
        for rec in self:
            if rec.id_number and rec.id_number[0] not in ['1','2']:
                raise UserError("ID number must start with '1' or '2'")

    @api.constrains('phone')
    def phone_number_constrain(self):
        for rec in self:
            if rec.phone and rec.phone[0:2] !='05':
                raise UserError("Phone number must start with '05'")

            elif len(rec.phone) != 10 :
                raise UserError("the phone number must contain of 10 numbers")

    @api.onchange('id_number')
    def _onchange_id_number(self):
        if self.id_number:
            existing = self.search([
                ('id_number', '=', self.id_number),
                ('id', '!=', self.id or 0)  # Use 0 for new records
            ])
            if existing:
                return {
                    'warning': {
                        'title': 'Duplicate ID Number',
                        'message': f'This ID number already exists: {self.id_number}. Please use a different ID number.'
                    }
                }

    @api.constrains('id_number')
    def id_number_restriction(self):
        for rec in self:
            national_identity_number_list = self.env['contract'].search([]).mapped('customer_id.national_identity_number')

            existing = self.search([
                ('id_number', '=', rec.id_number),
                ('id', '!=', rec.id)
            ])
            if existing:
                raise ValidationError("This ID number already exists in guarantors : %s" % rec.id_number)

            elif rec.id_number in national_identity_number_list:
                raise ValidationError("This ID number already exists in customer before  : %s" % rec.id_number)

            elif len(rec.id_number) != 10 :
                raise UserError("the id number must contain of 10 numbers")




class StatementLines(models.Model):
    _name = 'statement.lines'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Add these mixins


    contract_id = fields.Many2one('contract',ondelete='cascade')

    statement = fields.Char()
    create_uid = fields.Many2one('res.users',string="Created By")
    create_date = fields.Date(string="Creation On")

    payment_date_for_notification = fields.Date()

    def automated_action_check_payment_date(self):
        print("Checking payment dates for notifications...")

        # Search for lines with future payment dates
        statement_lines = self.search([
            ('payment_date_for_notification', '=', fields.Date.today())
        ])

        for line in statement_lines:
            try:
                line.activity_schedule(
                    'mail.mail_activity_data_todo',
                    date_deadline=fields.Date.today(),
                    user_id=line.create_uid.id if line.create_uid else self.env.user.id,
                    summary='Payment Reminder Notification',
                    note=f'Customer mentioned they will pay today for line: {line.id}'
                )
                print(f"Activity scheduled for line {line.id}")

            except Exception as e:
                print(f"Error creating activity for line {line.id}: {str(e)}")




