// var myCustomFlag = true;

$(document).ready(function(){
    console.log("js is loaded");

    $("#send-aes").click(function(){
        var sentence = document.getElementById('write-aes').innerText;
//         var sentence = $("#write-aes").val();
        console.log(sentence)
        // alert( "Handler for .click() called2." );
        $.ajax({
            method: 'POST',
            data: { "text_field" : sentence },
            dataType: 'text',
            url: '/query',
            success: function(response) {
                renderSearchResult(response);
                const button = document.querySelector('button');
                button.addEventListener('click',colorWord);
            }
        })

    });
    // $("card").click(function(){
    //     alert("The paragraph was clicked.");
    // });

//     $(document).click(function(event) {
// //         var text = $(event.target).id;
// //         console.log(event.target.id)
//         var text = $(event.target).text();
//         var sentence = $("#write-aes").val();
//         var re_add = new RegExp("\{\ *\+ *(.*?) *\+ *\}");
//         var re_del = new RegExp("\[ *- *(.*?) *- *\]");
//         var re_delandadd = new RegExp("(\[ *- *(.*?) *- *\] *\{\ *\+ *(.*?) *\+ *\} *)+");
//         var splits = text.split(" ");
//         var i;
//         var tail;
//         var matchArray;
//         var search_result = document.getElementById('write-aes');
//         if (text.includes("Replace") && text.includes("with")){
//             tail = splits.findIndex(checkwith)
//             matchArray = sentence.match(re_delandadd);
//             console.log(matchArray);
//             for(i=0;i<matchArray.length;i++){
//                 if(text.includes(splits[1])&&text.includes(splits[tail+1])){
//                     sentence = sentence.replace(matchArray,'<u>'+matchArray+'</u>');
//                     search_result.innerHTML = sentence;
//                     break;
//                 }
//             }         
//         }else if (text.includes("Omit")){
//             matchArray = sentence.match(re_del);
//             console.log(matchArray);
//             for(i=0;i<matchArray.length;i++){
//                 if(text.includes(splits[1])){
//                     sentence = sentence.replace(matchArray,'<u>'+matchArray+'</u>');
//                     search_result.innerHTML = sentence;
//                     break;
//                 }
//             }
//         }else if (text.includes("Insert")){
//             matchArray = sentence.match(re_add);
//             console.log(matchArray);
//             for(i=0;i<matchArray.length;i++){
//                 if(text.includes(splits[1])){
//                     sentence = sentence.replace(matchArray,'<u>'+matchArray+'</u>');
//                     search_result.innerHTML = sentence;
//                     break;
//                 }
//             }
//         }
//     });
    
    var input = document.getElementById("write-aes");
    input.addEventListener("keyup", function(event) {
      if (event.keyCode === 13) {
       event.preventDefault();
       document.getElementById("send-aes").click();
      }
    });
    
    var themaintextarea = document.getElementsByClassName('clickable'); 
    for (var i = 0; i < themaintextarea.length; i++) {   
        themaintextarea[i].addEventListener('click', getSel);
    }
});

function getSel() // javascript
{
    // obtain the object reference for the <textarea>
    var txtarea = document.getElementById("write-aes");
    // obtain the index of the first selected character
    var start = txtarea.selectionStart;
    // obtain the index of the last selected character
    var finish = txtarea.selectionEnd;
    // obtain the selected text
    var from = txtarea.value.substring(start-7, start);
    var end = txtarea.value.substring(start, start+7);
    // do something with the selected content
    console.log(sel)
}
function checkwith(word){
    return word == "with";
}
function colorWord(event){
    console.log(event.target.id);
}