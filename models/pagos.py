# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class Aportaciones(models.Model):
    _name = "loan.pagos"
    _order = 'fecha asc'

    cliente_id = fields.Many2one("res.partner", "Cliente", required=True, domain=[('customer', '=', True)])
    fecha = fields.Date("Fecha de pago", required=True)
    prestamo_id = fields.Many2one("loan.management.loan", "Prestamo", required=True)
    importe_pagado = fields.Float("Importe Pagado", required=True)
    observaciones = fields.Text("Observaciones")
    state = state = fields.Selection([
            ('borrador','Borrador'),
            ('cancelado','Anulado'),
            ('done', 'Validado'),
        ], string='Estado', index=True)

    name = fields.Char("Número de pago")
    cuotas = fields.Many2many("loan.management.loan.cuota", string="Abono a Cuota(s)")
    asiento_id = fields.Many2one("account.move", "Asiento Contable")

    @api.one
    def cancelar_pago(self):
        if self.cuotas:
            if len(self.cuotas) == 1:
                self.cuotas.monto_pagado = self.cuotas.monto_pagado - self.importe_pagado
                self.cuotas.saldo_pendiente = self.monto_cuota
                if not self.cuotas.state == 'vigente':
                    self.cuotas.state = 'novigente'
            else:
                for cuota in self.cuotas:
                    obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', cuota.numero_cuota)])
                    obj_cuota.monto_pagado = obj_cuota.monto_pagado - obj_cuota.pago_ids.importe_pago_cuota
                    obj_cuota.saldo_pendiente = obj_cuota.monto_cuota
                    if not obj_cuota.state == 'vigente':
                        obj_cuota.state = 'novigente'

            self.write({'state': 'cancelado'})
            for asiento in self.asiento_id:
                asiento.unlink()
            self.observaciones = 'Pago anulado de préstamo'

