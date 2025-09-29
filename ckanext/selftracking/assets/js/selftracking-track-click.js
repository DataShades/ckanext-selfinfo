ckan.module("selftracking-track-click", function ($, _) {
  "use strict";
  return {
    options: {
        activity: null,
        path: null
        
    },

    initialize: function () {
        $.proxyAll(this, /_on/);
        const activity = this.options.activity;
        const path = this.options.path;
        const _this = $(this.el);
 
        _this.on('click', () => {
            if (path && activity) {
                const data = {
                    'type': activity,
                    'path': path,
                }

                var csrf_field = $('meta[name=csrf_field_name]').attr('content');
                var csrf_token = $('meta[name=' + csrf_field + ']').attr('content');

                fetch('/api/action/selftracking_send_track_for_queue', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrf_token
                    },
                    body: JSON.stringify(data),
                    keepalive: true
                })
            }
        })

    },
  };
});
