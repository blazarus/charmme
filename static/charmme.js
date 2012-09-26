$(document).ready(function() {

	$(".loginButton").click( function() {
		console.log($(this).html());
		var username = $(this).html();
		var newUrl = window.location.host + "/profile/" + username;
		document.cookie = "username="+username;
		window.location = "../profile/" +username;
		
		//alert(newUrl);
	//	window.location = newUrl;
	});


});
