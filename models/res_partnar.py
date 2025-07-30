from odoo import fields,models,api
from odoo.exceptions import ValidationError, UserError


class Customer(models.Model):
    _inherit =  'res.partner'


    # age = fields.Char(string="Age",compute='_compute_age')
    age = fields.Integer(string="Age",compute='_compute_age',store=True)
    mobile = fields.Char(string="Mobile")
    birth = fields.Date(string="Date Of Birth")
    city = fields.Char(string="City")
    id_expiry = fields.Date(string="Id Expiry Date")
    remaining_id_expiry = fields.Integer(compute='_compute_remaining_id_expiry',store=True)
    license_expiry_date = fields.Date(string="License Expiry Date")
    remaining_license_expiry_date = fields.Integer(compute='_compute_remaining_license_expiry_date',store=True)
    license_number = fields.Char(string="License Number")
    national_identity_number = fields.Char(string="National Identity Number", size=10)
    nationality = fields.Many2one('res.country',string="Nationality")
    id_attachment = fields.Char()
    license_attachment = fields.Char()
    is_leassing_customer = fields.Boolean(string="Is leassing customer ")

    @api.constrains('id_attachment', 'license_attachment', 'is_leassing_customer')
    def attachment_required_restriction(self):
        for rec in self:
            if rec.is_leassing_customer and (not rec.id_attachment or not rec.license_attachment):
                raise ValidationError("'Id Attachment' and 'License Attachment' are required fields when customer is a leasing customer.")


    @api.depends('birth')
    def _compute_age(self):
        for rec in self:
            if rec.birth:
                today = fields.Date.today()
                birth_date = rec.birth
                rec.age = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
                )
            else:
                rec.age = 0

    @api.depends('id_expiry')
    def _compute_remaining_id_expiry(self):
        for rec in self:
            if rec.id_expiry:
                today = fields.Date.today()
                delta = rec.id_expiry - today
                rec.remaining_id_expiry = delta.days
            else:
                rec.remaining_id_expiry = 0

    @api.depends('license_expiry_date')
    def _compute_remaining_license_expiry_date(self):
        for rec in self:
            if rec.license_expiry_date:
                today = fields.Date.today()
                delta = rec.license_expiry_date - today
                rec.remaining_license_expiry_date = delta.days
            else:
                rec.remaining_license_expiry_date = 0


    @api.constrains('national_identity_number')
    def national_identity_number_constrain(self):
        for rec in self:
            if rec.national_identity_number and rec.national_identity_number[0] not in ['1','2']:
                raise UserError("national identity number must start with '1' or '2'")
