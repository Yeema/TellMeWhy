//$('.linggle.search-result').hide();

function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}




var SearchResult = {
    query: function(query) {
       console.log(query)
      $.ajax({
          url: '/linggle',
          type: 'POST',
          data: {'sent':query},
          dataType: 'json',
      })
      .done(this.renderSearchResult);
    },
  
  
    renderSearchResult: function(data) {
      console.log(data)
        if (data.ngrams.length > 0) {
            $('.linggle.search-result tbody').html(data.ngrams.map(function(ngramData) {
            var ngram = ngramData[0];
            var count = ngramData[1];
            var percent = Math.round(count/data.total * 1000) / 10;
            return SearchResult.renderNgramRowHtml(ngram, count, percent);
            }).join(''));
            Example.initExampleBtns();
        } else {
            $('.linggle.search-result tbody').html('<tr><td colspan=4>No result</td></tr>');
        }
      
    },
  
    renderNgramRowHtml: function(ngram, count, percent) {
      //console.log(ngram, count, percent)
      
      var countStr = numberWithCommas(count)
      var ngramIdstr = ngram.replace(/\ /g , '_');
      // TODO: template literals is in ES6, which is not compatible with IE11
      return `<tr>
        <td class="ngram">${ngram}
          <div class="progress">
            <div class="progress-bar" role="progressbar" style="width: ${percent}%;">
          </div>
        </td>
        <td class="percent text-right">${percent} &percnt;</td>
        <td class="count text-right">${countStr}</td>
        <td class="example">
          <button class="linggle btn btn-green" type="button" data-ngram="${ngram}"
          data-loading-text="<i class='fa fa-circle-o-notch fa-spin'></i> Loading"
          data-hide-text="Hide"
          data-show-text="Show"
          >Show</button>
        </td>
      </tr>
      <tr class="examples" id="${ngramIdstr}" data-fetched="false" data-hide="true" style="display: none;">
      </tr>`;
    },
  };
