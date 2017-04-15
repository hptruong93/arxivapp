
$(document).ready(function() {
    document.getElementById('unbookmark-button').addEventListener('click', function(e) {
        var startIndex = 'check_box_'.length;
        var totalString = '';
        var joiner = '';

        var extractName = function(index, paperElement) {
            if (paperElement.checked) {
                var new_id = paperElement.id.substring(startIndex);
                totalString += joiner + new_id;

                joiner = ',';
            }
        };

        $('[id^=check_box]').each(extractName);
        console.log(totalString);

        document.getElementById('arxiv_ids').value = totalString;
    });
});