$(document).ready(function() {
    $('.tabs .tab-links a').on('click', function(e)  {
        var currentAttrValue = $(this).attr('href');
 
        // Show/Hide Tabs
        $('.tabs ' + currentAttrValue).show().siblings().hide();
 
        // Change/remove current tab to active
        $(this).parent('li').addClass('active').siblings().removeClass('active');
 
        e.preventDefault();
    });
});

var options = [];

// $( '.dropdown-menu a' ).on( 'click', function( event ) {
// 	console.log("AAA");
//    var $target = $( event.currentTarget ),
//        val = $target.attr( 'data-value' ),
//        $inp = $target.find( 'input' ),
//        idx;

//    if ( ( idx = options.indexOf( val ) ) > -1 ) {
//       options.splice( idx, 1 );
//       setTimeout( function() { $inp.prop( 'checked', false ) }, 0);
//    } else {
//       options.push( val );
//       setTimeout( function() { $inp.prop( 'checked', true ) }, 0);
//    }

//    $( event.target ).blur();
      
//    console.log( options );
//    return false;
// });