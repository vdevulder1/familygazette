$(document).ready(function () {

    $("#menu-toggle").click(function(e) {
        e.preventDefault();
        $("#wrapper").toggleClass("toggled");
    });

    $('img').each(function() {
        var width = $(this).width();
        var height = $(this).height();
        
        if (height > width && height > $(window).height()) {
            let ratio = width/height;
            let new_width = ratio*100;
            $(this).css("height", "100vh");
            $(this).css("width", new_width+"vh");
        }
    });

});

function addComment(nb) {
    comment = "#comment" + nb;
    $(comment).toggle('show');
}

function addSuggestion() {
    $("#suggestion").toggle("show");
}