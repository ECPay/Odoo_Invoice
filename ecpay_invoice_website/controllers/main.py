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

        # 情況1：要列印發票
        if kwargs.get('print_flag'):
            # 情況2：要列印發票也要開立統編
            if kwargs.get('ident_flag'):
                res['ec_ident_name'] = kwargs['identifier_name']
                res['ec_ident'] = kwargs['identifier']
            res['ec_print_address'] = kwargs['invoice_address']
            res['ec_print'] = True
        # 情況3：要捐贈發票
        elif kwargs.get('donate_flag'):
            res['ec_donate'] = True
            res['ec_donate_number'] = kwargs['LoveCode']
        # 情況4：不列印也不捐贈，只使用載具
        elif not kwargs.get('print_flag') and not kwargs.get('donate_flag'):
            if kwargs['invoice_type'] == '0':
                res['ec_carrier_type'] = ''
            else:
                res['ec_carrier_type'] = kwargs['invoice_type']

            if kwargs['invoice_type'] == '2' or kwargs['invoice_type'] == '3':
                res['ec_carrier_number'] = kwargs['CarrierNum']
            else:
                res['ec_carrier_number'] = ''
        else:
            return 'error'

        if res:
            order.write(res)

        return '200'
