var global_response;
var global_mode = 'gec-tab';
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
                    global_response = response;
                    renderLinggleResult(response);
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
            index = $(this).data('edit');
            console.log(index);
            SearchResult.query(global_response[index]);
            var searchBar = $('#search-bar');
            searchBar.val(global_response[index])
            $('.linggle.search-result').show()
        }
    });
});

function show_edit(event, response){
    var edit_id = $(this).data('edit');
    var mode = $('.nav-link.active').attr('id');
    console.log(edit_id);
//     if(mode!='linggle-tab'){
        $(`span.edit:not(.${edit_id})`).removeClass('active');
        $(`span.${edit_id}`).toggleClass('active');
//     }
}

