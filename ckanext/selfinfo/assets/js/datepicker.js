ckan.module('datepicker', function ($, _) {
    'use strict';
    return {
      options: {
        changeMonth: true,
        changeYear: true,
        showButtonPanel: true,
        closeText: 'Clear',
        currentText: 'Today',
        maxDate: 0,
        dateFormat: 'yy-mm-dd',
        beforeShow: function (input, inst) {
        }
      },
      initialize: function () {
        $(this.el).datepicker(this.options);
      },
    };
  }
);
