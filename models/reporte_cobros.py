# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class Cuota(models.TransientModel):
    _name = 'loan.forcast.cuotas'
    _order = 'monto_cuota asc'

    treasury_id = fields.Many2one("loan.forecast","Forecast")
    prestamo_id = fields.Many2one("loan.management.loan", "# de Préstamo")
    cuota_id = fields.Many2one("loan.management.loan.cuota", "# de Cuota")
    fecha_pago = fields.Date("Fecha de pago")
    partner_id = fields.Many2one("res.partner", string="Cliente")
    state = fields.Selection(
        [('cotizacion', 'Cotizacion'), ('cancelada', 'Cancelada'), ('novigente', 'No vigente'), ('vigente', 'Vigente'),
        ('morosa', 'Morosa'),('pagada', 'Pagada')], string='Estado de cuota', default='cotizacion')

    monto_cuota = fields.Float("Monto de Cuota")
    saldo_prestamo = fields.Float("Saldo Pendiente")
    numero_cuota = fields.Integer("# de cuota", readonly=True)


class ReportCobros(models.TransientModel):
    _name = 'loan.forecast'
    _description = 'Proyección de Cobros'

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], default=get_currency)
    name = fields.Char(string="Description", required=True)
    start_date = fields.Date(string="Fecha de Inicio")
    end_date = fields.Date(string="Fecha Final")
    cuotas_ids = fields.One2many("loan.forcast.cuotas", "treasury_id", "Cuotas")
    state = fields.Selection([('draft','Borrador'),('progress','Progreso'),('done','Finalizado')], string='Estado',default='draft')
    total_proy = fields.Monetary("Total a Cobrar", readonly=True)
    numero_cuotas = fields.Integer("# Cuotas a Cobrar", readonly=True)
    es_reporte_mora = fields.Boolean("Es reporte de mora")


    @api.one
    @api.constrains('end_date', 'start_date')
    def check_date(self):
        if not self.es_reporte_mora:
            if self.start_date > self.end_date:
                raise exceptions.Warning(_('Error!:: La fecha final debe de ser mayor que la fecha inicial.'))

    @api.one
    def restart(self):
        if self.cuotas_ids:
            for cuotas in self.cuotas_ids:
                cuotas.unlink()
        return True

    @api.multi
    def button_calculate(self):
        self.restart()
        self.cuotas_proy()
        self.gettotales()

    @api.one
    def cuotas_proy(self):
        cuota_obj = self.env["loan.management.loan.cuota"]
        treasury_credito = self.env["loan.forcast.cuotas"]
        state = []
        cr_ids = False
        if not self.es_reporte_mora:
            state.append("novigente")
            state.append("vigente")
            state.append("morosa")
        else:
            state.append("morosa")

        if not self.es_reporte_mora:
            cr_ids = cuota_obj.search([('fecha_pago', '>=', self.start_date), ('fecha_pago', '<=', self.end_date),
            ('state', 'in', tuple(state))])
        else:
            cr_ids = cuota_obj.search([('state', 'in', tuple(state))])

        for crs in cr_ids:
            valores = {
                'treasury_id': self.id,
                'prestamo_id': crs.prestamo_id.id,
                'cuota_id': crs.id,
                'fecha_pago': crs.fecha_pago,
                'partner_id': crs.prestamo_id.afiliado_id.id,
                'state': crs.state,
                'monto_cuota': crs.monto_cuota,
                'numero_cuota': crs.numero_cuota,
                'saldo_prestamo': crs.saldo_prestamo,
            }
            new_id = treasury_credito.create(valores)

    def gettotales(self):
        if self.cuotas_ids:
            monto_cuota = 0.0
            numero_cuotas = 0
            for line in self.cuotas_ids:
                monto_cuota += line.monto_cuota
                numero_cuotas += 1

            self.total_proy = monto_cuota
            self.numero_cuotas = numero_cuotas

    @api.multi
    def action_done(self):
        self.write({'state':'done'})