# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class EcpayInvoiceSaleOrder(models.Model):
    _inherit = 'sale.order'

    ec_print = fields.Boolean(string="列印")
    ec_donate = fields.Boolean(string="捐贈")
    ec_donate_number = fields.Char(string="愛心碼")
    ec_print_address = fields.Char(string="發票寄送地址")
    ec_ident_name = fields.Char(string="發票抬頭")
    ec_ident = fields.Char(string="統一編號")
    ec_carrier_type = fields.Selection(string='載具類別',
                                       selection=[('1', '綠界科技電子發票載具'), ('2', '消費者自然人憑證'),
                                                  ('3', '消費者手機條碼')])
    ec_carrier_number = fields.Char(string="載具號碼")

    def _prepare_invoice(self):
        res = super(EcpayInvoiceSaleOrder, self)._prepare_invoice()

        res.update({
            'ecpay_CustomerIdentifier': self.ec_ident,
            'is_print': self.ec_print,
            'is_donation': self.ec_donate,
            'lovecode': self.ec_donate_number,
            'ec_print_address': self.ec_print_address,
            'ec_ident_name': self.ec_ident_name,
            'carrierType': self.ec_carrier_type,
            'carrierNum': self.ec_carrier_number,
        })

        return res
