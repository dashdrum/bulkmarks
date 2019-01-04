

/* Get title when URL is entered */
$(document).ready(function(){
  $("#id_url").focusout(function() {
    var title = $("#id_title").val();
    if(title == null || title == ""){
      $.ajax({
          type: "GET",
          url: "/l/api/gettitle/",
          data:  {'URL':  $(this).val()},
          dataType: 'json',
          success: function(data, textStatus, xhr){
            var data = $.parseJSON(xhr.responseText);
            var title = data["title"];
            $('#id_title').val(title);
          },
          error: function(xhr, textStatus, errorThrown){

            var data = $.parseJSON(xhr.responseText);

            error_code = data["error_code"]
            error_message = data["error_message"]
            /* This alert is only here for debugging */
            // alert(error_message);
          }
      });
    };
  });
});