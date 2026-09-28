window.addEventListener('load', function () {
  const url = window.COUNTER_API_URL;
  if (!url) {
    console.warn('Visitor counter disabled: COUNTER_API_URL is not set.');
    return;
  }

  fetch(url, { method: 'POST' })
    .then(function (response) {
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }
      return response.json();
    })
    // get data and set it to the counter
    .then(function (data) {
      document.querySelector('.counter').textContent = data.value;
    })
    // catch the error
    .catch(function (error) {
      console.error('Error:', error);
    });
});
