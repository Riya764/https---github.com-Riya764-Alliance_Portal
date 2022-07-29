(function($) {
    $(document).ready(function() {
        $("#id_cancel_order option").attr("disabled", false);
        $("#id_cancel_reason").attr("disabled", false);
        if ($("#id_order_status option").attr("disabled")) {
            $("#id_cancel_order option").attr("disabled", true);
            $("#id_cancel_reason").attr("disabled", true);
        }

        var dissable_options = [];
        $("#id_order_status > option[disabled]").each(function() {
            dissable_options.push(this.value);
        });
        $("#id_order_status option").attr("disabled", false);

        var order_status_index = $("#id_order_status").val();
        if (order_status_index === 7) {
            var other_reason = $(".field-cancel_order > div > p").html();

            if (other_reason.indexOf("Other") != -1) {
                $(".field-cancel_reason").show();
            } else {
                $(".field-cancel_reason").hide();
            }
        } else {
            $(".field-cancel_reason").hide();
            $(".field-cancel_order").hide();
        }

        $("#id_order_status > option").each(function() {
            if ($.inArray(this.value, dissable_options) != -1) {
                $(this).attr("disabled", true);
            }
        });

        $("#id_order_status").on("change", function(d) {
            if ($(this).val() == 7) {
                $(".field-cancel_order").show();
                $("#id_cancel_order").attr("required", "");
                $("#id_cancel_order option").attr("disabled", false);
                var selected_index = $(
                    'select[id$="id_cancel_order"] option:selected'
                ).index();
                if (selected_index == 5) {
                    $(".field-cancel_reason").show();
                } else {
                    $(".field-cancel_reason").hide();
                }
            } else {
                $(".field-cancel_reason").hide();
                $(".field-cancel_order").hide();
            }
        });

        $("#id_cancel_order").on("change", function(e) {
            if (e.target.selectedIndex == 5) {
                $("#id_cancel_reason").val("");
                $("#id_cancel_reason").attr("disabled", false);
                $(".field-cancel_reason").show();
            } else {
                $("#id_cancel_reason").attr("disabled", true);
                $(".field-cancel_reason").hide();
            }
        });

        $("form").bind("submit", function(event) {
            $(".errornote").remove();
            $(".errorlist").remove();

            var bOK = true;
            var selected_index = $(
                'select[id$="id_cancel_order"] option:selected'
            ).index();
            var order_status_index = parseInt(
                document.getElementById("id_order_status").value
            );

            // check for partial dispatch and display error message
            $(
                '.dynamic-distributor_order_details select[id^="id_distributor_order_details"]'
            ).each(function(key, option) {
                if (option.value == "5" && order_status_index != 5) {
                    alert(
                        "Please select order status as Dispatch, Partial Dispatch is not allowed!"
                    );
                    bOK = false;
                    event.preventDefault();
                    return false;
                }

                if (option.value != "5" && order_status_index == 5) {
                    alert("Please select item status as Dispatch!");
                    bOK = false;
                    event.preventDefault();
                    return false;
                }
            });

            // check for partial receive and display error message
            $(
                '.dynamic-alliancepartnerorderdetail_set select[id$="item_status"]'
            ).each(function(key, option) {
                if (option.value == "6" && order_status_index != 6) {
                    alert(
                        "Please select order status as RS RECEIVED, Partial Receiving is not allowed!"
                    );
                    bOK = false;
                    event.preventDefault();
                    return false;
                }
            });

            // make disabled option false for submitting value to form
            if (bOK) {
                $("#id_order_status option").attr("disabled", false);

                if ($("select[name^=distributor_order_details]") != undefined) {
                    $("select[name^=distributor_order_details] option").attr(
                        "disabled",
                        false
                    );
                }

                $('select[id^="id_alliancepartnerorderdetail_set"] option').attr(
                    "disabled",
                    false
                );
            }

            if (order_status_index == 7) {
                if (selected_index == 0) {
                    $("fieldset:first-child").before(
                        '<p class="errornote">Please correct the errors below.</p>'
                    );
                    $(".field-cancel_order:first div").before(
                        '<ul class="errorlist"><li>This field is required.</li></ul>'
                    );
                    return false;
                }
                if (selected_index == 5) {
                    if ($("#id_cancel_reason").val() == "") {
                        $("fieldset:first-child").before(
                            '<p class="errornote">Please correct the errors below.</p>'
                        );
                        $(".field-cancel_reason:first div").before(
                            '<ul class="errorlist"><li>This field is required.</li></ul>'
                        );
                        return false;
                    }
                }
            }
        });
        //for admin
        var order_status_index_admin = $(".field-order_status p").html();
        if (order_status_index_admin == "CANCELLED") {
            var selected_index_admin = $(".field-cancel_order p").html();
            $(".field-cancel_order").show();
            if (selected_index_admin == "Other") {
                $(".field-cancel_reason").show();
            } else {
                $(".field-cancel_reason").hide();
            }
        }
        //end here admin
    });
})(django.jQuery);