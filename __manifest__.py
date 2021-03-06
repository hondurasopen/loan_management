# -*- encoding: utf-8 -*-
##############################################################################

{
    "name": "Loan Management",
    "depends": [
        "base",
        "account",
        "product",
    ],
    "author": "Cesar Alejandro Rodriguez, Odoo Honduras",
    "category": "Sale",
    "description": """Loan Management """,
    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        "wizard/wizard_generate_detail.xml",
        "views/loan_management_menu.xml",
        "views/loan_type_view.xml",
        "views/loan_plazo_view.xml",
        "views/loan_interes_view.xml",
        "views/loan_view .xml",
        "views/loan_cuota_view.xml",
        "views/loan_docs_view.xml",
        "views/contracto_sale_sequence.xml",
        "views/aportacion_view.xml",
        "views/aportaciones.xml",
        "views/cliente_view.xml",
        "wizard/wizard_status_cuotas_view.xml",
        "views/mora_view.xml",
        "views/tipo_gasto_view.xml",
        "views/retiros_view.xml",
        "views/reporte_cobros_view.xml",
        "reports/report_prestamo.xml",
        "reports/report_prestamo_view.xml",
        "reports/report_boleta.xml",
        "reports/report_boleta_pago_view.xml",
        "reports/report_retiro.xml",
        "reports/report_retiro_view.xml",
        "reports/report_aportacion.xml",
        "reports/report_aportacion.xml",
        "reports/report_aportaciones_view.xml",
        "reports/report_wizard_forecast.xml",
        "reports/report_wizard_forecast_view.xml",
        "reports/report_boleta_aportaciones.xml",
        "reports/report_boleta_aportaciones_view.xml",
    ],
    'demo': [],
    'installable': True,
}
