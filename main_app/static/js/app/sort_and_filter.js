

function sort_and_filter_toggle() {
    el = $('#sort_and_filter');
    el.toggle(500);
}

function fill_last_login_date() {
    var text = $('#filter_from_date_last_login').text().trim();
    $('#filter_from_date_input').val(text);
}

function previous_page(click_event) {
    if (!$('#submit_filter').length) {
        return;
    }

    click_event.preventDefault();
    var current_page = $('#filter_page').val().trim();
    if (current_page) {
        current_page = Math.min(1, parseInt(current_page) - 1);
    } else {
        current_page = 1;
    }
    $('#filter_page').val(current_page);
    $('#submit_filter').click();
}

function next_page(click_event) {
    if (!$('#submit_filter').length) {
        return;
    }

    click_event.preventDefault();
    var current_page = $('#filter_page').val().trim();
    console.log(current_page);
    if (current_page) {
        current_page = parseInt(current_page) + 1;
    } else {
        current_page = 2;
    }
    $('#filter_page').val(current_page);
    $('#submit_filter').click();
}



$(document).ready(function() {
    // Filling in last login date in filter
    $('#filter_from_date_label').click(fill_last_login_date);

    // Pagination with filtering
    $('#previous_page_link').click(previous_page);
    $('#next_page_link').click(next_page);
});