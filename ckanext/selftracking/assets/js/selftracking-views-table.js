ckan.module("selftracking-views-table", function ($, _) {
  "use strict";
  return {
    options: {
        target: null,
    },

    initialize: function () {
        $.proxyAll(this, /_on/);
        const target = this.options.target;

        const table = new DataTable('#' + target, {
            pageLength: 25,
            layout: {
            topStart: {
                pageLength: {
                    menu: [ 25, 50, 100, 1000, 10000 ]
                },
                buttons: [
                    'csv'
                ],  
            },
            topEnd: {
                searchBuilder: {},
                search: {
                    placeholder: 'Search here'
                }
            },
            }
        });

        table.order([1, 'desc']).draw();
    },
  };
});
