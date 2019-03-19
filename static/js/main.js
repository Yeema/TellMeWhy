function entail(sentence){
    return sentence;
}

function renderSearchResult(data){
    var search_result = document.getElementById('accordionExample');
    // search_result.innerHTML = data;
    console.log('in renderSearchResult')
    var counter = 0;
    console.log(data)
    search_result.innerHTML = data;
}