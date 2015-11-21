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

$(".show-more a").on("click", function() {
    var $link = $(this);
    var $content = $link.parent().next("div.text-content");
    var linkText = $link.text();

    $content.toggleClass("short-text, full-text");

    $link.text(getShowLinkText(linkText));

    return false;
});

function getShowLinkText(currentText) {
    var newText = '';

    if (currentText.toUpperCase() === "MORE") {
        newText = "Less";
    } else {
        newText = "More";
    }

    return newText;
}