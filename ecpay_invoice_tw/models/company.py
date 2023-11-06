# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ecpay_demo_mode = fields.Boolean(string='測試模式', help='會使用測試電子發票的API網址進行開票', default=True)
    ecpay_MerchantID = fields.Char(string='MerchantID', default='2000132')
    ecpay_HashKey = fields.Char(string='HashKey', default='ejCk326UnaZWKisg')
    ecpay_HashIV = fields.Char(string='HashIV', default='q9jcZX8Ib9LM8wYk')
    auto_invoice = fields.Selection(string='開立電子發票方式', required=True,
                                    selection=[('manual', '手動'), ('automatic', '自動'), ('hand in', '人工填入')],
                                    default='manual')
    seller_Identifier = fields.Char(string='賣方統編', default='53538851')
