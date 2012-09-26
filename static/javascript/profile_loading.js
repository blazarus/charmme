$(document).ready( function () {
  console.log("Making ajax call to get profile page data");
  $("#content").load(window.location.href + 'data/', function () {
    console.log("Loaded data");

    //Get LinkedIn script async once the profile data has been loaded
    $.getScript("http://platform.linkedin.com/in.js?async=true", function success() {
        IN.init({ // can add onLoad: "myonloadfunction"
          api_key: 'el2rntv7bzpg',
          authorize: 'true'
        });
    });
  });
  setTimeout(updateLoadingMessage, 10000);


});

var updateLoadingMessage = function () {
  $("#loading-message").text("Generating best recommendations...");
};

var setMetCookie = function (met) {
  window.open( "http://www.linkedin.com/search/fpsearch?type=people&keywords=" + met + "&pplSearchOrigin=GLHD&pageKey=fps_results");
  var cookie_str = document.cookie + ";met=" + met
  document.cookie = cookie_str;
}

var changeStatus = function () {
  javascript:debugger;
  var statusButton = document.getElementById('#status_button');
  var status = document.getElementById('status');

  if (statusButton.value.match("Change")) {
    status.disabled = false;
    statusButton.value = "Publish";
  } else if (statusButton.value.match("Publish")) {
    status.disabled= true;
    statusButton.value= "Change";
  }
}

var getID = function () {
   IN.API.Profile("me").result( function(result) {
      $("#profile").html('<script type="IN/FullMemberProfile" data-id="' + result.values[0].id + '"><script>');
      IN.parse(document.getElementById("profile"));
      $("#bio").remove();
   });
}

