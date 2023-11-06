# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import http
from odoo.http import request


class EcpayInvoiceController(http.Controller):

    @http.route('/payment/ecpay/save_invoice_type', type='json', methods=['POST'], auth="public")
    def save_invoice_type(self, **kwargs):
        order_id = request.session['sale_order_id']
        order = request.env['sale.order'].sudo().browse(order_id)

        res = {
            'ec_ident_name': '',
            'ec_ident': '',
            'ec_print': '',
            'ec_donate': '',
            'ec_donate_number': '',
            'ec_carrier_type': '',
            'ec_carrier_number': '',
        }

        invoice_type = kwargs.get('invoiceType')
        if type(invoice_type) is not int or not (-1 < invoice_type < 3):
            return False

        if invoice_type == 0:
            e_type = kwargs.get('e_type')

            if not type(e_type) is int and not (-1 < e_type < 4):
                return False

            res.update({
                'ec_carrier_type': str(e_type or ''),
                'ec_carrier_number': kwargs.get('CarrierNum', '') if e_type > 1 else '',
            })
        elif invoice_type == 1:
            address = kwargs.get('invoice_address')

            if not address:
                return False

            res.update({
                'ec_print': True,
                'ec_print_address': address,
            })

            if kwargs.get('ident_flag', False):
                res.update({
                    'ec_ident_name': kwargs.get('identifier_name', ''),
                    'ec_ident': kwargs.get('identifier', ''),
                })
        elif invoice_type == 2:
            love_code = kwargs.get('LoveCode')

            if not love_code:
                return False

            res.update({
                'ec_donate': True,
                'ec_donate_number': love_code,
            })

        order.write(res)
        return True
