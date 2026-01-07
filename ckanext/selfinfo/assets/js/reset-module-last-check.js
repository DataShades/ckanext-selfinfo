this.ckan.module('reset-module-last-check', function($) {
	return {
		options : {
                  monthNames: ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"
                  ],
                  action: null
		},
		initialize: function () {
			$.proxyAll(this, /_on/);
                  this._onLoad();
		},
            _onLoad: function() {
                  const _this = this;
                  $(this.el).find(".force-reset-selfinfo").each(function(idx, item){
                        $(item).on('click', function(event){
                              event.preventDefault();
                              const target = this.getAttribute('data-target');
                              if (target && _this.options.action) {
                                    var client = _this.sandbox.client;
                                    client.call('POST', _this.options.action, { module : target }, _this._onClickLoaded);
                              }
                        });
                  })
            },
		_onClickLoaded: function(json) {
                  if (json.success) {
                        $("td.td-"+ json.result.name +"-selfinfo-curVersion").text(json.result.current_version);
                        $("td.td-"+ json.result.name +"-selfinfo-latestVersion").text(json.result.latest_version);
                        
                        let updated = new Date(json.result.updated);

                        $("td.td-"+ json.result.name +"-selfinfo-updated").text(this.options.monthNames[updated.getMonth()] + ' ' +  updated.getDate() + ', ' + updated.getFullYear());
                  }
		},
	};
});
