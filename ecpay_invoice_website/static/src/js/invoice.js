odoo.define('ecpay_invoice_tw.checkout', function (require) {
    "use strict";

    const rpc = require('web.rpc');
    const publicWidget = require('web.public.widget');
    const PaymentCheckoutForm = require('payment.checkout_form');

    let sharedDataset = {
        invoiceType: 0,

        eType: 0,
        carrierNum: '',
        name: '',
        identifier: '',

        address: '',
        vatNeeded: false,

        loveCode: '',
    };

    let ECPayInvoiceHandler = publicWidget.Widget.extend({
        selector: '.ecpay-invoice-info-form',
        events: {
            'click #ecpay_invoice_print .form-check': '_changeType',

            // 電子發票
            'change #invoice_e_type': '_changeEType',
            'change #CarrierNum': '_changeCarrierNum',

            // 紙本發票
            'change #invoice_address': '_changeAddress',
            'change input[name="identifier_group"]': '_changePaperIdenti',
            'change #identifier_name': '_changeBuyerName',
            'change #identifier': '_changeBuyerIdentifier',

            // 捐贈
            'change #LoveCode': '_changeLoveCode',
        },

        init: function () {
            let def = this._super(...arguments);
            this.state = sharedDataset;

            this.default_msg = {
                carrierNum: '載具格式為1碼斜線「/」加上7碼由數字及大寫英文字母及+-.符號組成的字串',
                natureNum: '總長度為16碼字元,前兩碼為大寫英文【A-Z】,後14碼為數字【0-9】',
                wait: '判斷中，請稍候...',
            }
            return def;
        },

        start: function () {
            this.$page = this.$el.find('.invoice-page');
            this.changeTypePage();

            this.state.address = this.$el.find('#invoice_address').val();

            return this._super(...arguments)
        },

        // --------------------
        //  Handler
        // --------------------
        changeTypePage: function () {
            this.$page.hide()
                .eq(this.state.invoiceType).show();
        },

        updateBuyerAlert: function () {
            let $alert = this.$el.find('#warning-identifier');

            let msg = [];
            if (!this.state.name) {
                msg.push('- 請輸入受買人名稱(不可有特殊符號)')
            }

            if (!this.state.identifier) {
                msg.push('- 請輸入正確的統編')
            }

            $alert.html(msg.join('<br/>'))[msg.length ? 'removeClass' : 'addClass']('d-none');
        },

        // --------------------
        //  Events
        // --------------------
        _changeType: function (ev) {
            let input = ev.currentTarget.querySelector('input');
            if (!input) {
                return false;
            }

            if (input.checked === false) {
                input.checked = true;
            }

            this.state.invoiceType = parseInt(input.value) || 0;
            this.changeTypePage();
        },

        _changeEType: function (ev) {
            this.state.eType = parseInt(ev.currentTarget.value) || 0;

            if (this.state.eType < 0 || this.state.eType > 3) {
                this.state.eType = 0;
            }

            this.$el.find('#ecpay_invoice_CarrierNum')
                .toggleClass('d-none', this.state.eType < 2);

            let $msg = this.$el.find('#warning-CarrierNum');
            console.log(this.state.eType);
            if (this.state.eType === 2) {
                $msg.text(this.default_msg.natureNum);
            } else if (this.state.eType === 3) {
                $msg.text(this.default_msg.carrierNum);
            }
        },

        _changeCarrierNum: function (ev) {
            let target = ev.currentTarget;
            let $msg = this.$el.find('#warning-CarrierNum');
            let value = target.value || '';
            let msg = this.default_msg.carrierNum;
            let pass = true;

            if (this.state.eType > 1) {
                if (this.state.eType === 2) {
                    if (!/^[A-Za-z]{2}[0-9]{14}$/.test(value)) {
                        msg = `自然人憑證格式不正確！${this.default_msg.natureNum}`;
                        pass = false;
                    } else {
                        msg = this.default_msg.natureNum;
                    }
                } else {
                    if (/^\/[0-9a-zA-Z+-.]{7}$/.test(value)) {
                        target.disabled = true;
                        msg = this.default_msg.wait;
                        rpc.query({
                            model: 'account.move',
                            method: 'check_carrier_num',
                            args: [value],
                        }).then(result => {
                            target.disabled = false;

                            if (!result) {
                                $msg.text(`載具內容不存在！${this.default_msg.carrierNum}`);
                            }

                            this.state.carrierNum = result ? value : '';
                        });
                    } else {
                        msg = `格式錯誤！${this.default_msg.carrierNum}`;
                        pass = false;
                    }
                }
            }

            $msg.text(msg);
            this.state.carrierNum = pass ? value : '';
        },

        _changeAddress: function (ev) {
            let value = ev.currentTarget.value || '';
            let $alert = this.$el.find('#div-invoice_address .alert');
            if (value.length < 5 || value.length > 300) {
                $alert.removeClass('d-none');
                this.state.address = '';
                return false;
            }

            $alert.addClass('d-none');
            this.state.address = value;
        },

        _changePaperIdenti: function (ev) {
            this.state.vatNeeded = ev.currentTarget.value === '1';

            this.$el.find('#ecpay_invoice_identifier_name')
                .toggleClass('d-none', !this.state.vatNeeded);
        },

        _changeBuyerName: function (ev) {
            let value = ev.currentTarget.value || '';
            let reTest = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(value);
            this.state.name = (value.length && !reTest) ? value : '';
            this.updateBuyerAlert();
        },

        _changeBuyerIdentifier: function (ev) {
            let value = ev.currentTarget.value || '';
            let reTest = /^[0-9]{8}$/.test(value);
            this.state.identifier = reTest ? value : '';
            this.updateBuyerAlert();
        },

        _changeLoveCode: function (ev) {
            let $alert = this.$el.find('#warning-LoveCode');
            let target = ev.currentTarget;
            let value = target.value;

            if (!/^([xX][0-9]{2,6}|[0-9]{3,7})$/.test(value)) {
                $alert.text('愛心碼格式應為3~7碼的數字').removeClass('d-none');
                sharedDataset.loveCode = '';
                return true;
            }

            target.disabled = true;
            $alert.text(this.default_msg.wait).removeClass('d-none alert-danger').addClass('alert-warning');
            rpc.query({
                model: 'account.move',
                method: 'check_lovecode',
                args: [value],
            }).then(result => {
                target.disabled = false;

                if (result) {
                    $alert.addClass('d-none');
                } else {
                    $alert.text('愛心碼不存在').removeClass('alert-warning').addClass('alert-danger');
                    target.focus();
                }

                sharedDataset.loveCode = result ? value : '';
            });
        },
    });

    publicWidget.registry.ECPayInvoiceHandler = ECPayInvoiceHandler;

    PaymentCheckoutForm.include({
        _onClickPay: function (ev) {
            const self = this;
            const originSuper = this._super;
            ev.stopPropagation();
            ev.preventDefault();
            let target = ev.currentTarget;

            let prom = this._ensureEcpayInvoiceAlright();
            if (prom) {
                target.disabled = true;
                prom.then(result => {
                    target.disabled = false;
                    if (!result) {
                        self._displayError('更新電子發票資訊失敗', '更新電子發票資訊失敗，請稍後重試');
                    } else {
                        originSuper.apply(self, arguments);
                    }
                });
            }
        },

        _ensureEcpayInvoiceAlright() {
            let prom, showError = (t, m) => this._displayError(
                t || '未定義的錯誤',
                m || '未定義的錯誤'
            );
            let route = '/payment/ecpay/save_invoice_type';

            let { invoiceType } = sharedDataset;
            if (invoiceType === 0) {
                if (sharedDataset.eType > 1  && !sharedDataset.carrierNum) {
                    return false;
                }

                prom = rpc.query({
                    route,
                    params: {
                        invoiceType,
                        e_type: sharedDataset.eType,
                        CarrierNum: sharedDataset.carrierNum,
                    }
                });
            } else if (invoiceType === 1) {
                if (!sharedDataset.address) {
                    showError('電子發票有必填欄位尚未填寫', '請填寫發票寄送地址！')
                    return false;
                }

                let dataset = {
                    invoiceType,
                    print_flag: true,
                    invoice_address: sharedDataset.address,
                };

                if (sharedDataset.vatNeeded) {
                    if (!sharedDataset.name || !sharedDataset.identifier) {
                        showError('電子發票有必填欄位尚未填寫', '請確認「受買人姓名」，「統一編號」是否有填寫');
                        return false;
                    }

                    Object.assign(dataset, {
                        ident_flag: true,
                        identifier_name: sharedDataset.name,
                        identifier: sharedDataset.identifier,
                    });
                }

                prom = rpc.query({
                    route,
                    params: dataset
                });
            } else if (invoiceType === 2) {
                if (!sharedDataset.loveCode) {
                    showError('電子發票有必填欄位尚未填寫', '請確認「捐贈碼」是否有填寫正確');
                    return false;
                }

                prom = rpc.query({
                    route,
                    params: {
                        invoiceType,
                        LoveCode: sharedDataset.loveCode,
                    }
                });
            } else {
                showError('錯誤的類型', '不支援的電子發票類型');
                return false;
            }

            return prom;
        },
    });

    return {
        sharedDataset,
        ECPayInvoiceHandler,
    };
});