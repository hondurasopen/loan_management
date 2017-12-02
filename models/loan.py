# -*- encoding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning
from itertools import ifilter


class Loan(models.Model):
    _name = "loan.management.loan"
    _order = 'fecha_solicitud asc'
    _inherit = ['mail.thread']

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.one
    def get_fecha_vencimiento(self):
        for prestamo in self:
            if self.cuota_ids:
                fecha = datetime
                for line in  self.cuota_ids:
                    fecha = line.fecha_pago
                self.fecha_vencimiento = fecha

    @api.one
    def get_saldo(self):
        for prestamo in self:
            pagado = 0.0
            pendiente = 0.0
            mora = 0.0
            capital = 0.0
            for line in self.cuota_ids:
                if line.state == 'pagada':
                    pagado += line.monto_pagado
                if line.state == 'novigente' or line.state == 'vigente':
                    if not line.monto_pagado == 0.0 and line.monto_pagado < line.capital:
                        capital += (line.capital - line.monto_pagado)
                    if line.monto_pagado == 0.0:
                        capital += line.capital
                mora += line.mora
                pendiente += line.saldo_pendiente

            self.saldo_pendiente = round(pendiente, 2)
            self.total_capital = capital
            self.mora_prestamo = mora
            if self.mora_prestamo > 0.0:
                self.prestamo_moroso = True
            if round(pendiente, 2) == 0.0 and self.state == 'progreso':
                self.write({'state': 'liquidado'})

    @api.one
    def get_gastos_prestamo(self):
        for prestamo in self:
            total_gasto = 0.0
            for gasto in self.gastos_ids:
                total_gasto += gasto.importe_gasto
            self.gastos_administrativos = total_gasto

    @api.onchange("prestamo_id")
    def onchanrefinanciamiento(self):
        if self.prestamo_id and self.prestamo_refinanciado:
            self.saldo_prestamo_anterior = self.prestamo_id.total_capital

    # Prestamos refinanciados
    prestamo_refinanciado = fields.Boolean("Refinanciamiento", readonly=True)
    prestamo_id = fields.Many2one("loan.management.loan", "Refinanciar Préstamo")
    saldo_prestamo_anterior = fields.Monetary("Saldo Anterior")
    fecha_vencimiento = fields.Date("Fecha de Vencimiento", compute='get_fecha_vencimiento')
    # Valores numericos
    total_capital = fields.Float("Capital de Prestamo", compute='get_saldo')
    total_interes = fields.Float("Total de interes", states={'cotizacion': [('readonly', False)]})
    total_monto = fields.Float("Importe Total", states={'cotizacion': [('readonly', False)]})
    cuato_prestamo = fields.Float("Cuota de prestamo", states={'cotizacion': [('readonly', False)]})
    monto_solicitado = fields.Float("Monto solicitado", required=True)
    saldo_pendiente = fields.Float("Saldo pendiente", readonly=True, compute='get_saldo')
    mora_prestamo = fields.Float("Mora de prestamo", readonly=True, compute='get_saldo')
    # Gastos de prestamo
    monto_comision = fields.Monetary("Comisióm bancaria")
    total_desembolso = fields.Float("Monto a desembolsar")
    fecha_desembolso = fields.Date("Fecha de desembolso")
    referencia_desembolso = fields.Char("No. de Cheque/ Transferencia")
    notas_desembolso = fields.Text("Notas de desombolso")
    # Campos generales

    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], default=get_currency)
    name = fields.Char("Numero de prestamo", required=True, default=lambda self: self.env['ir.sequence'].get('prestamo'))
    afiliado_id = fields.Many2one("res.partner", "Cliente", required=True, domain=[('customer', '=', True)], states={'cotizacion': [('readonly', False)]})
    fecha_solicitud = fields.Date("Fecha de solicitud", required=True, default=fields.Date.today, states={'cotizacion': [('readonly', False)]})
    fecha_aprobacion = fields.Date("Fecha de aprobación", states={'cotizacion': [('readonly', False)]})
    fecha_pago = fields.Date("Fecha Inicial(Pagos)", states={'cotizacion': [('readonly', False)]})
    currency_id = fields.Many2one("res.currency", "Moneda", default=lambda self: self.env.user.company_id.currency_id)
    # Parametros
    plazo_pago = fields.Integer("Plazo de pago", required=True, states={'cotizacion': [('readonly', False)]})
    periodo_plazo_pago = fields.Selection([('dias', 'Diario'), ('quincenal', 'Quincenal'),  ('meses', 'Mensual')], string='Periodo', default='meses', required=True)
    tasa_interes = fields.Float("Tasa de interes Anual", required=True)
    notas = fields.Text("Notas")
    state = fields.Selection([('cotizacion', 'Cotizacion'), ('progress', 'Esperando Aprobacion'), ('rechazado', 'Rechazado'), ('aprobado', 'Aprobado'),
        ('desembolso', 'En desembolso'), ('progreso', 'En progreso'), ('liquidado', 'Liquidado')], string='Estado de prestamo',  readonly=True, default='cotizacion')
    tipo_prestamo_id = fields.Many2one("loan.management.loan.type", "Tipo de Prestamo", required=True, states={'cotizacion': [('readonly', False)]})
    cuota_ids = fields.One2many("loan.management.loan.cuota", "prestamo_id", "Cuotas de prestamo")
    doc_ids = fields.One2many("loan.management.tipo.documento", "prestamo_id", "Documentos de validacion")
    move_id = fields.Many2one('account.move', 'Asiento Contable', ondelete='restrict', readonly=True)
    journal_id = fields.Many2one("account.journal", "Banco", domain=[('type', '=', 'bank')])

    # Información de pagos
    pagos_ids = fields.One2many("loan.pagos", "prestamo_id", "Pagos de Cuotas")
    mora_id = fields.Many2one("loan.management.loan.mora", "Tasa Moratoria")
    prestamo_moroso = fields.Boolean("Prestamo en mora", compute='get_saldo')
    prestamo_done = fields.Boolean("Prestamo liquidado", compute='get_saldo')

    aportacion_id = fields.Many2one("loan.aportaciones", "Aportación de afiliado")

    gastos_ids = fields.One2many("loan.tipos.gastos.line", "prestamo_id", "Gastos de prestamos")
    gastos_administrativos = fields.Float("Total de gastos") #, compute='get_gastos_prestamo')
    monto_aportacion = fields.Float("Monto de Aportación")
    amount_total_text = fields.Char("Amount Total", compute = 'get_totalt', default='Cero')
    # Seguro de prestamo

    @api.onchange("gastos_ids")
    def onchange_gastos_ids(self):
        total_gasto = 0.0
        for gasto in self.gastos_ids:
            total_gasto += gasto.importe_gasto
        self.gastos_administrativos = total_gasto
        self.total_desembolso = self.monto_solicitado - self.gastos_administrativos

    @api.onchange("tipo_prestamo_id")
    def _get_tasa_plazo(self):
        self.plazo_pago = self.tipo_prestamo_id.plazo_pago_id.numero_plazo
        self.tasa_interes = self.tipo_prestamo_id.tasa_interes_id.tasa_interes
        #self.periodo_plazo_pago = self.tipo_prestamo_id.tasa_interes_id.capitalizable

    # Generar partida de desembolso
    def generar_partida_contable(self):
        self.total_desembolso = self.monto_solicitado - self.gastos_administrativos -self.monto_aportacion
        account_move = self.env['account.move']
        lineas = []
        vals_debit = {
            'debit': self.monto_solicitado,
            'credit': 0.0,
            'amount_currency': 0.0,
            'name': 'Desmbolso de prestamo',
            'account_id': self.afiliado_id.property_account_receivable_id.id,
            'partner_id': self.afiliado_id.id,
            'date': self.fecha_desembolso,
        }

        vals_credit = {
            'debit': 0.0,
            'credit': self.total_desembolso,
            'amount_currency': 0.0,
            'name': 'Desmbolso de prestamo',
            'account_id': self.journal_id.default_debit_account_id.id,
            'partner_id': self.afiliado_id.id,
            'date': self.fecha_desembolso,
        }
        if self.tipo_prestamo_id.porcentaje_aportacion > 0:
            vals_aportacion = {
                'debit': 0.0,
                'credit': self.monto_aportacion,
                'amount_currency': 0.0,
                'name': 'Aportación de afiliado por desembolso de prestamo',
                'account_id': self.afiliado_id.property_account_payable_id.id,
                'partner_id': self.afiliado_id.id,
                'date': self.fecha_desembolso,
            }
            lineas.append((0, 0, vals_aportacion))
        lineas.append((0, 0, vals_debit))
        lineas.append((0, 0, vals_credit))
        if self.gastos_administrativos > 0.0:
            for gastos in self.gastos_ids:
                valores_gastos = {
                    'debit': 0.0,
                    'credit': gastos.importe_gasto,
                    'amount_currency': 0.0,
                    'name': 'Gastos de prestamo',
                    'account_id': gastos.name.cuenta_id.id,
                    'partner_id': self.afiliado_id.id,
                    'date': self.fecha_desembolso,
                }
                lineas.append((0, 0, valores_gastos))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.fecha_desembolso,
            'ref': 'Desembolso de prestamo' + ' ' + self.name,
            'line_ids': lineas,
        }
        id_move = account_move.create(values)
        return id_move.id

    @api.multi
    def action_rechazar(self):
        self.write({'state': 'rechazado'})

    @api.multi
    def action_borrador(self):
        self.write({'state': 'cotizacion'})

    @api.multi
    def action_desembolso(self):
        self.write({'state': 'desembolso'})

    @api.multi
    def adelantar_cuotas(self):
        arreglo = []
        for cuotas in self.cuota_ids:
            if cuotas.state == 'vigente' or cuotas.state == 'morosa':
                raise Warning(_('No puede establecer cuotas en vigente ya que ya existe una cuota vigente o cuota(s) morosa(s)'))
            if cuotas.state == 'novigente':
                arreglo.append(cuotas.numero_cuota)
        numero_cuota = (min(arreglo))
        obj_cuotas = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.id), ('numero_cuota', '=', numero_cuota), ('state', '=', 'novigente')])
        if obj_cuotas:
            obj_cuotas.write({'state': 'vigente'})

    @api.multi
    def generar_contabilidad(self):
        if self.total_desembolso <= 0:
            raise Warning(_('El monto de desembolso debe de ser mayor que cero'))
        if not self.journal_id.default_debit_account_id:
            raise Warning(_('No existe cuenta asociada al banco, revise las parametrizaciones contables del diario'))
        self.generar_aportacion()
        self.write({'move_id': self.generar_partida_contable()})
        self.write({'state': 'progreso'})

        if self.prestamo_refinanciado:
            for cuota in self.prestamo_id.cuota_ids:
                if not cuota.state == 'pagada':
                    cuota.monto_pagado = cuota.saldo_pendiente
                    cuota.saldo_pendiente = 0.0
                    cuota.state = 'cancelada'
                    cuota.description = 'Préstamo liquidado por refinanciamiento'
            self.prestamo_id.write({'state': 'liquidado'})

    # Generar aportacion
    def generar_aportacion(self):
        if self.tipo_prestamo_id.porcentaje_aportacion > 0:
            obj_aportaciones = self.env["loan.aportaciones"]
            aportacion = self.total_desembolso * (self.tipo_prestamo_id.porcentaje_aportacion / 100)
            values = {
                'cliente_id': self.afiliado_id.id,
                'fecha': self.fecha_desembolso,
                'monto_aportacion': aportacion,
                'state': 'draft',
                'journal_id': self.journal_id.id,
                'tipo_aportacion': 'aportacion',
                'observaciones': "Aportación por deducción de prestamo",
                'state': 'done',
            }
            aport_id = obj_aportaciones.create(values)
            if aport_id:
                self.write({'aportacion_id': aport_id.id})
                self.monto_aportacion = aportacion

    @api.multi
    def action_aprobar(self):
        obj_loan_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.id)])
        for cuota in obj_loan_cuota:
            cuota.state = 'novigente'
        self.write({'state': 'aprobado'})
        self.saldo_pendiente = self.total_monto
        # TODO: RESTAR GASTOS DE PRESTAMOS
        self.total_desembolso = self.monto_solicitado
        self.fecha_aprobacion = datetime.now()

    @api.multi
    def action_solicitar_aprobacion(self):
        if self.monto_solicitado <= 0:
            raise Warning(_('El monto solicitado debe de ser mayor que cero'))
        self.write({'state': 'progress'})

    @api.one
    def get_calculadora_emi(self):
        self.total_interes = 0.0
        for fee in self.cuota_ids:
            self.total_interes += fee.interes

        self.total_monto = self.monto_solicitado + self.saldo_prestamo_anterior + self.total_interes
        self.cuato_prestamo = round(self.cuato_prestamo, 2)

    def fct_cuotanivelada(self):
        obj_loan_cuota = self.env["loan.management.loan.cuota"]
        obj_loan_cuota_unlink = obj_loan_cuota.search([('prestamo_id', '=', self.id)])
        if self.cuota_ids:
            for delete in obj_loan_cuota_unlink:
                delete.unlink()
        plazo = 1
        cuota_fecha = datetime.now()
        interest = 0.0
        rate_monthly = 0.0
        annuity_factor = 0.0
        saldo_acumulado = 0.0
        capital = 0.0
        monto_solicitado = self.monto_solicitado + self.saldo_prestamo_anterior

        if self.tipo_prestamo_id.tasa_interes_id.capitalizable == 'anual':
            if self.periodo_plazo_pago ==  'meses':
                rate_monthly = (self.tasa_interes / 12.0) / 100.0
            if self.periodo_plazo_pago == 'quincenal':
                rate_monthly = (self.tasa_interes / 24.0) / 100.0
            if self.periodo_plazo_pago == 'dias':
                rate_monthly = (self.tasa_interes / 365) / 100.0
            annuity_factor = (rate_monthly * ((1 + rate_monthly) ** self.plazo_pago)) / (((1 + rate_monthly) ** self.plazo_pago) - 1)
            self.cuato_prestamo = monto_solicitado * annuity_factor
        else:
            raise Warning(_('No se han definido tasas capitalizables mensuales y quincenales'))

        values = {
            'prestamo_id': self.id,
            'afiliado_id': self.afiliado_id.id,
            'monto_cuota': self.cuato_prestamo,
            'saldo_pendiente': self.cuato_prestamo,
            'state': 'cotizacion',
            'mora': 0.0,
        }
        if not self.fecha_pago:
            cuota_fecha = (datetime.strptime(self.fecha_solicitud, '%Y-%m-%d'))
        else:
            cuota_fecha = (datetime.strptime(self.fecha_pago, '%Y-%m-%d'))
        while plazo <= self.plazo_pago:
            #if cuota_fecha.day <= 15:
                # values["fecha_pago"] = cuota_fecha + relativedelta(day=30, months=plazo)
            # else:
                # values["fecha_pago"] = cuota_fecha + relativedelta(day=15, months=plazo)

            if plazo == 1:
                interest = monto_solicitado * rate_monthly
                capital = self.cuato_prestamo - interest
                values["interes"] = interest
                values["capital"] = capital
                saldo_acumulado = monto_solicitado - capital
                values["saldo_prestamo"] = saldo_acumulado
                values["fecha_pago"] = cuota_fecha
            if plazo > 1:
                interest = saldo_acumulado * rate_monthly
                capital = self.cuato_prestamo - interest
                values["interes"] = interest
                values["capital"] = capital
                saldo_acumulado = saldo_acumulado - capital
                values["saldo_prestamo"] = saldo_acumulado
                cuota_fecha = cuota_fecha + relativedelta(day=cuota_fecha.day, months=1)
                values["fecha_pago"] = cuota_fecha
            values["numero_cuota"] = plazo
            id_cuota = obj_loan_cuota.create(values)
            plazo +=  1
        self.get_calculadora_emi()


    def fct_cuotaplana(self):
        obj_loan_cuota = self.env["loan.management.loan.cuota"]
        obj_loan_cuota_unlink = obj_loan_cuota.search([('prestamo_id', '=', self.id)])
        if self.cuota_ids:
            for delete in obj_loan_cuota_unlink:
                delete.unlink()
        plazo = 1
        cuota_fecha = datetime.now()
        interest = 0.0
        saldo_acumulado = 0.0
        capital = 0.0
        monto_solicitado = self.monto_solicitado + self.saldo_prestamo_anterior
        if self.tipo_prestamo_id.tasa_interes_id.capitalizable == 'anual':
            self.cuato_prestamo = (monto_solicitado * (1 + (self.tasa_interes / 100.0))) / self.plazo_pago
            interest = (monto_solicitado * (self.tasa_interes / 100)) / self.plazo_pago
            capital = monto_solicitado / self.plazo_pago
        else:
            raise Warning(_('No se han definido tasas capitalizables mensuales y quincenales'))

        values = {
            'prestamo_id': self.id,
            'afiliado_id': self.afiliado_id.id,
            'monto_cuota': self.cuato_prestamo,
            'saldo_pendiente': self.cuato_prestamo,
            'mora': 0.0,
            #'capital':capital,
            #'interes':interes,
            'state': 'cotizacion',
        }
        if not self.fecha_pago:
            cuota_fecha = (datetime.strptime(self.fecha_solicitud, '%Y-%m-%d'))
        else:
            cuota_fecha = (datetime.strptime(self.fecha_pago, '%Y-%m-%d'))
        while plazo <= self.plazo_pago:
            if plazo == 1:
                values["interes"] = interest
                values["capital"] = capital
                saldo_acumulado = monto_solicitado - capital
                values["saldo_prestamo"] = saldo_acumulado
                values["fecha_pago"] = cuota_fecha
            if plazo > 1:
                values["interes"] = interest
                values["capital"] = capital
                saldo_acumulado = saldo_acumulado - capital
                values["saldo_prestamo"] = saldo_acumulado
                cuota_fecha = cuota_fecha + relativedelta(day=cuota_fecha.day, months=1)
                values["fecha_pago"] = cuota_fecha
            values["numero_cuota"] = plazo
            id_cuota = obj_loan_cuota.create(values)
            plazo +=  1
        self.get_calculadora_emi()


    @api.one
    def get_generar_cuotas(self):
        if self.plazo_pago <= 0:
            raise Warning(_('Los plazos de pago deben ser mayor que 1'))
        if self.tipo_prestamo_id.metodo_calculo == 'cuotanivelada':
            self.fct_cuotanivelada()
        if self.tipo_prestamo_id.metodo_calculo == 'plana':
            self.fct_cuotaplana()

    @api.model
    def _calcular_cuota(self, valor_prestamo, interes, plazo_tiempo):
        cuota = (valor_prestamo * (1 + interes / 100.0)) / plazo_tiempo
        return cuota

    @api.model
    def _calcular_capital_cuota(self, valor_prestamo, plazo_tiempo):
        capital = valor_prestamo / plazo_tiempo
        return capital

    @api.model
    def _calcular_interes_cuota(self, valor_prestamo, interes, plazo_tiempo):
        interes = (valor_prestamo * interes / 100.0) / plazo_tiempo
        return interes


    @api.one
    def get_totalt(self):
        self.amount_total_text=''

        if self.currency_id:
            self.amount_total_text=self.to_word(self.monto_solicitado,self.currency_id.name)
        else:
            self.amount_total_text =self.to_word(self.monto_solicitado,self.user_id.company_id.currency_id.name)
        return True

    def to_word(self,number, mi_moneda):
        valor= number
        number=int(number)
        centavos=int((round(valor-number,2))*100)
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )

        DECENAS = (
            'VENTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN ')

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
            )
        if mi_moneda != None:
            try:
                moneda = ifilter(lambda x: x['currency'] == mi_moneda, MONEDAS).next()
                if number < 2:
                    moneda = moneda['singular']
                else:
                    moneda = moneda['plural']
            except:
                return "Tipo de moneda inválida"
        else:
            moneda = ""
        converted = ''
        if not (0 < number < 999999999):
            return 'No es posible convertir el numero a letras'

        number_str = str(number).zfill(9)
        millones = number_str[:3]
        miles = number_str[3:6]
        cientos = number_str[6:]

        if(millones):
            if(millones == '001'):
                converted += 'UN MILLON '
            elif(int(millones) > 0):
                converted += '%sMILLONES ' % self.convert_group(millones)

        if(miles):
            if(miles == '001'):
                converted += 'MIL '
            elif(int(miles) > 0):
                converted += '%sMIL ' % self.convert_group(miles)

        if(cientos):
            if(cientos == '001'):
                converted += 'UN '
            elif(int(cientos) > 0):
                converted += '%s ' % self.convert_group(cientos)
        if(centavos)>0:
            converted+= "con %2i/100 "%centavos
        converted += moneda
        return converted.title()


    def convert_group(self,n):
        UNIDADES = (
            '',
            'UN ',
            'DOS ',
            'TRES ',
            'CUATRO ',
            'CINCO ',
            'SEIS ',
            'SIETE ',
            'OCHO ',
            'NUEVE ',
            'DIEZ ',
            'ONCE ',
            'DOCE ',
            'TRECE ',
            'CATORCE ',
            'QUINCE ',
            'DIECISEIS ',
            'DIECISIETE ',
            'DIECIOCHO ',
            'DIECINUEVE ',
            'VEINTE '
        )
        DECENAS = (
            'VEINTI',
            'TREINTA ',
            'CUARENTA ',
            'CINCUENTA ',
            'SESENTA ',
            'SETENTA ',
            'OCHENTA ',
            'NOVENTA ',
            'CIEN '
        )

        CENTENAS = (
            'CIENTO ',
            'DOSCIENTOS ',
            'TRESCIENTOS ',
            'CUATROCIENTOS ',
            'QUINIENTOS ',
            'SEISCIENTOS ',
            'SETECIENTOS ',
            'OCHOCIENTOS ',
            'NOVECIENTOS '
        )
        MONEDAS = (
            {'country': u'Colombia', 'currency': 'COP', 'singular': u'PESO COLOMBIANO', 'plural': u'PESOS COLOMBIANOS', 'symbol': u'$'},
            {'country': u'Honduras', 'currency': 'HNL', 'singular': u'Lempira', 'plural': u'Lempiras', 'symbol': u'L'},
            {'country': u'Estados Unidos', 'currency': 'USD', 'singular': u'DÓLAR', 'plural': u'DÓLARES', 'symbol': u'US$'},
            {'country': u'Europa', 'currency': 'EUR', 'singular': u'EURO', 'plural': u'EUROS', 'symbol': u'€'},
            {'country': u'México', 'currency': 'MXN', 'singular': u'PESO MEXICANO', 'plural': u'PESOS MEXICANOS', 'symbol': u'$'},
            {'country': u'Perú', 'currency': 'PEN', 'singular': u'NUEVO SOL', 'plural': u'NUEVOS SOLES', 'symbol': u'S/.'},
            {'country': u'Reino Unido', 'currency': 'GBP', 'singular': u'LIBRA', 'plural': u'LIBRAS', 'symbol': u'£'}
        )
        output = ''

        if(n == '100'):
            output = "CIEN "
        elif(n[0] != '0'):
            output = CENTENAS[int(n[0]) - 1]

        k = int(n[1:])
        if(k <= 20):
            output += UNIDADES[k]
        else:
            if((k > 30) & (n[2] != '0')):
                output += '%sY %s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])
            else:
                output += '%s%s' % (DECENAS[int(n[1]) - 2], UNIDADES[int(n[2])])

        return output

    def addComa(self, snum ):
        s = snum;
        i = s.index('.') # Se busca la posición del punto decimal
        while i > 3:
            i = i - 3
            s = s[:i] +  ',' + s[i:]
        return s



