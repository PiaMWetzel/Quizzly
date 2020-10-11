

function hide_message(item, some_address)
{
    
    if( some_address)
    {
        window.location.href = some_address;
    }
    item.style.display = "none";

    
}

function show_message(content)
 {
    var message = document.getElementById("custom-message");
    message.style.display = "block";
    document.getElementById("message-center").innerHTML = content;

 }

 function show_message_and_redirect_on_ok(content, address_)
 {

    var item = document.getElementById("cust_mess_button");
    item.addEventListener("click", function(){hide_message(item.parentNode.parentNode, address_);}) 
    var message = document.getElementById("custom-message");
    message.style.display = "block";
    document.getElementById("message-center").innerHTML = content;
    
 }

function clear_message()
{
    message = "";
}