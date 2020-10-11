function log_out()
{

    $.ajax({
        url: "http://localhost:5000/log_out",
        type: "POST",
        contentType: "application/JSON",
        data: null,
        success:function(){
        show_message_and_redirect_on_ok("Successfully logged out","/");
}
    });

}

function access_profile()
{
    // window.alert("accessing profile");
    window.location.href = "/profile";
}


function new_quiz()
{
   window.location.href = "/create_quiz"

}