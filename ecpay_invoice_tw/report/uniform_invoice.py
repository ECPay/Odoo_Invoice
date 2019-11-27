
from odoo import models, fields, api
from odoo.exceptions import UserError

class ReportEcpayInvoice(models.AbstractModel):
    _name = 'report.ecpay_invoice_tw.invoice'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['account.move'].browse(docids)
        ecpay_invoice = []
        for line in docs:
            if line.uniform_state == 'invoiced':
                ecpay_invoice.append(line.ecpay_invoice_id.id)
            else:
                raise UserError('不能列印有未開或已作廢的電子發票!!')
        res = self.env['uniform.invoice'].browse(ecpay_invoice)
        seller_Identifier = self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.seller_Identifier')
        return {
            'doc_ids': res.ids,
            'doc_model': 'uniform.invoice',
            'docs': res,
            'seller_Identifier': seller_Identifier,
            'orderlines': docs.invoice_line_ids
        }
