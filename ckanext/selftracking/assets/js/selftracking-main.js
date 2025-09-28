ckan.module("selftracking-main", function ($, _) {
  "use strict";
  return {
    options: {
        dataPie: null,
    },

    initialize: function () {
        $.proxyAll(this, /_on/);
        const dataPie = this.options.dataPie;
        const labels = dataPie.map(d => d.type);
        const values = dataPie.map(d => d.count);
        const colors = dataPie.map(d => d.color);

        const total = values.reduce((a, b) => a + b, 0);

        const ctx = document.getElementById('chart').getContext('2d');


        const centerTextPlugin = {
            id: 'centerText',
            beforeDraw(chart, args, options) {
            if (options.display) {
                const { ctx, chartArea: { width, height } } = chart;
                ctx.save();
                ctx.font = options.font || 'bold 20px sans-serif';
                ctx.fillStyle = options.color || 'black';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(options.text, width / 2, height / 2);
                ctx.restore();
            }
            }
        };

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: colors,
                hoverOffset: 4,
            }]
            },
            options: {
                cutout: '50%',
                plugins: {
                    legend: {
                    position: 'bottom',
                    display: false,
                    },
                    tooltip: {
                    enabled: true
                    },
                    centerText: {
                    display: true,
                    text: total,
                    color: 'black',
                    font: 'bold 22px sans-serif'
                    }
                }
            },
            plugins: [centerTextPlugin]
        });

        chart.update();
    },
  };
});
