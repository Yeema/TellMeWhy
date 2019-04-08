function renderSearchResult(data){
    var search_result = document.getElementById('accordionExample');
    // search_result.innerHTML = data;
    console.log('in renderSearchResult')
    console.log(data['html'])
    search_result.innerHTML = data['html'];
    var write_result = document.getElementById('write-aes');
    console.log(data['sent'])
    write_result.innerHTML = data['sent'];
}

function renderGECResult(data){
    var search_result = document.getElementById('accordionGEC');
    // search_result.innerHTML = data;
    console.log(data['html'])
    var counter = 0;
//     console.log(data['html'])
    search_result.innerHTML = data['html'];
    var write_result = document.getElementById('write-aes');
    console.log(data['sent'])
    write_result.innerHTML = data['sent'];
}

function renderLinggleResult(data){
    var write_result = document.getElementById('write-aes');
    console.log(data['sent'])
    write_result.innerHTML = data['sent'];
}