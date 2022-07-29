(function($) {
    "use strict";
    $(document).ready(function() {
        if (typeof $("#id_order_status") !== undefined) {
            $("#id_order_status").on("change", function() {
                var parent_option = $(this).val();
                $(".field-item_status > select:visible").each(function() {
                    if (
                        $("option[value=" + parent_option + "]", this).attr("disabled") !=
                        "disabled"
                    ) {
                        $(this).val(parent_option);
                    }
                });
            });
        }
    });
})(django.jQuery);