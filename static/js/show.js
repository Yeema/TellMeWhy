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
                          element.addEventListener('click', show_edit, false);
                    });
                }
            })
        }else{
            console.log('Linggle!')
        }

    });
    
    
    const buttons = document.querySelectorAll('button');
    console.log(buttons)
    buttons.forEach(function(element) {
        if(element.id!='send-aes'){
            var mode = $('.nav-link.active').attr('id');
            if (mode == 'gec-tab'){
                element.addEventListener('click',function(event){
                    changeSpan(event,global_response);
                },false);
            }else if (mode == 'explain-tab'){
                element.addEventListener('click',function(event){
                    colorWord(event,global_response);
                },false);
            }
            
        }
    });
    
    var input = document.getElementById("write-aes");
    input.addEventListener("keyup", function(event) {
      if (event.keyCode === 13) {
       event.preventDefault();
       document.getElementById("send-aes").click();
      }
    });
});

function show_edit(event, response){
    var edit_id = $(this).data('edit');
    console.log(edit_id);
    $(`span.edit:not(.${edit_id})`).removeClass('active');
    $(`span.${edit_id}`).toggleClass('active');
//     $.ajax({
//             method: 'POST',
//             data: {'pos':respond[event.target.id.substring(3).concat('\tpos')] , 'sent':respond['sent']},
//             dataType: 'text',
//             url: '/color',
//             success: function(response) {
//                 document.getElementById('write-aes').innerHTML = response;
//             }
//    })
}

function changeSpan(event,response){
    console.log(event.target.text);
    var labelname = $(event.target.id).text();
    show_edit
//     if(labelname.startsWith("Replace")){
//         var x = document.getElementById('deletion'+event.target.id.substring(3));
//         var y = document.getElementById('addition'+event.target.id.substring(3));   
//         x.style.color = '#00FF00';
//     }else if(labelname.startsWith("Omit")){
//         var x = document.getElementById('deletion'+event.target.id.substring(3));
//         x.style.color = '#00FF00';
//     }else{
//         var x = document.getElementById('addition'+event.target.id.substring(3));
//         x.style.color = '#00FF00';
//     }
}