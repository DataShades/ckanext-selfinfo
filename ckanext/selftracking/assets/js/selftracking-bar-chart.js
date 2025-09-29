ckan.module("selftracking-bar-chart", function ($, _) {
  "use strict";
  return {
    options: {
        data: null,
        key: null,
        target: null
    },

    initialize: function () {
        $.proxyAll(this, /_on/);
        const data = this.options.data;
        const key = this.options.key;
        const target = this.options.target;
        const ctx = document.getElementById(target + '-bar-chart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
            labels: data.labels,
            datasets: [{
                label: key,
                data: data.values,
                backgroundColor: data.color,
                borderColor: data.color,
                borderWidth: 1
            }]
            },
            options: {
            responsive: true,
            plugins: {
                legend: { display: true }
            },
            scales: {
                y: { beginAtZero: true }
            }
            }
        });
    },
  };
});
