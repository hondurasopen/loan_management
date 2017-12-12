# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class LoanType(models.Model):
    _name = "loan.management.loan.type"
    _inherit = ['mail.thread']

    name = fields.Char("Tipo de Prestamo", required=True)
    active = fields.Boolean(string="Prestamo Activo", default=True)
    description = fields.Text("Notas Generales")
    monto_maximo = fields.Float("Monto Maximo", help="Monto maximo para el prestamo", required=True)
    plazo_pago_id = fields.Many2one("loan.management.loan.plazo", "Plazo de tiempo", required=True)
    tasa_interes_id = fields.Many2one("loan.management.loan.interes", "Tasa de Interes", required=True)
    metodo_calculo = fields.Selection([('cuotanivelada', 'Cuota Nivelada'), ('plana', 'Cuota Plana'), ('insoluto', 'Saldos Insolutos')], 
        string='Metodo de Cálculo', default='cuotanivelada', required=True)
    cuenta_ingreso =  fields.Many2one('account.account', 'Cuenta de Ingresos')
    cuenta_intereses_mora =  fields.Many2one('account.account', 'Ganancias por Mora', required=True)
    cuenta_intereses =  fields.Many2one('account.account', 'Ganancias por Interes', required=True)
    porcentaje_aportacion = fields.Float("Deducción para aportación %")
    porcentaje_seguro = fields.Float("% de seguro")
    cuenta_seguro =  fields.Many2one('account.account', 'Cuenta de seguro')


class LoanPlazo(models.Model):
    _name = "loan.management.loan.plazo"

    name = fields.Char("Nombre de Plazo")
    numero_plazo = fields.Integer("Numero de plazos", required=True)
    active = fields.Boolean(string="Activo", default=True)
    tipo_plazo = fields.Selection([('quincenal', 'Quincenas'), ('mensual', 'Meses'), ('diario', 'Diario')], string='Periodos', default='mensual')

    @api.model
    def create(self, vals):
        plazo = vals.get("numero_plazo")
        tipo = vals.get("tipo_plazo")
        description = ""
        if tipo == 'quincenal':
            description = "Quincenas"
        if tipo == "mensual":
            description = "Meses"

        vals["name"] = str(plazo) + " " + description
        return super(LoanPlazo, self).create(vals)


class LoanInteres(models.Model):
    _name = "loan.management.loan.interes"

    name = fields.Char("Nombre de Tasa")
    tasa_interes = fields.Float("Tasa de interes (%)", required=True)
    capitalizable = fields.Selection([('anual', 'Anual')], required=True, string='Capitalizable', default='anual')
    active = fields.Boolean(string="Activo", default=True)

    @api.model
    def create(self, vals):
        capitalizable = vals.get("capitalizable")
        tasa = vals.get("tasa_interes")
        vals["name"] = str(tasa) + "%" + " " + capitalizable
        return super(LoanInteres, self).create(vals)

