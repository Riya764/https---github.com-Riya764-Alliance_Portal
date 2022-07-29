(function($) {
    'use strict';
    $(document).ready(function() {
        if (typeof($("#id_brand")) != undefined) {
            $("#id_brand").on("change", function() {
                var partner_id = $(this).val();
                if (partner_id != '') {
                    $.ajax({
                        url: "/app/get_partner_code/",
                        method: "GET",
                        data:{allianceid:partner_id},
                        success: function(data){
                            if(data['code'] !=''){
                                $("#id_partner_code").val(data['code']);
                            }
                        }
                    });
                }
            });
        }
    });
})(django.jQuery);