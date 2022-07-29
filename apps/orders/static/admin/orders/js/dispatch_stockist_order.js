if (!$) {
  $ = django.jQuery();
}
// Get the modal
var modal = document.getElementById("myModal");

// Get the button that opens the modal
var btn = document.getElementById("myBtn");

var cancel_btn = document.getElementById("cancel-button");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

var loader = document.getElementById("overlay-spinner");

// When the user clicks on the button, open the modal
btn.onclick = function () {
  modal.style.display = "block";
};

// When the user clicks on <span> (x), close the modal
span.onclick = function () {
  modal.style.display = "none";
};

cancel_btn.onclick = function () {
  modal.style.display = "none";
};

// When the user clicks anywhere outside of the modal, close it
// window.onclick = function (event) {
//   if (event.target == modal) {
//     modal.style.display = "none";
//   }
// }; option:selected

function addProduct() {
  const product_id = $("#add-product-id").val();
  const available_stock = Number($("#add-product-id option:selected").attr("data-stock"));
  console.log(available_stock);

  if (product_id == null) {
    alert("Please select a product");
    $("#add-product-id").css({
      border: "1px solid red",
    });
    return false;
  }

  console.log($("#order-id").val());
  const url = $("#add-product-url").val();
  var token = $('input[name="csrfmiddlewaretoken"]').attr("value");
  var data = {
    order_id: Number($("#order-id").val()),
    product_id: Number(product_id),
  };
  $.ajax({
    url: url,
    data: JSON.stringify(data),
    method: "POST",
    contentType: "application/json",
    headers: {
      "X-CSRFToken": token,
    },
    beforeSend: function () {
      loader.style.display = "block";
      modal.style.display = "none";
    },
    success: function (data) {
      console.log(data);
      location.reload();
    },
    error: function (data) {
      console.log("error");
      modal.style.display = "block";
      loader.style.display = "none";
    },
  });
}
