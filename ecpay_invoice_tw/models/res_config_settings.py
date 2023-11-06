# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models, fields


class EcpayInvocieResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ecpay_demo_mode = fields.Boolean(string='測試模式', help='會使用測試電子發票的API網址進行開票',
                                     related='company_id.ecpay_demo_mode', readonly=False)
    ecpay_MerchantID = fields.Char(string='MerchantID', related='company_id.ecpay_MerchantID', readonly=False)
    ecpay_HashKey = fields.Char(string='HashKey', related='company_id.ecpay_HashKey', readonly=False)
    ecpay_HashIV = fields.Char(string='HashIV', related='company_id.ecpay_HashIV', readonly=False)
    auto_invoice = fields.Selection(string='開立電子發票方式', required=True,
                                    selection=[('manual', '手動'), ('automatic', '自動'), ('hand in', '人工填入')],
                                    related='company_id.auto_invoice', readonly=False)
    seller_Identifier = fields.Char(string='賣方統編', related='company_id.seller_Identifier', readonly=False)
