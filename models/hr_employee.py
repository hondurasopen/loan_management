# -*- encoding: utf-8 -*-
from odoo import models, fields, api

class Recursoshumanos(models.Model):
    _inherit = "hr.employee"

    otherid = fields.Integer("Clave de empleado")
    aportaciones_ids = fields.One2many("loan.aportaciones", "empleado_id", "Aportaciones")
