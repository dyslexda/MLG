$(function() {
    $('button').click(function() {
        var url = '/calculator/api/ump/' + $("#game_id").val() + '/ranges'
        $.ajax({
            url: url,
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                $("#results_div").html(response);
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});