var prev_sent = "";
var global_response;
$(document).ready(function(){
    console.log("js is loaded");
    
    $("#send-aes").click(function(){
        var sentence = document.getElementById('write-aes').innerText;
        // var sentence = document.getElementById('write-aes').textContent;
        // var sentence = $("#write-aes").text();
        console.log(sentence);
//         console.log(global_mode);
        var mode = $('.nav-link.active').attr('id');
        console.log(mode)
        if(mode == 'gec-tab'){
               $.ajax({
                method: 'POST',
                data: { "sent" : sentence },
                dataType: 'json',
                url: '/GEC',
                success: function(response) {
                    renderGECResult(response);
                    global_response = response;
                    prev_sent = document.getElementById('write-aes').innerText;
                    const buttons = document.querySelectorAll('button');
                    console.log(buttons)
                    buttons.forEach(function(element) {
                        console.log('click button, gec-tab ');
                          element.addEventListener('click', show_edit, false);
                    });
                }
            });
        }else if(mode == 'explain-tab'){
               $.ajax({
                method: 'POST',
                data: { "text_field" : sentence },
                dataType: 'json',
                url: '/query',
                success: function(response) {
                    renderSearchResult(response);
                    global_response = response;
                    prev_sent = document.getElementById('write-aes').innerText;
                    const buttons = document.querySelectorAll('button');
                    console.log(buttons)
                    buttons.forEach(function(element) {
                        console.log('click button, explain-tab ');
                        element.addEventListener('click', show_edit, false);
                    });
                }
            })
        }else{
            $.ajax({
                method: 'POST',
                data: { "sent" : sentence },
                dataType: 'json',
                url: '/linggle_go',
                success: function(response) {
                    renderLinggleResult(response);
                    prev_sent = document.getElementById('write-aes').innerText;
                    global_response = response;
                }
            })
        }
    });
    
    
    var input = document.getElementById("write-aes");
    input.addEventListener("keyup", function(event) {
      if (event.keyCode === 13) {
       event.preventDefault();
       document.getElementById("send-aes").click();
      }
    });
    
    $(document).on('click','.edit',function(){
        var mode = $('.nav-link.active').attr('id');
        if (mode == 'linggle-tab'){
            console.log(this);
            index = $(this).data('edit');
            console.log(index);
            SearchResult.query(global_response[index]);
            var searchBar = $('#search-bar');
            searchBar.val(global_response[index])
            $('.linggle.search-result').show()
        }
    });
    
    $(document).on('click','.nav-link',function(){
        var mode = $('.nav-link.active').attr('id');
        if (mode == 'linggle-tab'){
//             var sentence = document.getElementById('write-aes').innerText;
//             console.log(sentence);
//             console.log(prev_sent);
//             if(sentence=="" || prev_sent == sentence){
//                 console.log(this);
                $(".textcrollbar").find("span.edit").addClass('active');
//             }
        }
    });
});

function show_edit(event, response){
    var edit_id = $(this).data('edit');
    var mode = $('.nav-link.active').attr('id');
    console.log(edit_id);
    $(`span.edit:not(.${edit_id})`).removeClass('active');
    $(`span.${edit_id}`).toggleClass('active');
}

