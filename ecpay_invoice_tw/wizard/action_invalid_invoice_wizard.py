# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models
from odoo.addons.ecpay_invoice_tw.sdk.ecpay_main import *
from odoo.exceptions import UserError


class ActionInvalidInvoiceWizard(models.TransientModel):
    _name = 'action.invalid.invoice.wizard'
    _description = '作廢電子發票時必須填入原因'

    reason = fields.Char(string='作廢發票原因', required=True)

    # 執行電子發票作廢
    def run_invoice_invalid(self):
        self.ensure_one()
        move = self.env['account.move'].browse(self._context.get('active_id'))
        if move.move_type != 'out_invoice':
            raise UserError('作廢電子發票的應收憑單類型應該為客戶應收憑單')

        # 檢查是否有開立電子發票
        if move.ecpay_invoice_id:
            if move.ecpay_invoice_id.IIS_Invalid_Status == '1':
                raise UserError('該電子發票：%s 已作廢!!' % move.ecpay_invoice_id.name)
        else:
            raise UserError('找不到電子發票!!')

        # 建立物件
        invoice = EcpayInvoice()

        company_id = move.company_id

        # 初始化物件
        move.ecpay_invoice_init(invoice, 'B2CInvoice/Invalid', 'Invalid', company_id)

        # 設定電子發票作廢需要參數
        invoice.Send['InvoiceNo'] = move.ecpay_invoice_id.name
        invoice.Send['InvoiceDate'] = move.ecpay_invoice_id.IIS_Create_Date.strftime("%Y/%m/%d")
        invoice.Send['Reason'] = self.reason

        # 送出資訊
        aReturn_Info = invoice.Check_Out()

        # 判定是否成功作廢
        if aReturn_Info['RtnCode'] != 1:
            raise UserError('作廢電子發票失敗!!錯誤訊息：' + aReturn_Info['RtnMsg'])

        # 更新儲存在Odoo中的電子發票資訊
        move.ecpay_invoice_id.get_ecpay_invoice_info()
        move.ecpay_invoice_id = None
        move.uniform_state = 'invalid'
