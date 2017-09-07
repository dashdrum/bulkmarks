$(function () {

  $(".js-add-link").click(function () {
    $.ajax({
      url: '/l/create/',
      type: 'get',
      dataType: 'json',
      beforeSend: function () {
        $("#modal-link").modal("show");
      },
      success: function (data) {
        $("#modal-link .modal-content").html(data.html_form);
      }
    });
  });

});

$("#modal-link").on("submit", ".js-link-add-form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          alert("Link created!");  // <-- This is just a placeholder for now for testing
        } else {
          $("#modal-link .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  });