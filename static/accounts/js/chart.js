// usage: call loadMilkChart(chartDataUrl, canvasId)
function loadMilkChart(chartDataUrl, canvasId) {
  fetch(chartDataUrl)
    .then(r => {
      if (!r.ok) throw new Error('Network response was not ok');
      return r.json();
    })
    .then(json => {
      const el = document.getElementById(canvasId);
      if (!el) return;
      const ctx = el.getContext('2d');
      if (window._milkChart) window._milkChart.destroy();
      window._milkChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: json.labels,
          datasets: [{
            label: 'Litres per day',
            data: json.data,
            borderWidth: 2,
            borderColor: '#007bff',
            backgroundColor: 'rgba(0,123,255,0.1)',
            fill: true,
            tension: 0.3
          }]
        },
        options: {
          responsive: true,
          scales: {
            x: { display: true },
            y: { beginAtZero: true }
          }
        }
      });
    })
    .catch(err => console.error('Chart load error', err));
}