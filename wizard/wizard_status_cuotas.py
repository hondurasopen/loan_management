# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardStatusCuotas(models.TransientModel):
    _name = 'loan.wizard.generar.cuotas'
    _description = 'Asistente de Status de Cuotas'

    # Información General
    date_generation = fields.Date(string="Fecha de Generación", required=True, default=fields.Date.today)

    @api.multi
    def generar_status_cuotas(self):
        prestamos_obj = self.env["loan.management.loan"].search([('state', '=', 'progreso')])
        date_generation = fields.Date.today()
        if self.date_generation:
            date_generation = self.date_generation

        for prestamo in prestamos_obj:
            for cuota in prestamo.cuota_ids:
                if date_generation > cuota.fecha_pago and not cuota.state == 'pagada' and not cuota.saldo_pendiente == 0.0:
                    fecha_run = (datetime.strptime(date_generation, '%Y-%m-%d'))
                    fecha_cuota = (datetime.strptime(cuota.fecha_pago, '%Y-%m-%d'))
                    diferencia_fecha = (fecha_run - fecha_cuota).days
                    mora = 0.0
                    if round(cuota.saldo_pendiente, 10) >= round(cuota.monto_cuota, 10):
                        print "Cuota de prestamo igual a saldo"
                        mora = ((cuota.monto_cuota * (prestamo.mora_id.tasa_mora / 100)) / 30) * diferencia_fecha
                        cuota.saldo_pendiente = cuota.monto_cuota + mora
                        cuota.mora = cuota.saldo_pendiente - cuota.monto_cuota
                    else:
                        mora = ((cuota.saldo_pendiente * (prestamo.mora_id.tasa_mora / 100)) / 30) * diferencia_fecha
                        cuota.saldo_pendiente = cuota.saldo_pendiente + mora
                        cuota.mora = mora
                    cuota.write({'state': 'morosa'})
                if date_generation == cuota.fecha_pago and not cuota.state == 'pagada' and not cuota.saldo_pendiente == 0.0:
                    cuota.write({'state': 'vigente'})
                    cuota.mora = 0.0
                    cuota.saldo_pendiente = cuota.monto_cuota
