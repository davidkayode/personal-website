window.addEventListener('load', function() {
    const url = 'https://cu2jqacorb.execute-api.us-east-1.amazonaws.com/default/visitorCounterLambda';
  
    fetch(url, {
        method: 'POST',
    })
      .then(function(response) {
        if (!response.ok) {
          throw new Error(`HTTP error: ${response.status}`);
        }
        return response.json();
      })
      // get data and set it to the counter
      .then(function(data) {
        document.querySelector('.counter').textContent = data.value;
    })
    // catch the error
    .catch(function(error) {
        console.error('Error:', error);
    });
});
