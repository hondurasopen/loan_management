# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class Customer(models.Model):
    _inherit = "res.partner"

    @api.one
    def get_ahorros(self):
        saldo_aportaciones = 0.0
        saldo_ahorros = 0.0
        retiros = 0.0
        for line in self.aportaciones_ids:
            if line.state == 'done':
                if line.tipo_aportacion == 'aportacion':
                    saldo_aportaciones += line.monto_aportacion
                else:
                    saldo_ahorros += line.monto_aportacion
        for rt in self.retiro_ids:
            if line.state == 'done':
                retiros = rt.monto_retiro
        self.total_ahorros = saldo_ahorros
        self.total_aportaciones = saldo_aportaciones
        self.total_retiros = retiros
        self.saldo_cliente = self.total_ahorros + self.total_aportaciones - self.total_retiros


    prestamos_ids = fields.One2many("loan.management.loan", "afiliado_id", "Prestamos de Cliente" )
    identidad = fields.Char("Identidad")
    rtn = fields.Char("RTN")
    aportaciones_ids = fields.One2many("loan.aportaciones", "cliente_id", "Prestamos de Cliente", domain=[('state', '=', 'done')])
    total_ahorros = fields.Monetary("Ahorros", compute=get_ahorros)
    total_aportaciones = fields.Monetary("Aportaciones", compute=get_ahorros)
    total_retiros = fields.Monetary("Retiros", compute=get_ahorros)
    saldo_cliente = fields.Monetary("Saldo de Cliente", compute=get_ahorros)
    retiro_ids = fields.One2many("loan.retiros", "cliente_id", "Retiros")
