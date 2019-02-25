
from odoo import models, fields, api


class EcpayInvocieResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ecpay_demo_mode = fields.Boolean(string='測試模式', help='會使用測試電子發票的API網址進行開票')
    ecpay_MerchantID = fields.Char(string='MerchantID')
    ecpay_HashKey = fields.Char(string='HashKey')
    ecpay_HashIV = fields.Char(string='HashIV')
    auto_invoice = fields.Selection(string='開立電子發票方式', required=True,
                                    selection=[('manual', '手動'), ('automatic', '自動'), ('hand in', '人工填入')])
    seller_Identifier = fields.Char(string='賣方統編')

    @api.model
    def get_values(self):
        res = super(EcpayInvocieResConfigSettings, self).get_values()
        res.update(
            ecpay_demo_mode=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_demo_mode'),
            ecpay_MerchantID=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_MerchantID'),
            ecpay_HashKey=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_HashKey'),
            ecpay_HashIV=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.ecpay_HashIV'),
            auto_invoice=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.auto_invoice'),
            seller_Identifier=self.env['ir.config_parameter'].sudo().get_param('ecpay_invoice_tw.seller_Identifier')
        )
        return res

    @api.multi
    def set_values(self):
        super(EcpayInvocieResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.ecpay_demo_mode', self.ecpay_demo_mode)
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.ecpay_MerchantID', self.ecpay_MerchantID)
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.ecpay_HashKey', self.ecpay_HashKey)
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.ecpay_HashIV', self.ecpay_HashIV)
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.auto_invoice', self.auto_invoice)
        self.env['ir.config_parameter'].sudo().set_param('ecpay_invoice_tw.seller_Identifier', self.seller_Identifier)