class Loanline(models.Model):
    _name = "loan.management.loan.cuota"
    _rec_name = 'numero_cuota'

    prestamo_id = fields.Many2one("loan.management.loan", "Numero de prestamo", readonly=True)
    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], related="prestamo_id.currency_id")
    afiliado_id = fields.Many2one("res.partner", "Cliente", required=True)
    fecha_pago = fields.Date("Fecha de Pago")
    monto_cuota = fields.Monetary("Monto de Cuota")
    capital = fields.Monetary("Capital")
    interes = fields.Monetary("Interes")
    mora = fields.Monetary("Mora")
    seguro = fields.Monetary("Seguro")
    saldo_prestamo = fields.Monetary("Saldo Pendiente")
    state = fields.Selection(
        [('cotizacion', 'Cotizacion'), ('cancelada', 'Cancelada'), ('novigente', 'No vigente'), ('vigente', 'Vigente'),
        ('morosa', 'Morosa'),('pagada', 'Pagada')], string='Estado de cuota', default='cotizacion')
    description = fields.Text("Notas Generales")
    numero_cuota = fields.Integer("# de cuota", readonly=True)
    saldo_pendiente = fields.Monetary("Saldo de Cuota")
    monto_pagado = fields.Monetary("Monto Pagado")

    @api.multi
    def action_pagar(self):
        self.write({'state': 'pagada'})

