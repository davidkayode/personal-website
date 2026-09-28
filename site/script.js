window.addEventListener('load', function () {
  // The API URL is generated at deploy time, so fetch it instead of relying on
  // a script tag: a cached index.html then still finds the current API.
  return fetch('/config.json', { cache: 'no-cache' })
    .then(function (response) {
      if (!response.ok) {
        throw new Error(`config.json HTTP error: ${response.status}`);
      }
      return response.json();
    })
    .then(function (config) {
      if (!config.counterApiUrl) {
        throw new Error('config.json has no counterApiUrl');
      }
      return fetch(config.counterApiUrl, { method: 'POST' });
    })
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
      console.warn('Visitor counter unavailable:', error.message);
    });
});
