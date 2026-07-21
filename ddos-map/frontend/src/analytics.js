import Chart from "chart.js/auto";

// src/analytics.js
// Initializes a Chart.js line chart for live events per second.
// Exposes initChart() which returns an object with updateChart(value).

export function initChart() {
  const ctx = document.getElementById('analytics-chart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [], // timestamps
      datasets: [
        {
          label: 'Events/sec',
          data: [],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37,99,235,0.2)',
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          display: true,
          title: { display: true, text: 'Time' },
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Events/sec' },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: { mode: 'index', intersect: false },
      },
    },
  });

  function updateChart(value) {
    const now = new Date();
    chart.data.labels.push(now.toLocaleTimeString());
    chart.data.datasets[0].data.push(value);
    if (chart.data.labels.length > 60) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }
    chart.update('none');
  }

  return { updateChart };
}
