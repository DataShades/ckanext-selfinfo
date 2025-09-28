ckan.module("selftracking-24-hours", function ($, _) {
  "use strict";
  return {
    options: {
        data: null,
    },

    initialize: function () {
        $.proxyAll(this, /_on/);
        const data = this.options.data.items;
        const ctx = document.getElementById('last-24-hours').getContext('2d');
        var prepare_datasets = [];
        
        for (const [key, value] of Object.entries(data)) {
            prepare_datasets.push({
                label: key,
                data: value.data,
                borderColor: value.color,
                backgroundColor: value.color,
                fill: false,
                tension: 0.3   
            });
        }
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.options.data.labels,
                datasets: prepare_datasets
            },
            options: {
                responsive: true,
                plugins: {
                tooltip: { mode: 'index', intersect: false },
                legend: { position: 'top' },
                // title: { display: true, text: 'Tracks per hour (last 24h)' }
                },
                scales: {
                x: { title: { display: true, text: 'Hour' } },
                y: { title: { display: true, text: 'Views' }, beginAtZero: true }
                }
            }
        });
    },
  };
});
