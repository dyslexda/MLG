$(function() {
    $('button').click(function() {
        $.ajax({
            url: '/calculator/api',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                $("#place_for_preview").html(response);
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});