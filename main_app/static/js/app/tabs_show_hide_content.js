function getShowLinkText(currentText) {
    var newText = '';

    if (currentText.toUpperCase() === "FULL ABSTRACT") {
        newText = "Less Abstract";
    } else {
        newText = "Full Abstract";
    }

    return newText;
}

function showHideContent() {
    $(".show-more a").each(function() {
        var $link = $(this);
        var $content = $link.parent().next("div.text-content");

        // console.log($link);

        var visibleHeight = $content[0].clientHeight;
        var actualHide = $content[0].scrollHeight - 1;

        // console.log(actualHide);
        // console.log(visibleHeight);

        if (actualHide > visibleHeight) {
            $link.show();
        } else {
            $link.hide();
        }
    });
}

$(".show-more a").on("click", function() {
    console.log("A");
    var $link = $(this);
    var $content = $link.parent().next("div.text-content");
    var linkText = $link.text();
    console.log(linkText);
    $content.toggleClass("short-text, full-text");

    $link.text(getShowLinkText(linkText));

    return false;
});

//Tabs switching
$(document).ready(function() {
    showHideContent();
    $('.tabs .tab-links a').on('click', function(e)  {
        var currentAttrValue = $(this).attr('href');
 
        // Show/Hide Tabs
        $('.tabs ' + currentAttrValue).show().siblings().hide();
        showHideContent();
 
        // Change/remove current tab to active
        $(this).parent('li').addClass('active').siblings().removeClass('active');
 
        e.preventDefault();
    });
});