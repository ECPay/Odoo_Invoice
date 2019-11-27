odoo.define('ecpay_invoice_tw.checkout', function (require) {
    "use strict";

    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var check_invoice_name = false, check_ident = false, check_invoice_address = false , check_num= false, check_lovecode = false;

    var add_show = false,love_show = false,type_show = false,carr_show=false,ident_show = false,ident_data_show=false;
    // 傳送資料到後端
    function chose_invoice_type() {
        var invoice_type = $("#invoice_type").find(":selected").val();
        var LoveCode = $("#LoveCode").val();
        var invoice_address=$("#invoice_address").val();
        var CarruerNum=$("#CarruerNum").val();
        var identifier=$("#identifier").val();
        var identifier_name=$("#identifier_name").val();
        var ident_flag = $('#is_identifier').prop("checked");
        var donate_flag = $('#donate').prop("checked");
        var print_flag = $('#print').prop("checked");
        // 檢查是否為電子發票輸入畫面
        if (invoice_type != null && LoveCode != null && invoice_address != null && CarruerNum != null && identifier != null && identifier_name != null &&
            ident_flag != null && donate_flag != null && print_flag != null){
            ajax.jsonRpc('/payment/ecpay/save_invoice_type', 'call', {
                invoice_type: invoice_type,
                CarruerNum: CarruerNum,
                LoveCode: LoveCode,
                invoice_address:invoice_address,
                identifier:identifier,
                identifier_name:identifier_name,
                ident_flag :ident_flag,
                donate_flag:donate_flag,
                print_flag:print_flag
            }).then(function () {

            });
        }
    }


    // 計算名稱字數
    let check_invoice_name_length = (name) => {
            let l = name.length;
            let blen = 0;
            for (let i = 0; i < l; i++) {
                if ((name.charCodeAt(i) & 0xff00) != 0) {
                    blen++;
                }
                blen++;
            }
            return blen;
        };

    $(document).ready(function() {
        // 預設使用載具
        type_show = true;
        // 初始化 將全部欄位隱藏
        $('#div-invoice_address').hide();
        $('#ecpay_invoice_LoveCode').hide();
        $('#ecpay_invoice_CarruerNum').hide();
        $('#ecpay_invoice_identifier').hide();
        $('#ecpay_invoice_identifier_name').hide();

        // 抓取原生下一步按鈕
        var next_button = $('.btn.btn-primary.pull-right.mb32');

        // 按下驗證後，呼叫controller，執行發票資訊寫入到銷售訂單。
        next_button.on("click",function () {
            chose_invoice_type();
        });

        function next_button_botton_validate () {
            // 情況1：列印紙本發票
            if (add_show && ident_data_show === false){
                if (check_invoice_address){
                    next_button.prop('disabled', false);
                }else {
                    next_button.prop('disabled', true);
                }
            }
            // 情況2：開立統編發票
            else if (add_show && ident_show && ident_data_show){
                if (check_invoice_name && check_ident && check_invoice_address) {
                    next_button.prop('disabled', false);
                } else {
                    next_button.prop('disabled', true);
                }
            }
            // 請況3：捐贈發票
            else if (love_show){
                if(check_lovecode){
                    next_button.prop('disabled', false);
                } else {
                    next_button.prop('disabled', true);
                }
            }
            // 情況4：只使用載具
            else if (type_show && carr_show){
                if (check_num){
                    next_button.prop('disabled', false);
                }
                else {
                    next_button.prop('disabled', true);
                }
            }
        }
        // 決定是否顯示錯誤訊息
        function waring_check(){
            if (check_invoice_name) {
                $('#warning-identifier_name').hide();
            } else {
                $('#warning-identifier_name').show();
            }
            if (check_invoice_address) {
                $('#warning-invoice_address').hide();
            } else {
                $('#warning-invoice_address').show();
            }
            if (check_ident) {
                $('#warning-identifier').hide();
            } else {
                $('#warning-identifier').show();
            }
            if (check_lovecode){
                $('#warning-LoveCode').hide();
            } else {
                $('#warning-LoveCode').show();
            }
            if (check_num){
                $('#warning-CarruerNum').hide();
            } else {
                $('#warning-CarruerNum').show();
            }
            next_button_botton_validate();
        }

        // 確定是否顯示發票欄位
        function show_invoice_item() {
            if(add_show){
                $('#div-invoice_address').fadeIn();
            }else {
                $('#div-invoice_address').fadeOut();
            }
            if(love_show){
                $('#ecpay_invoice_LoveCode').fadeIn();
            }else {
                $('#ecpay_invoice_LoveCode').fadeOut();
            }
            if(type_show){
                $('#invoice_type_selection').fadeIn();
            }else {
                $('#invoice_type_selection').fadeOut();
                carr_show=false;
            }
            if(carr_show){
                $('#ecpay_invoice_CarruerNum').fadeIn();
            }else {
                $('#ecpay_invoice_CarruerNum').fadeOut();
            }
            if(ident_show){
                $('#ecpay_invoice_identifier').fadeIn();
            }else {
                $('#ecpay_invoice_identifier').fadeOut();
                ident_data_show=false;
            }
            if(ident_data_show){
                $('#ecpay_invoice_identifier_name').fadeIn();
            }else {
                $('#ecpay_invoice_identifier_name').fadeOut();
            }
            next_button_botton_validate();
        }

        // 判定是否列印，捐贈發票
        $('input[type=radio][name=print_group]').change(function () {
            if (this.value === '0'){
                add_show = false;
                love_show = false;
                type_show = true;
                ident_show = false;
                if ($('#invoice_type').val()==='2' || $('#invoice_type').val()==='3'){
                    carr_show=true;
                }
            }
            else if (this.value === '1'){
                // 顯示發票地址
                add_show = true;
                // 隱藏愛心碼
                love_show = false;
                // 顯示是否使用載具
                type_show = false;
                // 顯示是否使用統一編號
                ident_show = true;
                if($('#is_identifier').prop("checked")){
                    ident_data_show = true;
                }
            }
            else if (this.value === '2'){
                add_show = false;
                love_show = true;
                type_show = false;
                ident_show = false;
            }
            show_invoice_item();
        });


        // 如果載具選項有變，顯示載具輸入框
        $('#invoice_type_selection').on("change", "#invoice_type", function () {
            if ($('#invoice_type').val()==='2'){
                $('#warning-CarruerNum').html('載具格式為固定長度為16且格式為2碼大寫英文字母加上14碼數字');
                carr_show=true;
            }
            else if($('#invoice_type').val()==='3'){
                $('#warning-CarruerNum').html('載具格式為1碼斜線「/」加上7碼由數字及大寫英文字母及+-.符號組成的字串');
                carr_show=true;
            }
            else{
                carr_show=false;
            }
            show_invoice_item();
        });

        // 是否使用統編
        $('input[type=radio][name=identifier_group]').change(function () {
            if (this.value === '1'){
                ident_data_show = true;
            }
            else{
                ident_data_show = false;
            }
            show_invoice_item();
        });



        // 判別地址
        $('#invoice_address').on('input', function () {
            var input = $(this);
            var is_invoice_address = input.val();
            if (is_invoice_address && is_invoice_address.length >= 6 && is_invoice_address.length <= 60) {
                $('#div-invoice_address').removeClass("has-error");
                check_invoice_address = true;
            } else {
                $('#div-invoice_address').addClass("has-error");
                check_invoice_address = false;
            }
            waring_check()
        });

        // 判別統編格式
        $('#identifier').on('input', function () {
            var input = $(this);
            var re = /^[0-9]{8}$/;
            var is_ident = re.test(input.val());
            if (is_ident) {
                $('#div-identifier').removeClass("has-error");
                check_ident = true;
            } else {
                $('#div-identifier').addClass("has-error");
                check_ident = false;
            }
            waring_check()
        });

        // 判別載具格式
        $('#CarruerNum').on('input', function () {
            var carruer_type = $("#invoice_type").find(":selected").val();
            var input = $(this);
            var is_identifier = input.val();
            if (carruer_type === '2'){
                if(is_identifier.match(new RegExp(/^[A-Za-z]{2}[0-9]{14}$/)) === null){
                    $('#ecpay_invoice_CarruerNum').addClass("has-error");
                    check_num = false;
                }
                else {
                    $('#ecpay_invoice_CarruerNum').removeClass("has-error");
                    check_num = true;
                }
            }
            else if (carruer_type === '3') {
                if(is_identifier.match(new RegExp(/^\/{1}[0-9a-zA-Z+-.]{7}$/)) === null){
                    $('#ecpay_invoice_CarruerNum').addClass("has-error");
                    $("#warning-CarruerNum").html("載具格式為1碼斜線「/」加上7碼由數字及大寫英文字母及+-.符號組成的字串");
                    check_num = false;
                }
                else {
                    // 檢查手機條碼的正確性API
                    rpc.query({
                        model: 'account.move',
                        method: 'check_carruernum',
                        args: [is_identifier],
                    }).then(function (result) {
                        // 如果結果正確，就移除錯誤警告
                        if (result){
                        $('#ecpay_invoice_CarruerNum').removeClass("has-error");
                        check_num = true;
                        waring_check()
                        }
                        else {
                            $("#warning-CarruerNum").html("載具內容不存在");
                        }
                    });
                }
            }

            waring_check()
        });

        // 判別使用者姓名
        $('#identifier_name').on('input', function () {
            var input = $(this);
            var is_name = input.val();
            var format = /[ !@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/;
            if (is_name && check_invoice_name_length(is_name) >= 4 && check_invoice_name_length(is_name) <= 40 &&
              (format.test(is_name) === false)) {
              $('#div-identifier_name').removeClass("has-error");
              check_invoice_name = true;
            } else {
              $('#div-identifier_name').addClass("has-error");
              check_invoice_name = false;
            }
            waring_check()
        });

        // 判別愛心碼
        $('#LoveCode').on('input', function () {
            var input = $(this);
            var re = /^([xX]{1}[0-9]{2,6}|[0-9]{3,7})$/;
            var is_ident = re.test(input.val());
            if (is_ident){

                // 檢查愛心碼的正確性API
                rpc.query({
                    model: 'account.move',
                    method: 'check_lovecode',
                    args: [input.val()],
                }).then(function (result) {
                    // 如果結果正確，就移除錯誤警告
                    if (result){
                        $('#ecpay_invoice_LoveCode').removeClass("has-error");
                        check_lovecode = true;
                        waring_check()
                    }
                    else {
                        $('#warning-LoveCode').html("愛心碼不存在");
                    }

                });
            } else {
                $('#warning-LoveCode').html("愛心碼格式應為3~7碼的數字");
                $('#ecpay_invoice_LoveCode').addClass("has-error");
                check_lovecode = false;

            }
            waring_check()
        });
    });
});