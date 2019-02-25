from odoo import models, fields, api


class EcpayInvoiceSaleOrder(models.Model):
    _inherit = 'sale.order'

    ec_print = fields.Boolean(string="列印")
    ec_donate = fields.Boolean(string="捐贈")
    ec_donate_number = fields.Char(string="愛心碼")
    ec_print_address = fields.Char(string="發票寄送地址")
    ec_ident_name = fields.Char(string="發票抬頭")
    ec_ident = fields.Char(string="統一編號")
    ec_carruer_type = fields.Selection(string='載具類別', selection=[('1', '綠界科技電子發票載具'), ('2', '消費者自然人憑證'),
                                                                  ('3', '消費者手機條碼')])
    ec_carruer_number = fields.Char(string="載具號碼")

    @api.multi
    def _prepare_invoice(self):
        res = super(EcpayInvoiceSaleOrder, self)._prepare_invoice()

        res['ecpay_CustomerIdentifier'] = self.ec_ident
        res['is_print'] = self.ec_print
        res['is_donation'] = self.ec_donate
        res['lovecode'] = self.ec_donate_number
        res['ec_print_address'] = self.ec_print_address
        res['ec_ident_name'] = self.ec_ident_name
        res['carruerType'] = self.ec_carruer_type
        res['carruernum'] = self.ec_carruer_number

        return res