from odoo import api, models
import time
from datetime import date, datetime
from dateutil.relativedelta import relativedelta


class reporte(models.AbstractModel):
    _name = 'report.loan_management.report_estado_prestamo'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('loan_management.report_prestamo_print')
        docargs = {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            }
        return report_obj.render("loan_management.report_prestamo_print",docargs)


