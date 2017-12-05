# -*- encoding: utf-8 -*-
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, exceptions, _
from datetime import date, datetime
from odoo.exceptions import Warning


class WizardPagoCuotas(models.TransientModel):
    _name = 'loan.wizard.payment'
    _inherit = ['mail.thread']
    _description = 'Asistente de Pagos'
    _rec_name = 'prestamo_id'

    def _get_prestamo(self):
        contexto = self._context
        if 'active_id' in contexto:
            loan_obj = self.env["loan.management.loan"].browse(contexto['active_id'])
            return loan_obj

    # Obtiene la cuota mas anterior mororsa
    def get_primeracuotamora(self, prestamo_id):
        obj_prestamo = self.env["loan.management.loan"].search([('id', '=', prestamo_id)])
        obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', prestamo_id), 
                        ('state', '=', 'morosa')])
        arreglo = []
        for valor in obj_cuota:
            arreglo.append(valor.numero_cuota)
        numero_cuota = (min(arreglo))
        saldo_pendiente = 0.0
        capital = 0.0
        monto_cuota = 0.0
        interes = 0.0
        mora = 0.0
        result = {}
        for cuota in obj_prestamo.cuota_ids:
            if numero_cuota == cuota.numero_cuota and cuota.state == 'morosa':
                numero_cuota = cuota.numero_cuota
                saldo_pendiente = cuota.saldo_pendiente
                capital = cuota.capital
                monto_cuota = cuota.monto_cuota
                mora = cuota.mora
                interes = cuota.interes
        result["numero_cuota"] = numero_cuota
        result["monto_cuota"] = monto_cuota
        result["saldo_pendiente"] = saldo_pendiente
        result["capital"] = capital
        result["mora"] = mora
        result["interes"] = interes
        return result

    # Obtiene primera  cuota normalmente usado para abono a capital
    def get_ultimacuota(self, prestamo_id):
        obj_prestamo = self.env["loan.management.loan"].search([('id', '=', prestamo_id)])
        numero_cuota = 0
        saldo_pendiente = 0
        capital = 0
        monto_cuota = 0
        result = {}
        for cuota in obj_prestamo.cuota_ids:
            if numero_cuota < cuota.numero_cuota and cuota.state == 'novigente' or cuota.state == 'vigente':
                numero_cuota = cuota.numero_cuota
                saldo_pendiente = cuota.saldo_pendiente
                capital = cuota.capital
                monto_cuota = cuota.monto_cuota
        result["numero_cuota"] = numero_cuota
        result["monto_cuota"] = monto_cuota
        result["saldo_pendiente"] = saldo_pendiente
        result["capital"] = capital
        return result

    def pagar_cuotasmorosas(self, pago_mora):
        monto_disponible = pago_mora
        capital = 0.0
        interes = 0.0
        mora = 0.0
        result = {}
        while monto_disponible > 0:
            cuota_morosa_dict = self.get_primeracuotamora(self.prestamo_id.id)
            obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
            ('numero_cuota', '=', cuota_morosa_dict["numero_cuota"])])
            saldo_cuota = obj_cuota.saldo_pendiente
            resta_monto = 0.0
            if round(monto_disponible, 10) > round(saldo_cuota, 10):
                obj_cuota.write({'state': 'pagada'})
                for cuota in self.cuotas_ids:
                    if cuota.numero_cuota == cuota_morosa_dict["numero_cuota"]:
                        cuota.write({'state': 'pagada'})
                        cuota.monto_pago = cuota.saldo_pendiente
                        cuota.saldo_pendiente = 0.0
                resta_monto = monto_disponible - saldo_cuota
                if obj_cuota.interes > obj_cuota.monto_pagado:
                    interes = interes + (obj_cuota.interes - obj_cuota.monto_pagado)
                    capital = capital + obj_cuota.capital
                else:
                    capital = capital + (obj_cuota.capital - (obj_cuota.monto_pagado - obj_cuota.interes))
                mora = mora + obj_cuota.mora
                obj_cuota.mora = 0.0
                obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
                obj_cuota.saldo_pendiente = 0

            elif round(monto_disponible, 10) < round(saldo_cuota, 10):
                if obj_cuota.interes > obj_cuota.monto_pagado:
                    if monto_disponible > obj_cuota.interes:
                        interes = interes + (obj_cuota.interes - obj_cuota.monto_pagado)
                        disponible = monto_disponible - obj_cuota.interes
                        if round(disponible, 10) > round(obj_cuota.mora, 10) and obj_cuota.mora > 0.0:
                            mora = mora + obj_cuota.mora
                            disponible = disponible - obj_cuota.mora
                            capital = capital + disponible
                            obj_cuota.mora = 0.0
                        else:
                            mora = mora + disponible
                            obj_cuota.mora = obj_cuota.mora - disponible
                    else:
                        interes = monto_disponible
                else:
                    if obj_cuota.mora > 0.0:
                        if monto_disponible > obj_cuota.mora:
                            mora = mora + obj_cuota.mora
                            capital = monto_disponible - obj_cuota.mora
                            obj_cuota.mora = 0.0
                        else:
                            mora = monto_disponible
                            obj_cuota.mora = obj_cuota.mora - monto_disponible
                    else:
                        capital = capital + monto_disponible

                resta_monto = 0
                obj_cuota.monto_pagado += monto_disponible
                obj_cuota.saldo_pendiente = obj_cuota.saldo_pendiente - monto_disponible
                for cuota in self.cuotas_ids:
                    if cuota.numero_cuota == cuota_morosa_dict["numero_cuota"]:
                        cuota.saldo_pendiente = cuota.saldo_pendiente - monto_disponible
                        cuota.monto_pago = monto_disponible
            else:
                if obj_cuota.interes > obj_cuota.monto_pagado:
                    interes = interes + (obj_cuota.interes - obj_cuota.monto_pagado)
                    disponible = monto_disponible - obj_cuota.interes
                    if round(disponible, 10) > round(obj_cuota.mora, 10) and obj_cuota.mora > 0.0:
                        mora = mora + obj_cuota.mora
                        disponible = disponible - obj_cuota.mora
                        capital = capital + disponible
                        obj_cuota.mora = 0.0
                    else:
                        mora = mora + disponible
                        obj_cuota.mora = obj_cuota.mora - disponible
                else:
                    mora = mora + obj_cuota.mora
                    capital = capital + (monto_disponible - obj_cuota.mora)

                obj_cuota.write({'state': 'pagada'})
                obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
                resta_monto = 0.0
                for cuota in self.cuotas_ids:
                    if cuota.numero_cuota == cuota_morosa_dict["numero_cuota"]:
                        cuota.write({'state': 'pagada'})
                        cuota.monto_pago = obj_cuota.saldo_pendiente
                        cuota.saldo_pendiente = 0.0
                        resta_monto = 0
                obj_cuota.mora = 0.0
                obj_cuota.saldo_pendiente = 0.0

            monto_disponible = resta_monto
        result["capital"] = capital
        result["interes"] = interes
        result["mora"] = mora
        return result

    def abono_cuotasvigentes(self, monto):
        pago = round(monto, 2)
        monto_vigente = round(self.monto_vigente, 2)
        capital = 0.0
        interes = 0.0
        result = {}
        if pago == monto_vigente:
            obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', self.numero_cuota)])
            obj_cuota.write({'state': 'pagada'})
            obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
            obj_cuota.saldo_pendiente = 0.0
            for cuota in self.cuotas_ids:
                if cuota.state == 'vigente' and cuota.numero_cuota == obj_cuota.numero_cuota:
                    cuota.monto_pago += cuota.saldo_pendiente
                    cuota.saldo_pendiente = 0
                    cuota.write({'state': 'pagada'})
            capital = obj_cuota.capital
            interes = obj_cuota.interes
        if pago < monto_vigente and pago > 0.0:
            obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', self.numero_cuota)])
            obj_cuota.monto_pagado += pago
            obj_cuota.saldo_pendiente = obj_cuota.saldo_pendiente - pago
            for cuota in self.cuotas_ids:
                if cuota.state == 'vigente' and cuota.numero_cuota == obj_cuota.numero_cuota:
                    cuota.saldo_pendiente = cuota.saldo_pendiente - pago
                    cuota.monto_pago = pago
            if obj_cuota.interes > obj_cuota.monto_pagado:
                interes_restante = obj_cuota.interes - obj_cuota.monto_pagado
                if pago > interes_restante:
                    interes = interes_restante
                    capital = obj_cuota.capital - interes
                else:
                    interes = pago
            else:
                capital = pago

        result["capital"] = capital
        result["interes"] = interes
        return result

    def abono_capital(self, monto):
        # cuota_prestamo = round(self.prestamo_id.cuato_prestamo, 2)
        monto_disponible = round(monto, 2)
        while monto_disponible > 0:
            cuota_dict = self.get_ultimacuota(self.prestamo_id.id)
            # capital_cuota = round(cuota_dict["capital"], 2)
            obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                ('numero_cuota', '=', cuota_dict["numero_cuota"])])
            saldo_cuota = round(cuota_dict["saldo_pendiente"], 2)
            cuota = round(cuota_dict["monto_cuota"], 2)
            capital_cuota = round(cuota_dict["capital"], 2)
            obj_cuota_payment = self.env["loan.wizard.payment.lines"]
            #resta_monto = 0
            vals = {
                'numero_cuota': obj_cuota.numero_cuota,
                'pago_cuota_id': self.id,
                'fecha_pago': obj_cuota.fecha_pago,
                'monto_cuota': obj_cuota.monto_cuota,
                'mora': obj_cuota.mora,
            }
            if monto_disponible > capital_cuota:
                obj_cuota.write({'state': 'pagada'})
                obj_cuota.monto_pagado = capital_cuota
                vals["saldo_pendiente"] = 0
                vals["monto_pago"] = capital_cuota
                vals["state"] = obj_cuota.state
                obj_cuota.saldo_pendiente = 0

            if monto_disponible < capital_cuota:
                obj_cuota.saldo_pendiente = obj_cuota.saldo_pendiente - monto_disponible
                obj_cuota.monto_pagado += monto_disponible
                vals["saldo_pendiente"] = obj_cuota.saldo_pendiente
                vals["monto_pago"] = monto_disponible
                vals["state"] = obj_cuota.state

            if monto_disponible == capital_cuota:
                obj_cuota.saldo_pendiente = 0
                obj_cuota.monto_pagado += obj_cuota.capital
                obj_cuota.write({'state': 'pagada'})
                vals["saldo_pendiente"] = obj_cuota.saldo_pendiente
                vals["monto_pago"] = obj_cuota.capital
                vals["state"] = obj_cuota.state

            id_cuota = obj_cuota_payment.create(vals)
            monto_disponible = monto_disponible - vals["monto_pago"]

    def fct_crearpago_prestamo(self, mensaje, move_id):
        # No posteando el abono a capítal
        obj_pago = self.env["loan.pagos"]
        values = {
            'cliente_id': self.prestamo_id.afiliado_id.id,
            'fecha': self.date_payment,
            'prestamo_id': self.prestamo_id.id,
            'importe_pagado': self.monto,
            'state': 'done',
            'observaciones': mensaje,
            'name': self.name,
        }
        pago_id = obj_pago.create(values)
        if self.cuotas_ids and pago_id:
            dict_cuotas = []
            for cuota in self.cuotas_ids:
                obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', cuota.numero_cuota)])
                if cuota.monto_pago > 0.0:
                    dict_cuotas.append(obj_cuota.id)
                    valores_pago_cuota = {
                        'cuota_id': obj_cuota.id,
                        'pago_id': pago_id.id,
                        'importe_pago_cuota': cuota.monto_pago,
                        'fecha_pago': self.date_payment,
                    }
                    obj_cuota_pago = self.env["loan.management.loan.cuota.pago"]
                    cuota_line_pago = obj_cuota_pago.create(valores_pago_cuota)
                    #obj_cuota.write({'pagos_ids': [(0, 0, valores_pago_cuota)]})
            pago_id.write({'cuotas': [(6, 0, dict_cuotas)]})
            if move_id:
                pago_id.write({'asiento_id': move_id})

    @api.one
    def set_pagos(self):
        if self.monto > 0:
            if not self.has_revision_saldo:
                raise Warning(_('Primero genere la revisión de saldos, para poder realizar pagos'))

            saldo_pago = round(self.saldo_pago, 2)
            # Primera condición monto a pagar es igual a saldo actual
            if self.monto == saldo_pago:
                # Primera condición saldo en mora y sin cuotas vigentes
                if self.saldo_mora == 0.0 and self.monto_vigente > 0:
                    #obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        #('numero_cuota', '=', self.numero_cuota)])
                    move_id = False
                    for cuota in self.cuotas_ids:
                        obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', cuota.numero_cuota)])
                        cuota.monto_pago = cuota.saldo_pendiente
                        cuota.saldo_pendiente = 0.0
                        cuota.write({'state': 'pagada'})
                        obj_cuota.write({'state': 'pagada'})
                        obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
                        if obj_cuota.monto_cuota > obj_cuota.saldo_pendiente:
                            interes_pagados = obj_cuota.monto_cuota - obj_cuota.saldo_pendiente
                            capital = 0.0
                            interes = 0.0
                            if obj_cuota.interes > interes_pagados:
                                interes = obj_cuota.interes - interes_pagados
                                if self.monto > interes:
                                    capital = self.monto - interes
                                else:
                                    interes = self.monto
                            else:
                                capital = self.monto
                            move_id = self.generar_partida_contable(capital, interes, 0.0, obj_cuota.saldo_pendiente )
                        else:
                            move_id = self.generar_partida_contable(obj_cuota.capital, obj_cuota.interes, 0.0, obj_cuota.saldo_pendiente )
                        obj_cuota.saldo_pendiente = 0.0
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)
                # Segunda condición  monto vigente  y saldo de mora mayor que cero
                if self.saldo_mora > 0.0 and self.monto_vigente == 0.0:
                    monto_pagar = self.monto
                    interes = 0.0
                    capital = 0.0
                    mora = 0.0
                    for cuota in self.cuotas_ids:
                        obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', cuota.numero_cuota)])
                        if obj_cuota.monto_cuota > obj_cuota.saldo_pendiente:
                            if obj_cuota.interes > obj_cuota.monto_pagado:
                                interes = obj_cuota.interes - obj_cuota.monto_pagado
                                mora = mora + (obj_cuota.mora)
                                capital = capital + (obj_cuota.capital)
                            else:
                                mora = mora + obj_cuota.mora
                                capital = capital + (obj_cuota.saldo_pendiente - obj_cuota.mora)
                        else:
                            interes = interes + (obj_cuota.interes - obj_cuota.monto_pagado)
                            capital = capital + obj_cuota.capital
                            mora = mora + obj_cuota.mora
                        obj_cuota.write({'state': 'pagada'})
                        obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
                        obj_cuota.saldo_pendiente = 0.0
                        cuota.monto_pago = cuota.saldo_pendiente
                        cuota.saldo_pendiente = 0.0
                        obj_cuota.mora = 0.0
                        cuota.write({'state': 'pagada'})
                    move_id = self.generar_partida_contable(capital, interes, mora, self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

                if self.saldo_mora > 0.0 and self.monto_vigente > 0.0:
                    interes = 0.0
                    capital = 0.0
                    mora = 0.0
                    for cuota in self.cuotas_ids:
                        obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', cuota.numero_cuota)])
                        if obj_cuota.monto_cuota > obj_cuota.saldo_pendiente:
                            if obj_cuota.interes > obj_cuota.monto_pagado:
                                interes = obj_cuota.interes - obj_cuota.monto_pagado
                                mora = mora + (obj_cuota.mora)
                                capital = capital + (obj_cuota.capital)
                            else:
                                mora = mora + obj_cuota.mora
                                capital = capital + (obj_cuota.saldo_pendiente - obj_cuota.mora)
                        else:
                            interes = interes + (obj_cuota.interes - obj_cuota.monto_pagado)
                            capital = capital + obj_cuota.capital
                            mora = mora + obj_cuota.mora
                        cuota.monto_pago = cuota.saldo_pendiente
                        cuota.saldo_pendiente = 0.0
                        cuota.write({'state': 'pagada'})
                        obj_cuota.write({'state': 'pagada'})
                        obj_cuota.monto_pagado += obj_cuota.saldo_pendiente
                        obj_cuota.saldo_pendiente = 0.0
                        obj_cuota.mora = 0.0
                    move_id = self.generar_partida_contable(capital, interes, mora, self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

            # Segunda Condición grande de monto a pagar es menor que el saldo
            if self.monto < saldo_pago:
                if self.saldo_mora == 0.0 and self.monto_vigente > 0:
                    obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', self.numero_cuota)])
                    # Primero se paga interes despues se paga capital
                    move_id = False
                    capital = 0.0
                    interes = 0.0
                    if obj_cuota.monto_cuota > obj_cuota.saldo_pendiente:
                        interes_pagados = obj_cuota.monto_cuota - obj_cuota.saldo_pendiente
                        if obj_cuota.interes > interes_pagados:
                            interes = obj_cuota.interes - interes_pagados
                            if self.monto > interes:
                                capital = self.monto - interes
                            else:
                                interes = self.monto
                        else:
                            capital = self.monto
                    else:
                        if self.monto > obj_cuota.interes:
                            interes = obj_cuota.interes
                            capital = self.monto - interes
                        else:
                            interes = self.monto

                    move_id = self.generar_partida_contable(capital, interes, 0.0, self.monto)
                    for cuota in self.cuotas_ids:
                        cuota.saldo_pendiente = cuota.saldo_pendiente - self.monto
                        cuota.monto_pago = self.monto
                    obj_cuota.saldo_pendiente = obj_cuota.saldo_pendiente - self.monto
                    obj_cuota.monto_pagado += self.monto

                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

                if self.saldo_mora > 0.0 and self.monto_vigente == 0.0:
                    cuota_dict = self.pagar_cuotasmorosas(self.monto)
                    move_id = self.generar_partida_contable(cuota_dict["capital"], cuota_dict["interes"], cuota_dict["mora"], self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

                if self.saldo_mora > 0.0 and self.monto_vigente > 0.0:
                    monto_disponible = self.monto
                    saldo_mora = round(self.saldo_mora, 2)
                    dict_values = {}
                    values = {}
                    if monto_disponible > saldo_mora:
                        valor = monto_disponible - saldo_mora
                        dict_values = self.pagar_cuotasmorosas(self.saldo_mora)
                        values = self.abono_cuotasvigentes(valor)
                        dict_values["capital"] = dict_values["capital"] + values["capital"]
                        dict_values["interes"] = dict_values["interes"] + values["interes"]
                    else:
                        dict_values = self.pagar_cuotasmorosas(monto_disponible)
                    move_id = self.generar_partida_contable(round(dict_values["capital"], 2), round(dict_values["interes"], 2), dict_values["mora"], self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

            # Tercer caso monto a pagar es mayor que saldo por tanto se abonara a capital
            if self.monto > saldo_pago and saldo_pago != 0.0:
                raise Warning(_('El Monto a pagar es mayor que el saldo adeudado, primero realice el pago del saldo y luego realice un abono a capital'))

                if self.saldo_mora == 0.0 and self.monto_vigente > 0:
                    obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                        ('numero_cuota', '=', self.numero_cuota)])
                    values = self.abono_cuotasvigentes(self.monto_vigente)
                    abono = (self.monto - self.monto_vigente)
                    values["capital"] = values["capital"] + abono
                    self.abono_capital(abono)
                    move_id = self.generar_partida_contable(round(values["capital"], 2), round(values["interes"], 2), 0.0, self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

                if self.saldo_mora > 0.0 and self.monto_vigente == 0.0:
                    values = self.pagar_cuotasmorosas(self.saldo_mora)
                    abono = (self.monto - self.saldo_mora)
                    values["capital"] = values["capital"] + abono
                    self.abono_capital(abono)
                    move_id = self.generar_partida_contable(round(values["capital"], 2), round(values["interes"], 2), 0.0, self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

                if self.saldo_mora > 0.0 and self.monto_vigente > 0.0:
                    values = self.pagar_cuotasmorosas(self.saldo_mora)
                    vals = self.abono_cuotasvigentes(self.monto_vigente)
                    abono = (self.monto - self.saldo_mora - self.monto_vigente)
                    values["capital"] = values["capital"] + vals["capital"] + abono
                    values["interes"] = values["interes"] + vals["interes"]
                    self.abono_capital(abono)
                    move_id = self.generar_partida_contable(values["capital"], values["interes"], 0.0, self.monto)
                    if move_id:
                        self.fct_crearpago_prestamo("Pago de cuota(s)", move_id)

            # Abono a capital sin mora y sin cuotas vigentes
            if self.saldo_pago == 0.0 and self.monto_vigente == 0.0:
                # cuota_prestamo = round(self.prestamo_id.cuato_prestamo, 2)
                #capital = self.capital_prestamo()

                if self.monto > self.prestamo_id.total_capital:
                    raise Warning(_('Esta tratando de pagar mas del correspondiente del capital del prestamo actual'))
                self.abono_capital(self.monto)
                move_id = self.generar_partida_contable(self.monto, 0.0, 0.0, self.monto)
                if move_id:
                    self.fct_crearpago_prestamo("Abono a Capital", move_id)


            if self.record_aportaciones:
                if self.monto_aportacion > 0:
                    obj_aportaciones = self.env["loan.aportaciones"]
                    values = {
                        'cliente_id': self.prestamo_id.afiliado_id.id,
                        'fecha': self.date_payment,
                        'monto_aportacion': self.monto_aportacion,
                        'state': 'draft',
                        'journal_id': self.journal_id.id,
                        'tipo_aportacion': 'aportacion',
                    }
                    aport_id = obj_aportaciones.create(values)
                    if aport_id:
                        aport_id.action_ingresar()
                        self.write({'aport_id': aport_id.id})
                if self.monto_ahorro > 0:
                    obj_aportaciones_ahorro = self.env["loan.aportaciones"]
                    values_ahorro = {
                        'cliente_id': self.prestamo_id.afiliado_id.id,
                        'fecha': self.date_payment,
                        'monto_aportacion': self.monto_ahorro,
                        'state': 'draft',
                        'journal_id': self.journal_id.id,
                        'tipo_aportacion': 'ahorro',
                    }
                    ahorro_id = obj_aportaciones_ahorro.create(values_ahorro)
                    if ahorro_id:
                        ahorro_id.action_ingresar()
                        self.write({'ahorro_id': ahorro_id.id})
            # Cambiar de estado
            self.write({'state': 'pagada'})
        else:
            raise Warning(_('El monto a pagar debe de ser mayor que cero'))

    def capital_prestamo(self):
        capital = 0.0
        for prestamo in self.prestamo_id:
            for cuota in prestamo.cuota_ids:
                if cuota.state == 'novigente':
                    capital += cuota.capital
        return capital

    def generar_partida_contable(self, capital, interes, mora, monto):
        account_move = self.env['account.move']
        lineas = []
        # print "/" * 100
        # print round(mora, 10)
        # print round(capital, 10)
        # print round(interes, 10)
        # print round(monto, 10)
        monto_pago = round(mora, 10) + round(capital, 10) + round(interes, 10)
        # print monto_pago
        # print "/" * 100
        if mora > 0.0:
            vals_mora = {
                'debit': 0.0,
                'credit': mora,
                'amount_currency': 0.0,
                'name': 'Pago de Mora',
                'account_id': self.prestamo_id.tipo_prestamo_id.cuenta_intereses_mora.id,
                'partner_id': self.prestamo_id.afiliado_id.id,
                'date': self.date_payment,
            }
            lineas.append((0, 0, vals_mora))

        if capital > 0.0:
            vals_capital = {
                'debit': 0.0,
                'credit': capital,
                'amount_currency': 0.0,
                'name': 'Pago de Capital',
                'account_id': self.prestamo_id.afiliado_id.property_account_receivable_id.id,
                'partner_id': self.prestamo_id.afiliado_id.id,
                'date': self.date_payment,
            }
            lineas.append((0, 0, vals_capital))

        if interes > 0.0:
            vals_interes = {
                'debit': 0.0,
                'credit': interes,
                'amount_currency': 0.0,
                'name': 'Pago de intereses',
                'account_id': self.prestamo_id.tipo_prestamo_id.cuenta_intereses.id,
                'partner_id': self.prestamo_id.afiliado_id.id,
                'date': self.date_payment,
            }
            lineas.append((0, 0, vals_interes))

        if monto > 0.0:
            vals_banco = {
                'debit': monto_pago,
                'credit': 0.0,
                'amount_currency': 0.0,
                'name': 'Pago de prestamo',
                'account_id': self.journal_id.default_debit_account_id.id,
                'partner_id': self.prestamo_id.afiliado_id.id,
                'date': self.date_payment,
            }
            lineas.append((0, 0, vals_banco))

        values = {
            'journal_id': self.journal_id.id,
            'date': self.date_payment,
            'ref': 'Pago de prestamo' + ' ' + self.prestamo_id.name,
            'line_ids': lineas,
        }
        id_move = account_move.create(values)
        return id_move.id

    @api.one
    def generarsaldos(self):
        if self.prestamo_id:
            if self.cuotas_ids:
                for fee in self.cuotas_ids:
                    fee.unlink()
            obj_cuota_payment = self.env["loan.wizard.payment.lines"]
            saldo = 0
            for cuota in self.prestamo_id.cuota_ids:
                if cuota.state == 'vigente' or cuota.state == 'morosa':
                    vals = {
                        'numero_cuota': cuota.numero_cuota,
                        'pago_cuota_id': self.id,
                        'fecha_pago': cuota.fecha_pago,
                        'monto_cuota': cuota.monto_cuota,
                        'mora': cuota.mora,
                        'interes': cuota.interes,
                        'capital': cuota.capital,
                        'saldo_pendiente': cuota.saldo_pendiente,
                        'state': cuota.state,
                    }
                    id_cuota = obj_cuota_payment.create(vals)
                    saldo += cuota.saldo_pendiente
            self.write({'state': 'saldo'})
            self.has_revision_saldo = True
            #self.monto = saldo

    @api.one
    def liquidar_prestamo(self):
        if self.saldo_pago > 0.0 :
            raise Warning(_('El prestamo no debe tener cuota(s) vigente(s) o cuota(s) morosa(s) para liquidar el saldo de capital del préstamo'))

        if round(self.monto, 2) == round(self.capital_prestamo, 2):
            lista = self.l_prestamo()
            move_id = self.generar_partida_contable(self.monto, 0.0, 0.0, self.monto)
            if move_id:
                obj_pago = self.env["loan.pagos"]
                values = {
                    'cliente_id': self.prestamo_id.afiliado_id.id,
                    'fecha': self.date_payment,
                    'prestamo_id': self.prestamo_id.id,
                    'importe_pagado': self.monto,
                    'state': 'done',
                    'observaciones': 'Abono a capital y liquidación de préstamo',
                }
                pago_id = obj_pago.create(values)
                if pago_id:
                    dict_cuotas = []
                    for arreglo in lista:
                        obj_cuota = self.env["loan.management.loan.cuota"].search([('prestamo_id', '=', self.prestamo_id.id), 
                                ('numero_cuota', '=', arreglo)])
                        if obj_cuota:
                            dict_cuotas.append(obj_cuota.id)
                    pago_id.write({'cuotas': [(6, 0, dict_cuotas)]})
                    if move_id:
                        pago_id.write({'asiento_id': move_id})
            self.write({'state': 'pagada'})

        else: 
            raise Warning(_('El monto a pagar no es igual a saldo de total de capital del prestamo'))

    def l_prestamo(self):
        if self.prestamo_id:
            lineas = []
            for cuota in self.prestamo_id.cuota_ids:
                if not  cuota.state == 'pagada':
                    cuota.monto_pagado = cuota.capital
                    cuota.saldo_pendiente = 0.0
                    cuota.state = 'pagada'
                    cuota.description = 'Préstamo pagado con abono a capital'
                    lineas.append(cuota.numero_cuota)

            self.prestamo_id.saldo_pendiente = 0.0
            self.prestamo_id.write({'state': 'liquidado'})
            return lineas

    def _get_values(self):
        if self.cuotas_ids:
            for fee in self.cuotas_ids:
                if fee.state == 'vigente':
                    self.monto_vigente = self.monto_vigente + fee.saldo_pendiente
                    self.numero_cuota = fee.numero_cuota
                if fee.state == 'morosa':
                    self.saldo_mora = self.saldo_mora + fee.saldo_pendiente
                    #self.write({'cuotas_mora_num': [(4, fee.id, None)]})
            self.saldo_pago = self.monto_vigente + self.saldo_mora

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    def _get_total(self):
        self.total_transaction = self.monto + self.monto_aportacion + self.monto_ahorro

    @api.onchange("monto_aportacion", "monto_ahorro")
    @api.depends("monto", "monto_aportacion", "monto_ahorro")
    def onchange_aportacion(self):
        self._get_total()


    name = fields.Char("No. Pago", required=True, readonly= True,default=lambda self: self.env['ir.sequence'].get('pago'))
    liquidar_capital = fields.Boolean("Liquidar Préstamo")
    capital_prestamo = fields.Float("Capital de Prestamo", readonly=True, related="prestamo_id.total_capital")
    saldo_pendiente_prestamo = fields.Float("Saldo de Préstamo", readonly=True, related="prestamo_id.saldo_pendiente")
    # Información General
    date_payment = fields.Date(string="Fecha de Pago", required=True, default=fields.Date.today)
    prestamo_id = fields.Many2one("loan.management.loan", "Prestamo", default=_get_prestamo)
    monto = fields.Float("Pago de prestamo", required=True)
    saldo_pago = fields.Monetary("Saldo Pendiente", compute=_get_values)
    has_revision_saldo = fields.Boolean("Revision de Saldos")
    # Mora de Prestamo
    saldo_mora = fields.Monetary("Saldo en Mora", compute=_get_values)
    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], default=get_currency)
    # cuotas_mora_num = fields.Many2many("loan.management.loan.cuota", string="Cuotas en Mora")
    # Cuota Vigente
    monto_vigente = fields.Monetary("Monto Vigente", compute=_get_values)
    numero_cuota = fields.Integer("Cuota Vigente #", compute=_get_values)
    # Cuotas
    cuotas_ids = fields.One2many("loan.wizard.payment.lines", "pago_cuota_id", "Cuotas a pagar")
    existe_cuota_morosa = fields.Boolean("Cuotas en Mora")
    state = fields.Selection([('borrador', 'Borrador'), ('cancelada', 'Cancelado'), ('saldo', 'Revisión de Saldo'),('pagada', 'Pagada')], 
        readonly=True, string='Estado del Pago', default='borrador')
    notas = fields.Text("Observaciones")
    journal_id = fields.Many2one("account.journal", "Metodo de pago", required=True, domain=[('type', 'in', ['bank', 'cash'])])
    # Generar aportaciones
    record_aportaciones = fields.Boolean("Registro de Aportación")
    monto_aportacion = fields.Float("Monto de aportación")
    monto_ahorro = fields.Float("Monto de ahorro")
    ahorro_id = fields.Many2one("loan.aportaciones", "Ahorro de cliente", readonly=True)
    aport_id = fields.Many2one("loan.aportaciones", "Aportación de cliente", readonly=True)
    total_transaction = fields.Monetary("Total de transacción", compute=_get_total)

    @api.multi
    def set_borrador(self):
        self.write({'state': 'borrador'})

    @api.multi
    def set_cancelar(self):
        self.write({'state': 'cancelada'})


class WizardPagoCuotasLines(models.TransientModel):
    _name = 'loan.wizard.payment.lines'

    pago_cuota_id = fields.Many2one("loan.wizard.payment", "Pago")
    currency_id = fields.Many2one("res.currency", "Moneda", related="pago_cuota_id.currency_id")
    fecha_pago = fields.Date("Fecha de Pago")
    monto_cuota = fields.Monetary("Cuota")
    interes = fields.Monetary("Interes")
    capital = fields.Monetary("Capital")
    saldo_pendiente = fields.Monetary("Saldo de Pendiente")
    state = fields.Selection([('cotizacion', 'Cotizacion'), ('cancelada', 'Cancelada'), ('novigente', 'No vigente'), ('vigente', 'Vigente'),('morosa', 'Morosa'),('pagada', 'Pagada')], 
        readonly=True, string='Estado de cuota', default='cotizacion')
    description = fields.Text("Notas Generales")
    numero_cuota = fields.Integer("# de cuota", readonly=True)
    monto_pago = fields.Monetary("Monto Pagado")
    mora = fields.Monetary("Mora")

    reversar_interes = fields.Monetary("Interes a reversar")
    reversar_mora = fields.Monetary("Mora a reversar")

    @api.one
    def update_saldo(self):
        if self.reversar_interes < 0 or self.reversar_mora < 0:
            raise Warning(_('Los montos de interes a reversar deben ser mayores que cero '))

        if not self.reversar_interes > self.interes:
            self.saldo_pendiente = self.saldo_pendiente - self.reversar_interes

        if not self.reversar_mora > self.mora:
            self.saldo_pendiente = self.saldo_pendiente - self.reversar_mora

