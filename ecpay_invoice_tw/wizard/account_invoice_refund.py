from odoo import models, fields, api
from odoo.exceptions import UserError


class ECPAYINVOICEREFUNDInherit(models.TransientModel):
    _inherit = 'account.invoice.refund'

    refund_ecpay_kind = fields.Selection([('offline', '紙本同意'), ('online', '線上同意')],
        default='offline', string='同意類型', required=True, help='折讓電子發票同意類型')


    @api.multi
    def compute_refund(self, mode='refund'):
        res = super(ECPAYINVOICEREFUNDInherit, self).compute_refund(mode)
        context = dict(self._context or {})
        # 取得欲作廢或折讓的發票
        inv_obj = self.env['account.invoice'].browse(context.get('active_ids'))
        if len(inv_obj) == 0:
            raise UserError('錯誤，找不到欲作廢或折讓的發票！')
        if type(res) == dict:
            target = None
            # 從res中抓取產生的折讓單的 id
            data_refund = res['domain']
            for line in data_refund:
                if line[0] == 'id':
                    target = line[2]
                    break
            refund_inv = self.env['account.invoice'].browse(target)
            if len(refund_inv) == 0:
                raise UserError('錯誤，找不到建立的折讓單！')
            if mode == 'cancel':
                # 設定該折讓單要關聯欲作廢或折讓的統一發票
                refund_inv.ecpay_invoice_id = inv_obj.ecpay_invoice_id.id
                # 執行作廢
                refund_inv.run_invoice_invalid()
                # 將原先欲作廢的發票更新發票狀態
                inv_obj.uniform_state = 'invalid'
            elif mode == 'refund':
                # 設定該折讓單要關聯欲作廢或折讓的統一發票
                refund_inv.ecpay_invoice_id = inv_obj.ecpay_invoice_id.id
                refund_inv.refund_ecpay_kind = self.refund_ecpay_kind
                # 折讓參數
                refund_inv.is_refund = True
        return res
