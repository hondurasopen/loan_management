# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class Tipogastos(models.Model):
    _name = "loan.tipos.gastos"

    name = fields.Char("Nombre de gasto", required=True)
    importe_gasto = fields.Float("Monto de gasto")
    cuenta_id =  fields.Many2one('account.account', 'Cuenta para gastos', required=True)
    observaciones = fields.Text("Observaciones")
    activo = fields.Boolean("Gasto activo", default=True)


class Tipogastosline(models.Model):
    _name = "loan.tipos.gastos.line"

    name = fields.Many2one("loan.tipos.gastos", "Gasto de prestamo", required=True)
    importe_gasto = fields.Float("Monto de gasto")
    prestamo_id = fields.Many2one("loan.management.loan", "Prestamo")

    @api.onchange("name")
    def onchangename(self):
        if self.name:
            self.importe_gasto = self.name.importe_gasto
