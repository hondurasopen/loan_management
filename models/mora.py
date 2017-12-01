# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class LoanMora(models.Model):
    _name = "loan.management.loan.mora"
    _inherit = ['mail.thread']

    name = fields.Char("Mora ", required=True)
    active = fields.Boolean(string="Mora Activa", default=True)
    description = fields.Text("Notas Generales")
    dias_mora = fields.Integer("Dias de Mora")
    tasa_mora = fields.Float("Tasa de mora", help="Tasa de mora", required=True)

    # Cuenta contables
    cuenta_mora = fields.Many2one('account.account', 'Ingreso por mora', required=True)
