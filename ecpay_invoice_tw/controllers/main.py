
from odoo import http
from odoo.http import request


class EcpayInvoiceController(http.Controller):

    @http.route('/payment/ecpay/save_invoice_type', type='json', methods=['POST'], auth="public")
    def save_invoice_type(self, **kwargs):
        order_id = request.session['sale_order_id']
        order = request.env['sale.order'].sudo().browse(order_id)

        res = {}
        # 情況1：要列印發票
        if kwargs['print_flag'] is True:
            # 情況2：要列印發票也要開立統編
            if kwargs['ident_flag'] is True:
                res['ec_ident_name'] = kwargs['identifier_name']
                res['ec_ident'] = kwargs['identifier']
            res['ec_print_address'] = kwargs['invoice_address']
            res['ec_print'] = True
        # 情況3：要捐贈發票
        elif kwargs['donate_flag'] is True:
            res['ec_donate'] = True
            res['ec_donate_number'] = kwargs['LoveCode']
        # 情況4：不列印也不捐贈，只使用載具
        elif kwargs['print_flag'] is False and kwargs['donate_flag'] is False:
            if kwargs['invoice_type'] == '0':
                res['ec_carruer_type'] = ''
            else:
                res['ec_carruer_type'] = kwargs['invoice_type']

            if kwargs['invoice_type'] == '2' or kwargs['invoice_type'] == '3':
                res['ec_carruer_number'] = kwargs['CarruerNum']
            else:
                res['ec_carruer_number'] = ''

        else:
            print("error!!")
        print(res)
        order.write(res)
        return '200'
