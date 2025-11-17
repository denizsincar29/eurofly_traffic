
// Basic JS file for application

// Functions on page load
$(document).ready(function () {
	init_app();
	init_ajax();
	init_menu();
});


// Set a tag active
function init_app() {
	let url = new URL(window.location.href).pathname;
	url = url.replace(/\//g,'');
	$('.menu a').each(function() {
		if ( $(this).attr('href').replace(/\//g,'') === url ) 
			$(this).addClass('active');
	});
}

// Ajax requests
function init_ajax() {
	$("span.xhr").each(function(index, span) { // Funkcia pre kazdy span s triedou xhr
		call_ajax(span); // volame najprv hned po nacitani stranky a potom kazdu minutu
		setInterval(function() { call_ajax(span) }, 60 * 1000); // 60 * 1000 milsec
	});
	// spustime kazdu minutu
	function call_ajax(span) {
		var now = new Date();
		var data = {
			type: 'xhr', // Tymto si v php odchitime, ze je to xhr request
			offset: now.getTimezoneOffset(), // rozdiel v minutach napr. -60
			method: $(span).data('method'),	// Aku metodu v PHP budeme volat
			let: $(span).data('let'),	// nakoniec data s ktorimi potrebujeme v php pracovat
		};
		$.post({
			data: data,
			success: function(result) {
				$(span).html(result);
			}
		});
	}
}

// Responsive Menu
function init_menu() {
	var $clickable = $('.menu-responsive svg');
	$clickable.click(function() {
		var $menu = $('.menu-responsive ul');
		if ( $menu.hasClass('active') ) {
			$menu.removeClass('active').slideUp();
			$clickable.setAttribute('aria-expanded', false);
		} else {
			$menu.addClass('active').slideDown();
			$menu.removeClass('hide');
			$clickable.setAttribute('aria-expanded', true);
		}
	});


}
