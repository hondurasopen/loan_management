# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Aportaciones(models.Model):
    _name = "loan.aportaciones"
    _order = 'fecha asc'
    _inherit = ['mail.thread']

    name = fields.Char("Número de aportación", default=lambda self: self.env['ir.sequence'].get('ahorro'), states={'draft': [('readonly', False)]})
    cliente_id = fields.Many2one("res.partner", "Cliente", required=True, states={'draft': [('readonly', False)]})
    fecha = fields.Date("Fecha de aportación", required=True, states={'draft': [('readonly', False)]})
    monto_aportacion = fields.Float("Monto de aportación", required=True, states={'draft': [('readonly', False)]})
    observaciones = fields.Text("Notas Generales")
    state = fields.Selection([
            ('draft','Borrador'),
            ('cancel','Cancelada'),
            ('done','Ingresada'),
        ], string='Estado', index=True, default='draft')
    move_id = fields.Many2one('account.move', 'Asiento Contable', ondelete='restrict', readonly=True)
    journal_id = fields.Many2one("account.journal", "Metodo de pago", required=True, domain=[('type', 'in', ['bank', 'cash'])])
    tipo_aportacion = fields.Selection([('aportacion', 'Aportación'), ('ahorro', 'Ahorro')], 
        string='Tipo', required=True, index=True, default='aportacion')

    @api.multi
    def action_ingresar(self):
        if self.monto_aportacion <= 0:
            raise Warning(_('El monto del ahorro debe de ser mayor que cero'))
        self.write({'move_id': self.generar_partida_contable()})
        self.write({'state': 'done'})

    def generar_partida_contable(self):
        lineas = []
        account_move = self.env['account.move']
        vals_debit = {
            'debit': 0.0,
            'credit': self.monto_aportacion,
            'amount_currency': 0.0,
            'name': 'Aportación de cliente',
            'account_id': self.cliente_id.property_account_payable_id.id,
            'partner_id': self.cliente_id.id,
            'date': self.fecha,
        }

        vals_credit = {
            'debit': self.monto_aportacion,
            'credit': 0.0,
            'amount_currency': 0.0,
            'name': 'Aportación de cliente',
            'account_id': self.journal_id.default_debit_account_id.id,
            'partner_id': self.cliente_id.id,
            'date': self.fecha,
        }
        lineas.append((0, 0, vals_debit))
        lineas.append((0, 0, vals_credit))
        aport = self.name
        values = {
            'journal_id': self.journal_id.id,
            'date': self.fecha,
            'ref': 'Aportación de cliente',
            'line_ids': lineas,
            'partner_id': self.cliente_id.id,
        }
        id_move = account_move.create(values)
        return id_move.id
