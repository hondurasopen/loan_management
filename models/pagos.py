# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class Aportaciones(models.Model):
    _name = "loan.pagos"
    _order = 'fecha asc'

    cliente_id = fields.Many2one("res.partner", "Cliente", required=True, domain=[('customer', '=', True)])
    fecha = fields.Date("Fecha de pago", required=True)
    prestamo_id = fields.Many2one("loan.management.loan", "Prestamo", required=True)
    importe_pagado = fields.Float("Importe Pagado", required=True)
    observaciones = fields.Char("Observaciones")
    state = state = fields.Selection([
            ('borrador','Borrador'),
            ('cancelado','Cancelado'),
            ('done', 'Validado'),
        ], string='Estado', index=True)

    name = fields.Char("Número de pago")
    cuotas = fields.Many2many("loan.management.loan.cuota", string="Abono a Cuota(s)")
    asiento_id = fields.Many2one("account.move", "Asiento Contable")

class Aportaciones(models.Model):
    _name = "loan.pagos.cuotas" 
    _rec_name = 'numero_cuota'

    pago_id = fields.Many2one("loan.pagos", "Número de Pago")
    monto_cuota = fields.Float("Monto de Cuota")
    mora = fields.Float("Mora")
    numero_cuota = fields.Integer("# de cuota", readonly=True)
    saldo_pendiente = fields.Float("Saldo de Cuota")

