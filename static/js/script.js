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

    $("#newMessageForm").submit(function(e) {
        e.preventDefault(); // avoid to execute the actual submit of the form.
    
        var form = $(this);
        var url = form.attr('action');
        var userId = form.attr('data-target');
    
        $.ajax({
            type: "POST",
            url: url,
            data: form.serialize(), // serializes the form's elements.
            success: function(data){
                clearAndFillMessages(data, userId);
            }
        });
    });

    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});

function addComment(nb) {
    comment = "#post" + nb;
    $(comment).toggle('show');
}

function updateComment(nb) {
    comment = "#comment" + nb;
    $(comment).prop('readonly', false);
}

function addSuggestion() {
    $("#suggestion").toggle("show");
}

function clearAndFillMessages(data, idUser) {
    $('#messagesCard').empty();
    $('#newMessageContent').val('');
    data.forEach(element => {
        if(element.fields.sender == idUser) {
            $('#messagesCard').append(`<div class='row justify-content-end' style='margin: 0px;'><div class='card message sentMessage' id='message${element.pk}' data-toggle='tooltip' title='${element.fields.date}'>${element.fields.content}</div></div>`);
        } else {
            $('#messagesCard').append(`<div class='row justify-content-start' style='margin: 0px;'><div class='card message receivedMessage' data-toggle='tooltip' title='${element.fields.date}'>${element.fields.content}</div></div>`);
        } 
    });
    var objDiv = $("#scrollableMessages");
    objDiv.scrollTop(objDiv.height());
}

function getMessages(idConversation, idUser) {
    $.ajax({url: `messages/${idConversation}`,
    success: function(result){
        clearAndFillMessages(result, idUser);
        var convName = $(`#conversation${idConversation}`).text();
        $('#conversation_name').text(convName);
    }});

    $('#newMessageForm').attr('action', `/messages/${idConversation}/new-message`);
    $('#newMessageContent').prop('disabled', false);
    $('#newMessageButton').prop('disabled', false);
}