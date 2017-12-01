# -*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Retiros(models.Model):
    _name = "loan.retiros"
    _order = 'fecha asc'
    _inherit = ['mail.thread']

    def get_currency(self):
        return self.env.user.company_id.currency_id.id

    def get_saldo(self):
        if self.cliente_id:
            if self.cliente_id.saldo_cliente <= 0:
                raise Warning(_('El afiliado no cuenta con fondos para realizar el retiro'))
            self.total_disponible = self.cliente_id.saldo_cliente

    @api.onchange("cliente_id")
    def onchange_saldo(self):
        self.get_saldo()

    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)], default=get_currency)
    name = fields.Char("Número de retiro", default=lambda self: self.env['ir.sequence'].get('retiros'), states={'draft': [('readonly', False)]})
    cliente_id = fields.Many2one("res.partner", "Cliente", required=True, states={'draft': [('readonly', False)]})
    fecha = fields.Date("Fecha de retiro", required=True, states={'draft': [('readonly', False)]})
    monto_retiro = fields.Float("Monto de retiro", required=True, states={'draft': [('readonly', False)]})
    observaciones = fields.Text("Notas Generales")
    state = fields.Selection([
            ('draft','Borrador'),
            ('cancel','Cancelada'),
            ('done','Realizado'),
        ], string='Estado', index=True, default='draft')
    move_id = fields.Many2one('account.move', 'Asiento Contable', ondelete='restrict', readonly=True)
    journal_id = fields.Many2one("account.journal", "Metodo de pago", required=True, domain=[('type', 'in', ['bank', 'cash'])])
    total_disponible = fields.Float("Total disponible", compute=get_saldo)

    @api.multi
    def action_ingresar(self):
        if self.monto_retiro <= 0:
            raise Warning(_('El monto de retiro debe de ser mayor que cero'))

        if self.cliente_id.saldo_cliente <= 0:
            raise Warning(_('El afiliado no cuenta con fondos disponibles para realizar el retiro'))

        if self.monto_retiro > self.total_disponible:
            raise Warning(_('No cuenta el cliente con suficientes fondos para realizar el retiro'))

        self.write({'move_id': self.generar_partida_contable()})
        self.write({'state': 'done'})

    def generar_partida_contable(self):
        lineas = []
        account_move = self.env['account.move']
        vals_debit = {
            'debit': self.monto_retiro,
            'credit': 0.0,
            'amount_currency': 0.0,
            'name': 'Retiro de cliente',
            'account_id': self.cliente_id.property_account_payable_id.id,
            'partner_id': self.cliente_id.id,
            'date': self.fecha,
        }

        vals_credit = {
            'debit': 0.0,
            'credit': self.monto_retiro,
            'amount_currency': 0.0,
            'name': 'Aportación de cliente',
            'account_id': self.journal_id.default_credit_account_id.id,
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
