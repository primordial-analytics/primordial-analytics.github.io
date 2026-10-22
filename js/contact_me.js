$(function() {

  function showAlert(type, $content) {
    return $("<div class='alert alert-dismissible fade show'>")
      .addClass("alert-" + type)
      .append($content)
      .append("<button type='button' class='btn-close' data-bs-dismiss='alert' aria-label='Close'></button>")
      .appendTo($("#success").empty());
  }

  $("#contactForm input,#contactForm select,#contactForm textarea").jqBootstrapValidation({
    preventSubmit: true,
    submitError: function($form, event, errors) {
      $form.find("[aria-invalid='true']").first().trigger("focus");
    },
    submitSuccess: function($form, event) {
      event.preventDefault(); // prevent default submit behaviour
      var $this = $("#sendMessageButton");
      if ($this.attr("aria-disabled") === "true") {
        return; // a send is already in progress
      }
      // get values from FORM
      var name = $("input#name").val();
      var email = $("input#email").val();
      var phone = $("input#phone").val();
      var role = $("select#role").val();
      var message = "I am: " + role + "\n\n" + $("textarea#message").val();
      var firstName = name; // For Success/Failure Message
      // Check for white space in name for Success/Fail message
      if (firstName.indexOf(' ') >= 0) {
        firstName = name.split(' ').slice(0, -1).join(' ');
      }
      // Not the disabled property: that would drop keyboard focus to <body>
      $this.attr("aria-disabled", "true").addClass("disabled"); // Block duplicate messages until the AJAX call is complete
      $.ajax({
        url: 'https://0yzesnukyh.execute-api.us-east-1.amazonaws.com/email',
        type: "POST",
        crossDomain: true,
        contentType: 'application/json',
        data: JSON.stringify({
                'name': name,
                'phone': phone,
                'email': email,
                'message': message
        }),
        cache: false,
        success: function() {
          showAlert("success", $("<strong>").text("Your message has been sent."));
          if (typeof gtag === 'function') {
            gtag('event', 'generate_lead', {form: 'contact', role: role});
          }
          //clear all fields
          $('#contactForm').trigger("reset");
        },
        error: function() {
          var contactEmail = $('#contactForm').data('email');
          showAlert("danger", $("<strong>").text("Sorry " + firstName + ", the message did not go through. Please try again later, or email us at "))
            .find("strong").append($("<a>").attr("href", "mailto:" + contactEmail).text(contactEmail)).append(".");
        },
        complete: function() {
          setTimeout(function() {
            $this.removeAttr("aria-disabled").removeClass("disabled"); // Re-enable submit button when AJAX call is complete
          }, 1000);
        }
      });
    },
    filter: function() {
      return $(this).is(":visible");
    },
  });

  $("a[data-toggle=\"tab\"]").click(function(e) {
    e.preventDefault();
    $(this).tab("show");
  });
});

/*When clicking on Full hide fail/success boxes */
$('#name').focus(function() {
  $('#success').html('');
});
