

function sort_and_filter_toggle() {
	el = $('#sort_and_filter');
	el.toggle(500);
}

function fill_last_login_date() {
	var text = $('#filter_from_date_last_login').text().trim();
	$('#filter_from_date_input').val(text);
}

$(document).ready(function() {
    // Filling in last login date in filter
    $('#filter_from_date_label').click(fill_last_login_date);
});