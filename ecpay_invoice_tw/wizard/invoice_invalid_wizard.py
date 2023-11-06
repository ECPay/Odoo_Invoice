# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models
from odoo.addons.ecpay_invoice_tw.sdk.ecpay_main import *
from odoo.exceptions import UserError


class InvoiceInvalidWizard(models.TransientModel):
    _name = 'invoice.invalid.wizard'
    _description = '作廢折讓發票時必須填入原因'

    reason = fields.Char(string='作廢折讓原因', required=True)

    # 執行電子發票折讓作廢
    def run_refund_invalid(self):
        self.ensure_one()
        # 取得欲作廢的折讓單
        refund = self.env['account.move'].browse(self._context.get('active_id'))
        # 若有折讓單，進行檢查是否有折讓號碼
        if refund.IA_Allow_No is False:
            raise UserError('找不到折讓單號或是發票折讓單號!!')

        # 建立物件
        invoice = EcpayInvoice()

        company_id = refund.company_id

        # 初始化物件
        refund.ecpay_invoice_init(invoice, 'B2CInvoice/AllowanceInvalid', 'AllowanceInvalid', company_id)

        # 設定折讓作廢需要參數
        invoice.Send['InvoiceNo'] = refund.IA_Invoice_No.name
        invoice.Send['AllowanceNo'] = refund.IA_Allow_No
        invoice.Send['Reason'] = self.reason

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 判定是否成功作廢
        if aReturn_Info['RtnCode'] != 1:
            if aReturn_Info['RtnCode'] == 2000063:
                refund.IA_Invoice_No = False
                refund.IA_Allow_No = False
                refund.ecpay_invoice_id.IIS_Remain_Allowance_Amt = refund.ecpay_invoice_id.IIS_Sales_Amount
            else:
                raise UserError('作廢電子發票折讓失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])
        else:
            # 更新儲存在此張折讓憑單中的的電子發票資訊,去除要作廢的折讓的發票欄位、折讓號碼欄位
            refund.IA_Invoice_No = False
            refund.IA_Allow_No = False
            refund.ecpay_invoice_id.IIS_Remain_Allowance_Amt = refund.ecpay_invoice_id.IIS_Sales_Amount
